# January 2026 analysis — real Elexon snapshot

Snapshot refreshed from the public Elexon BMRS Insights API on 2026-11-02. The downloader made one FUELHH request per settlement date from 2026-01-01 through 2026-02-01 to cover the requested UTC start-time window, and one WINDFOR request per publication date from 2025-12-25 through 2026-01-31. It retained actual `startTime` values in `[2026-01-01T00:00Z, 2026-02-01T00:00Z)` and forecast records whose delivery `startTime` falls in January.

## Data coverage

- FUELHH returned 48 WIND records per settlement day. After strict UTC filtering, the cached actual snapshot contains **1,488 periods** (31 × 48), with no missing actuals in the evaluation window.
- WINDFOR returned 18,080 records for January delivery timestamps across the publication window. At the default 09:00 Europe/London cutoff, **744 of 1,488 actual timestamps matched (50.0%)**; 744 have no matching forecast and are left missing. The observed WINDFOR records are hourly while FUELHH is half-hourly. This product keeps the required exact `startTime` join and does not interpolate or duplicate forecasts to fill the other half-hours.
- Horizon diagnostics use all matched WINDFOR vintages, not only the cutoff selection. Each four-hour bucket contains about 961–992 records.

## Accuracy at the default cutoff

The following metrics are computed on the 744 exact timestamp matches for January UTC start times.

| Metric | Result |
|---|---:|
| MAE | **2,127 MW** |
| RMSE | **2,606 MW** |
| Mean error (actual − forecast) | **−1,852 MW** |
| NMAE, mean absolute error divided by max(actual, 1 MW) | **22.21%** |
| R² | **0.606** |
| Pearson correlation | **0.928** |
| Absolute error P50 / P75 | **1,759 / 2,997 MW** |
| Absolute error P90 / P95 / P99 | **4,306 / 5,351 / 6,139 MW** |

A negative mean error means the day-ahead forecast **over-forecast wind by about 1.85 GW on average** in this sample. Buyers using the forecast as a direct wind contribution should account for this directional tendency, but should validate over other months before applying a systematic adjustment.

## Worst periods and slices

- Largest individual absolute error: **6,894 MW**, at 2026-01-12 01:00 UTC (forecast 20,942 MW; actual 14,048 MW; 17.5-hour horizon).
- Highest daily MAE: **5,329 MW** on 2026-01-28 (24 exact hourly matches); next were Jan 12 at 4,875 MW and Jan 11 at 4,853 MW.
- Error was largest in the high-generation tercile: **2,448 MW MAE** (248 points), compared with 2,067 MW in medium and 1,867 MW in low. Tercile edges were approximately 9,366 MW and 14,658 MW actual generation.
- By Europe/London hour, the highest MAE was **2,521 MW at 05:00** (31 points); the lowest was 1,833 MW at 21:00 (31 points).

## Error versus forecast horizon

MAE increased from **1,772 MW at 0–4 hours** to **2,431 MW at 44–48 hours**, about 37% higher at the longest lead-time bucket. Intermediate buckets also trend upward overall, with some variation. This supports treating long-horizon values as less precise, rather than relying on one forecast error number for every lead time.

At the 20–24-hour bucket (midpoint 22 hours), signed error P10/P90 was approximately **−4,047 MW / +112 MW**. The large asymmetry is consistent with the observed over-forecast bias. The dashboard uses the nearest horizon bucket's empirical signed-error P10/P90 as a forecast range. This is a historical range, not a calibrated probability interval or a guarantee; the same January sample informs both summary and range, so out-of-sample validation is needed before operational use.

## Buyer recommendation

Keep the selected forecast vintage visible and retain the missing-period flag. For this month, do not treat the centreline as an unbiased point estimate: the sample is materially over-forecast on average, high-generation errors are larger, and error grows with horizon. Use the horizon-matched empirical range as a planning sensitivity, check actual coverage for every delivery day, and validate any bias correction on a separate period before changing procurement rules. The 50% strict-join coverage is a material limitation: one hourly WINDFOR point does not exist at each half-hourly FUELHH timestamp, and this version intentionally does not invent the in-between values.
