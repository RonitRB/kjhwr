from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    dataAvailable: bool
    source: str
    snapshotUpdatedUtc: Optional[str] = None
    defaultCutoff: str = "09:00"


class DaysResponse(BaseModel):
    days: list[str]


class ForecastRow(BaseModel):
    startTime: datetime
    generation: Optional[float] = None
    forecast: Optional[float] = None
    publishTime: Optional[datetime] = None
    horizonHours: Optional[float] = None
    error: Optional[float] = None
    absError: Optional[float] = None
    uncertaintyLower: Optional[float] = None
    uncertaintyUpper: Optional[float] = None
    day: Optional[str] = None
    localTime: Optional[str] = None


class ForecastSummary(BaseModel):
    totalMWh: Optional[float] = None
    peakMW: Optional[float] = None
    minMW: Optional[float] = None
    averageMW: Optional[float] = None


class ForecastResponse(BaseModel):
    day: str
    cutoff: str
    timezone: str
    rows: list[ForecastRow]
    coverage: int
    missingForecast: int
    summary: ForecastSummary
