# Recording script (under 10 minutes)

## Part 1 — Buyer pitch (0:00–4:30)

| Time | Screen / shot | Spoken track |
|---|---|---|
| 0:00–0:40 | Title, Northstar dashboard | Day-ahead buyers must commit before the delivery day, when wind remains uncertain. Windwatch makes the forecast vintage and its observed error visible. |
| 0:40–1:25 | Decision view controls | Select a January delivery day and the 09:00 London decision cutoff. The selected value is the latest Elexon forecast already published by that moment. |
| 1:25–2:15 | Forecast chart and settlement table | Inspect all 48 half-hour periods, forecast level, publication horizon and missing values. Export the exact rows as CSV. |
| 2:15–3:00 | Enter illustrative demand | With a buyer-entered demand value, the app shows a simple demand-minus-wind calculation. It does not introduce a separate demand feed. |
| 3:00–3:50 | Forecast vs actual and accuracy | Compare actual output with the cutoff-eligible forecast and inspect signed error and historic accuracy summaries. The cached January sample has 2,127 MW MAE, -1,852 MW signed bias, and 50% exact timestamp coverage. |
| 3:50–4:30 | Methodology | Emphasize that empirical error ranges help quantify uncertainty and are not guarantees. |

## Part 2 — Technical lead walkthrough (4:30–9:30)

| Time | Screen / shot | Spoken track |
|---|---|---|
| 4:30–5:15 | Architecture diagram | The downloader collects only FUELHH wind actuals and WINDFOR forecast vintages, then stores a local JSON snapshot. FastAPI serves analysis; React and Recharts provide the desk interface. |
| 5:15–6:20 | `fetch_data.py` | Requests are chunked by day with timeouts and retries. The committed snapshot contains 1,488 actual rows and 18,080 forecast vintages. The exact-time match is 50% because WINDFOR is hourly while FUELHH is half-hourly; the app surfaces this gap without filling it. |
| 6:20–7:25 | Backend selection and metrics | All joins are on UTC startTime. The selected publication is the maximum publishTime at or before the converted previous-day London cutoff. Coverage gaps stay in the result. |
| 7:25–8:20 | Frontend sections | Show decisions, forecast comparison, accuracy slices, and methodology. Input validation restricts delivery dates to January 2026. |
| 8:20–9:00 | Tests and CI | Walk through cutoff behavior, metric fixtures, API validation, Ruff, pytest, and frontend build checks. |
| 9:00–9:30 | Docker and Vercel config | Docker Compose runs the local stack. Vercel serves Vite static assets and routes API calls to the Python ASGI entrypoint. The real snapshot is included in the function bundle. |

Keep the full recording to 9 minutes 30 seconds maximum. Use the live Elexon snapshot and the coverage caveat shown in the app; do not hide the hourly-versus-half-hourly gaps.
