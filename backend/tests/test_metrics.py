import pandas as pd
from datetime import date

from app.main import _aggregate_actuals_hourly, _metrics, _select_latest_forecasts, _tables


def test_metrics_fixture():
    frame = pd.DataFrame(
        {
            "generation": [100.0, 200.0],
            "forecast": [90.0, 210.0],
            "error": [10.0, -10.0],
            "absError": [10.0, 10.0],
        }
    )
    result = _metrics(frame)
    assert result["mae"] == 10
    assert result["rmse"] == 10
    assert result["bias"] == 0
    assert result["p90"] == 10


def test_cutoff_never_selects_later_publication():
    forecasts = pd.DataFrame(
        {
            "startTime": pd.to_datetime(["2026-01-02T12:00:00Z"] * 3, utc=True),
            "publishTime": pd.to_datetime(
                ["2026-01-01T08:00:00Z", "2026-01-01T09:00:00Z", "2026-01-01T10:00:00Z"],
                utc=True,
            ),
            "generation": [100.0, 110.0, 999.0],
        }
    )
    selected = _select_latest_forecasts(forecasts, "09:00")
    assert selected.iloc[0].forecast == 110.0
    assert selected.iloc[0].publishTime == pd.Timestamp("2026-01-01T09:00:00Z")


def test_fuelhh_is_averaged_to_forecast_hour():
    actual = pd.DataFrame(
        {
            "startTime": pd.to_datetime(
                [
                    "2026-01-15T00:00:00Z",
                    "2026-01-15T00:30:00Z",
                    "2026-01-15T01:00:00Z",
                    "2026-01-15T01:30:00Z",
                ],
                utc=True,
            ),
            "generation": [14602.0, 14311.0, 14200.0, 14516.0],
        }
    )
    hourly = _aggregate_actuals_hourly(actual, date(2026, 1, 15), date(2026, 1, 15))
    assert hourly.startTime.tolist() == list(
        pd.to_datetime(["2026-01-15T00:00:00Z", "2026-01-15T01:00:00Z"], utc=True)
    )
    assert hourly.generation.tolist() == [14456.5, 14358.0]


def test_jan15_audit_uses_latest_eligible_publish_and_hourly_actuals():
    day = date(2026, 1, 15)
    rows = _tables(day, day, "09:00")
    assert len(rows) == 24
    assert rows.generation.notna().all() and rows.forecast.notna().all()
    cutoff = pd.Timestamp("2026-01-14T09:00:00Z")
    assert (rows.publishTime <= cutoff).all()
    # This cached timestamp was checked against live Elexon WINDFOR revisions.
    sample = rows.loc[rows.startTime == pd.Timestamp("2026-01-15T00:00:00Z")].iloc[0]
    assert sample.publishTime == pd.Timestamp("2026-01-14T07:30:00Z")
    assert sample.forecast == 15834.0
    assert sample.generation == 14456.5
