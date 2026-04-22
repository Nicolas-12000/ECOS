from datetime import date
from typing import Optional

from pydantic import BaseModel


# ─── /predict ────────────────────────────────────────────────────────────────

class PredictRequest(BaseModel):
    municipio_code: str
    disease: str  # dengue | chikungunya | zika | malaria
    weeks_ahead: int = 2  # 1-4


class PredictionItem(BaseModel):
    epi_year: int
    epi_week: int
    week_start_date: date
    disease: str
    municipio_code: str
    departamento_code: str
    predicted_cases: float
    outbreak_flag: bool
    outbreak_threshold: float


class PredictResponse(BaseModel):
    municipio_code: str
    disease: str
    predictions: list[PredictionItem]


# ─── /history ────────────────────────────────────────────────────────────────

class HistoryItem(BaseModel):
    epi_year: int
    epi_week: int
    week_start_date: date
    disease: str
    municipio_code: str
    departamento_code: str
    cases_total: int
    temp_avg_c: Optional[float] = None
    humidity_avg_pct: Optional[float] = None
    precipitation_mm: Optional[float] = None


class HistoryResponse(BaseModel):
    municipio_code: str
    disease: str
    records: list[HistoryItem]


# ─── /signals ────────────────────────────────────────────────────────────────

class SignalsItem(BaseModel):
    epi_year: int
    epi_week: int
    week_start_date: date
    departamento_code: str
    disease: str
    rips_visits_total: Optional[int] = None
    mobility_index: Optional[float] = None
    vaccination_coverage_pct: Optional[float] = None


class SignalsResponse(BaseModel):
    departamento_code: str
    disease: str
    records: list[SignalsItem]
