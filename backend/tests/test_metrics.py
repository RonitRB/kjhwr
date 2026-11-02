import pandas as pd
from app.main import _metrics, _select_latest_forecasts


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
