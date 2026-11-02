import json
import os
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import httpx

BASE = os.getenv("ELEXON_BASE_URL", "https://data.elexon.co.uk/bmrs/api/v1/datasets")
OUT = Path(__file__).resolve().parents[1] / "data"
OUT.mkdir(exist_ok=True)


def get(dataset, params):
    for attempt in range(5):
        try:
            r = httpx.get(
                f"{BASE}/{dataset}/stream", params={**params, "format": "json"}, timeout=45
            )
            r.raise_for_status()
            data = r.json()
            if not isinstance(data, list):
                raise ValueError(f"Unexpected {dataset} response: {data}")
            return data
        except Exception:
            if attempt == 4:
                raise
            time.sleep(2**attempt)


def main():
    actual = []
    for i in range(32):
        d = date(2026, 1, 1) + timedelta(days=i)
        rows = get(
            "FUELHH",
            {
                "settlementDateFrom": d.isoformat(),
                "settlementDateTo": d.isoformat(),
                "fuelType": "WIND",
            },
        )
        actual += [r for r in rows if r.get("fuelType") == "WIND"]
        print("FUELHH", d, len(rows))
    utc_start = "2026-01-01T00:00:00Z"
    utc_end = "2026-02-01T00:00:00Z"
    actual = [row for row in actual if utc_start <= str(row.get("startTime", "")) < utc_end]
    forecasts = []
    start = date(2025, 12, 25)
    for i in range(38):
        d = start + timedelta(days=i)
        lo = f"{d.isoformat()}T00:00:00Z"
        hi = f"{(d + timedelta(days=1)).isoformat()}T00:00:00Z"
        rows = get("WINDFOR", {"publishDateTimeFrom": lo, "publishDateTimeTo": hi})
        forecasts += [r for r in rows if "2026-01-" in str(r.get("startTime", ""))]
        print("WINDFOR", d, len(rows))
    (OUT / "actuals.json").write_text(json.dumps(actual, separators=(",", ":")))
    (OUT / "forecasts.json").write_text(json.dumps(forecasts, separators=(",", ":")))
    manifest = {
        "downloadedAtUtc": datetime.now(timezone.utc).isoformat(),
        "actualDataset": "FUELHH",
        "forecastDataset": "WINDFOR",
        "actualRows": len(actual),
        "forecastRows": len(forecasts),
        "actualStartUtc": utc_start,
        "actualEndUtc": "2026-01-31T23:30:00Z",
        "forecastPublishFromUtc": "2025-12-25T00:00:00Z",
        "forecastPublishToUtcExclusive": "2026-02-01T00:00:00Z",
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print("Saved", len(actual), "actual and", len(forecasts), "forecast rows")


if __name__ == "__main__":
    main()
