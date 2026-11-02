# January 2026 analysis — real Elexon snapshot

Snapshot refreshed from the public Elexon BMRS Insights API on 2026-11-02. The downloader requested FUELHH by settlement date and WINDFOR by publication date, retaining FUELHH UTC start times in January and every WINDFOR vintage whose delivery startTime is in January.

## Resolution and coverage

FUELHH provides two 30-minute national WIND measurements per clock hour; WINDFOR provides hourly forecast periods. We now average the two UTC FUELHH readings within each hour and join that hourly mean to WINDFOR on its UTC `startTime`. The 1,488 actual readings become 744 hourly observations (31 × 24). At the default 09:00 Europe/London cutoff, all **744 / 744 hourly periods match (100.0% coverage)**, with zero missing forecasts or actuals. The original half-hour observations remain in the snapshot as source data and are not counted as independent forecast evaluations.

## Pairing audit: 2026-01-15

On Jan 15, London is on GMT, so the configured 09:00 Europe/London cutoff on Jan 14 is 2026-01-14 09:00 UTC. For every target hour, selection is the maximum `publishTime` no later than that instant. We queried the live Elexon WINDFOR stream for Jan 14 and checked the target 00:00 UTC revisions: Elexon returned publishes at 02:30, 04:30, 07:30, 09:30, 11:30, 15:30, 18:30 and 22:30 UTC. The selected 07:30 publish is the latest eligible revision; the 09:30 and later revisions are correctly excluded. The live FUELHH endpoint returned the expected Jan 15 settlement-day half-hours, and the values below are their hourly means. `startTime` is aligned in UTC; no settlement-day or timezone offset was found.

| startTime (UTC) | publishTime (UTC) | Horizon (h) | Forecast (MW) | Actual hourly mean (MW) |
|---|---|---:|---:|---:|
| 2026-01-15 00:00 | 2026-01-14 07:30 | 16.5 | 15,834 | 14,456.5 |
| 2026-01-15 01:00 | 2026-01-14 07:30 | 17.5 | 15,478 | 14,358.0 |
| 2026-01-15 02:00 | 2026-01-14 07:30 | 18.5 | 15,066 | 14,368.0 |
| 2026-01-15 03:00 | 2026-01-14 07:30 | 19.5 | 14,655 | 14,139.0 |
| 2026-01-15 04:00 | 2026-01-14 07:30 | 20.5 | 14,497 | 13,807.0 |
| 2026-01-15 05:00 | 2026-01-14 07:30 | 21.5 | 14,419 | 13,546.5 |
| 2026-01-15 06:00 | 2026-01-14 07:30 | 22.5 | 14,017 | 13,387.0 |
| 2026-01-15 07:00 | 2026-01-14 07:30 | 23.5 | 13,411 | 13,169.0 |
| 2026-01-15 08:00 | 2026-01-14 07:30 | 24.5 | 12,931 | 12,510.5 |
| 2026-01-15 09:00 | 2026-01-14 07:30 | 25.5 | 12,576 | 12,193.0 |

This check confirms the API selection and hourly pairing against live Elexon stream records. The 00:00 target's 07:30 forecast value (15,834 MW) matches the live record. The bias remains large after correcting the grain, so we found no pairing defect to explain it.

## Accuracy at the default cutoff

Metrics below use all 744 hourly pairs. Error is actual hourly mean minus forecast. NMAE is the mean of `|error| / max(actual, 1 MW)` per hour; it is not MAE divided by a single system capacity.

| Metric | Result |
|---|---:|
| MAE | **2,142 MW** |
| RMSE | **2,612 MW** |
| Mean error / bias | **−1,852 MW** |
| NMAE | **22.38%** |
| R² | **0.604** |
| Pearson correlation | **0.928** |
| Absolute error P50 / P75 | **1,788 / 3,013 MW** |
| Absolute error P90 / P95 / P99 | **4,300 / 5,307 / 6,261 MW** |

A negative mean error means the forecast over-forecast wind by about 1.85 GW on average in this January sample. The 22.38% NMAE is confirmed by the corrected 744-point calculation. It remains unusually high enough to warrant operational scrutiny, but this one month and source pairing do not establish the cause. We verified the cutoff and UTC pairing on a concrete date; comparisons over more delivery months would be needed before applying any bias correction.

## Worst periods and slices

- Largest individual absolute error: **6,894 MW**, at 2026-01-12 01:00 UTC (forecast 20,942 MW; actual 14,048 MW; 17.5-hour horizon).
- Highest daily MAE: **5,375 MW** on 2026-01-28; next were Jan 12 at **4,868 MW** and Jan 11 at **4,802 MW** (24 hourly pairs each).
- Error was largest in the high-generation tercile: **2,443 MW MAE** (248 hours), compared with **2,097 MW** medium and **1,886 MW** low. Actual-generation tercile edges were approximately 9,366 MW and 14,658 MW.
- By Europe/London hour, the highest MAE was **2,535 MW at 05:00** (31 hours); the next were 03:00 at 2,516 MW and 04:00 at 2,507 MW.

## Error versus forecast horizon

Horizon diagnostics compare every available WINDFOR vintage to the same hourly actual mean. MAE rises from **1,776 MW at 0–4 hours** to **2,444 MW at 44–48 hours**, about 38% higher at the longest lead. The trend is generally upward across intermediate buckets. Each bucket contains 961–992 forecast-vintage records.

At the 20–24-hour bucket (midpoint 22 hours), signed-error P10/P90 was approximately **−4,041 MW / +130 MW**. The asymmetry is consistent with the observed over-forecast tendency. The dashboard applies the nearest horizon bucket's empirical signed-error P10/P90 to the forecast as a range. It is historical, not a calibrated probability interval or guarantee; the January sample informs both the range and evaluation, so it needs out-of-sample validation.

## Buyer recommendation

Keep the selected forecast vintage and its publication time visible. For this January snapshot, do not treat the centreline as an unbiased point estimate: the month has substantial average over-forecasting, larger errors at higher generation, and increased error at longer horizons. Use the horizon-matched empirical range as a planning sensitivity, validate coverage by delivery day, and test any bias adjustment on a separate period before changing procurement rules.
