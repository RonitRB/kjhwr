from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from app.schemas import DaysResponse, ForecastResponse, HealthResponse
from pathlib import Path
import io
import os

ROOT = Path(__file__).resolve().parent
DATA = ROOT.parent / "data"
JAN_START = date(2026, 1, 1)
JAN_END = date(2026, 1, 31)
TZ = ZoneInfo("Europe/London")
DEFAULT_CUTOFF = os.getenv("DECISION_CUTOFF", "09:00")
app = FastAPI(
    title="Windwatch UK", version="1.0.0", description="UK day-ahead wind forecast monitoring"
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def _load(name):
    p = DATA / f"{name}.json"
    if not p.exists():
        return []
    return __import__("json").loads(p.read_text())


def _valid(d):
    x = date.fromisoformat(d)
    if not JAN_START <= x <= JAN_END:
        raise HTTPException(422, "Delivery days are restricted to January 2026")
    return x


def _select_latest_forecasts(forecasts: pd.DataFrame, cutoff: str) -> pd.DataFrame:
    """Select each period's last publication at or before its London day-ahead cutoff."""
    if forecasts.empty:
        return pd.DataFrame(
            {
                "startTime": pd.Series(dtype="datetime64[ns, UTC]"),
                "forecast": pd.Series(dtype="float64"),
                "publishTime": pd.Series(dtype="datetime64[ns, UTC]"),
                "horizonHours": pd.Series(dtype="float64"),
            }
        )
    selected = forecasts.copy()
    selected["day"] = selected.startTime.dt.date
    selected["cutoff"] = [
        datetime.combine(day - timedelta(days=1), time.fromisoformat(cutoff), TZ).astimezone(
            timezone.utc
        )
        for day in selected.day
    ]
    selected = (
        selected[selected.publishTime <= selected.cutoff]
        .sort_values("publishTime")
        .drop_duplicates("startTime", keep="last")
    )
    selected["horizonHours"] = (selected.startTime - selected.publishTime).dt.total_seconds() / 3600
    return selected[["startTime", "generation", "publishTime", "horizonHours"]].rename(
        columns={"generation": "forecast"}
    )


def _aggregate_actuals_hourly(actual: pd.DataFrame, start: date, end: date) -> pd.DataFrame:
    """Average the two UTC half-hour FUELHH readings into each forecast hour."""
    if actual.empty:
        return pd.DataFrame(
            {
                "startTime": pd.Series(dtype="datetime64[ns, UTC]"),
                "generation": pd.Series(dtype="float64"),
            }
        )
    hourly = actual.copy()
    hourly["startTime"] = pd.to_datetime(hourly["startTime"], utc=True, errors="coerce")
    hourly = hourly[(hourly.startTime.dt.date >= start) & (hourly.startTime.dt.date <= end)]
    hourly["startTime"] = hourly.startTime.dt.floor("h")
    return hourly.groupby("startTime", as_index=False, sort=True)["generation"].mean()


def _tables(start, end, cutoff=DEFAULT_CUTOFF):
    actual = pd.DataFrame(_load("actuals"))
    fc = pd.DataFrame(_load("forecasts"))
    if actual.empty:
        actual = pd.DataFrame(columns=["startTime", "generation"])
    if fc.empty:
        fc = pd.DataFrame(columns=["startTime", "publishTime", "generation"])
    for df, c in [(actual, "startTime"), (fc, "startTime")]:
        df[c] = pd.to_datetime(df[c], utc=True, errors="coerce")
    fc["publishTime"] = pd.to_datetime(fc["publishTime"], utc=True, errors="coerce")
    a = _aggregate_actuals_hourly(actual, start, end)
    f = fc[(fc.startTime.dt.date >= start) & (fc.startTime.dt.date <= end)].copy()
    f = _select_latest_forecasts(f, cutoff)
    m = (
        a[["startTime", "generation"]]
        .merge(f, on="startTime", how="outer")
        .sort_values("startTime")
    )
    m["error"] = m.generation - m.forecast
    m["absError"] = m.error.abs()
    m["day"] = m.startTime.dt.strftime("%Y-%m-%d")
    m["localTime"] = m.startTime.dt.tz_convert("Europe/London").astype(str)
    return m


def _metrics(m):
    x = m.dropna(subset=["generation", "forecast"]).copy()
    e = x.error
    if not len(x):
        return {
            "n": 0,
            "mae": None,
            "rmse": None,
            "bias": None,
            "mape": None,
            "r2": None,
            "correlation": None,
            "p50": None,
            "p75": None,
            "p90": None,
            "p95": None,
            "p99": None,
            "coverage": 0,
            "missingForecast": int(m.forecast.isna().sum()),
            "missingActual": int(m.generation.isna().sum()),
        }
    ss = ((x.generation - x.generation.mean()) ** 2).sum()
    return {
        "n": len(x),
        "mae": float(e.abs().mean()),
        "rmse": float((e.pow(2).mean()) ** 0.5),
        "bias": float(e.mean()),
        "mape": float((e.abs() / x.generation.clip(lower=1)).mean() * 100),
        "r2": float(1 - (e.pow(2).sum() / ss)) if ss else None,
        "correlation": float(x.generation.corr(x.forecast)) if len(x) > 1 else None,
        **{f"p{q}": float(e.abs().quantile(q / 100)) for q in [50, 75, 90, 95, 99]},
        "coverage": len(x) / max(1, len(m)),
        "missingForecast": int(m.forecast.isna().sum()),
        "missingActual": int(m.generation.isna().sum()),
    }


def _json_records(df):
    return df.astype(object).where(pd.notna(df), None).to_dict(orient="records")


@app.get("/api/health", response_model=HealthResponse)
def health():
    manifest_path = DATA / "manifest.json"
    manifest = __import__("json").loads(manifest_path.read_text()) if manifest_path.exists() else {}
    return {
        "status": "ok",
        "dataAvailable": bool(_load("actuals")),
        "source": "Elexon BMRS Insights",
        "snapshotUpdatedUtc": manifest.get("downloadedAtUtc"),
        "defaultCutoff": DEFAULT_CUTOFF,
    }


@app.get("/api/days", response_model=DaysResponse)
def days():
    return {"days": [(JAN_START + timedelta(days=i)).isoformat() for i in range(31)]}


@app.get("/api/forecast/latest", response_model=ForecastResponse)
def latest(day: str, cutoff: str = DEFAULT_CUTOFF):
    d = _valid(day)
    m = _tables(d, d, cutoff)
    rows = _json_records(m)
    horizon_buckets = by_horizon()["buckets"]
    for row in rows:
        lead = row.get("horizonHours")
        forecast = row.get("forecast")
        if lead is None or forecast is None or not horizon_buckets:
            row["uncertaintyLower"] = None
            row["uncertaintyUpper"] = None
            continue
        bucket = min(horizon_buckets, key=lambda item: abs(item["midpointHours"] - lead))
        row["uncertaintyLower"] = max(0.0, forecast + bucket["p10Error"])
        row["uncertaintyUpper"] = max(0.0, forecast + bucket["p90Error"])
    complete = [r for r in rows if r.get("forecast") is not None]
    forecast_total = sum(r["forecast"] for r in complete) if len(complete) == 24 else None
    return {
        "day": day,
        "cutoff": cutoff,
        "timezone": "Europe/London",
        "rows": rows,
        "coverage": len(complete),
        "missingForecast": len(rows) - len(complete),
        "summary": {
            "totalMWh": forecast_total,
            "peakMW": max((r["forecast"] for r in complete), default=None),
            "minMW": min((r["forecast"] for r in complete), default=None),
            "averageMW": (
                forecast_total / len(complete) if complete and forecast_total is not None else None
            ),
        },
    }


@app.get("/api/compare")
def compare(start: str, end: str, cutoff: str = DEFAULT_CUTOFF):
    a, b = _valid(start), _valid(end)
    if b < a:
        raise HTTPException(422, "end must be on or after start")
    m = _tables(a, b, cutoff)
    return {
        "rows": _json_records(m),
        "metrics": _metrics(m),
        "start": start,
        "end": end,
        "cutoff": cutoff,
    }


@app.get("/api/metrics")
def metrics(start: str = "2026-01-01", end: str = "2026-01-31", cutoff: str = DEFAULT_CUTOFF):
    a, b = _valid(start), _valid(end)
    m = _tables(a, b, cutoff)
    x = m.dropna(subset=["generation", "forecast"]).copy()
    out = _metrics(m)
    if len(x):
        x["hour"] = x.startTime.dt.tz_convert("Europe/London").dt.hour
        x["level"] = pd.qcut(x.generation, 3, labels=["Low", "Medium", "High"], duplicates="drop")
        out["byHour"] = [
            {
                "hour": int(k),
                "mae": float(v.error.abs().mean()),
                "bias": float(v.error.mean()),
                "n": len(v),
            }
            for k, v in x.groupby("hour")
        ]
        out["byLevel"] = [
            {
                "level": str(k),
                "mae": float(v.error.abs().mean()),
                "bias": float(v.error.mean()),
                "n": len(v),
            }
            for k, v in x.groupby("level", observed=True)
        ]
        out["histogram"] = [
            {"bin": float(k.mid), "count": int(v)}
            for k, v in pd.cut(x.error, 20, include_lowest=True).value_counts().sort_index().items()
        ]
    else:
        out.update(byHour=[], byLevel=[], histogram=[])
    insights = []
    if out["n"]:
        bias = out["bias"]
        direction = "under-forecast" if bias > 0 else "over-forecast"
        insights.append(f"Forecasts {direction} wind by {abs(bias):,.0f} MW on average.")
        if out["byLevel"]:
            level = max(out["byLevel"], key=lambda item: item["mae"])
            insights.append(
                f"Absolute errors were largest in the {level['level'].lower()} generation band "
                f"({level['mae']:,.0f} MW MAE)."
            )
        if out["byHour"]:
            hour = max(out["byHour"], key=lambda item: item["mae"])
            insights.append(
                f"The highest local-hour MAE was at {hour['hour']:02d}:00 ({hour['mae']:,.0f} MW)."
            )
    out["insights"] = insights
    return out


@app.get("/api/metrics/by-horizon")
def by_horizon(start: str = "2026-01-01", end: str = "2026-01-31"):
    """Compare every available forecast vintage with actuals by lead-time bucket."""
    first, last = _valid(start), _valid(end)
    actual = pd.DataFrame(_load("actuals"))
    forecasts = pd.DataFrame(_load("forecasts"))
    if actual.empty or forecasts.empty:
        return {"buckets": []}
    actual["startTime"] = pd.to_datetime(actual["startTime"], utc=True, errors="coerce")
    forecasts["startTime"] = pd.to_datetime(forecasts["startTime"], utc=True, errors="coerce")
    forecasts["publishTime"] = pd.to_datetime(forecasts["publishTime"], utc=True, errors="coerce")
    actual = _aggregate_actuals_hourly(actual, first, last)
    forecasts = forecasts[
        (forecasts.startTime.dt.date >= first) & (forecasts.startTime.dt.date <= last)
    ]
    actual = actual[["startTime", "generation"]].rename(columns={"generation": "actual"})
    forecasts = forecasts.rename(columns={"generation": "forecast"})
    matched = forecasts.merge(actual, on="startTime", how="inner")
    matched["horizonHours"] = (matched.startTime - matched.publishTime).dt.total_seconds() / 3600
    matched["error"] = matched.actual - matched.forecast
    matched = matched[(matched.horizonHours >= 0) & (matched.horizonHours < 48)]
    matched["bucket"] = pd.cut(matched.horizonHours, list(range(0, 53, 4)), right=False)
    return {
        "buckets": [
            {
                "horizon": str(k),
                "midpointHours": (k.left + k.right) / 2,
                "mae": float(v.error.abs().mean()),
                "bias": float(v.error.mean()),
                "p10Error": float(v.error.quantile(0.1)),
                "p90Error": float(v.error.quantile(0.9)),
                "n": len(v),
            }
            for k, v in matched.groupby("bucket", observed=True)
        ]
    }


@app.get("/api/export.csv")
def export(start: str = "2026-01-01", end: str = "2026-01-31", cutoff: str = DEFAULT_CUTOFF):
    m = _tables(_valid(start), _valid(end), cutoff)
    buf = io.StringIO()
    m.to_csv(buf, index=False)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=windwatch.csv"},
    )
