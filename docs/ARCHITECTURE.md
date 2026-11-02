# Architecture

```mermaid
flowchart LR
  E[Elexon BMRS Insights API] --> F[Chunked snapshot fetch script]
  F --> J[(Committed JSON: actuals + forecasts)]
  J --> S[FastAPI domain service]
  S --> M[UTC cutoff selection + metrics]
  M --> R[REST JSON / CSV]
  R --> U[React + TypeScript + Recharts]
  U --> B[Buyer decision and accuracy views]
```

## Data flow

`fetch_data.py` requests FUELHH one settlement day at a time and WINDFOR one publication day at a time, with retries and bounded HTTP timeouts. It filters FUELHH to WIND and forecast delivery times to January 2026. Snapshot JSON files are read locally by FastAPI, so runtime operation is offline once those files are populated.

For each hourly forecast delivery timestamp, the service computes the previous delivery date's configurable Europe/London cutoff, converts it to UTC, filters WINDFOR publications to `publishTime <= cutoff`, and chooses the latest publication. FUELHH half-hour readings are averaged within each UTC hour, then actual hourly means and selected forecasts are outer joined on UTC `startTime`; missing rows remain visible. Daily energy sums each hourly MW forecast across its one-hour interval. Horizon charts join every forecast vintage to that same hourly actual mean, separately from the cutoff selection.

## Module responsibilities

- `backend/scripts/fetch_data.py`: network ingestion, chunking and retry.
- `backend/app/main.py`: validation, domain selection, analysis calculations, REST and CSV output.
- `backend/data/`: committed snapshot location.
- `frontend/src/main.tsx`: four dashboard sections and charts.
- `api/index.py`, `vercel.json`: serverless API routing and static Vite build.
- Dockerfiles and compose: local production-like run.

## Deployment

Docker runs FastAPI on port 8000 and Nginx on 3000. Vercel builds the frontend as a static Vite artifact and bundles the FastAPI ASGI entrypoint with the approximately 2.3 MB snapshot. No runtime data source is required. Vercel's package limits should be checked after the real snapshot is populated.
