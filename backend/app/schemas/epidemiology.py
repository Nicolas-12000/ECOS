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
    endemic_risk: Optional[str] = None
    shap_values: Optional[dict[str, float]] = None


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
    vaccination_coverage_pct: Optional[float] = None
    trends_score: Optional[float] = None
    rss_mentions: Optional[float] = None
    signals_score: Optional[float] = None


class SignalsResponse(BaseModel):
    departamento_code: str
    disease: str
    records: list[SignalsItem]


# ─── /chat ────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str
    disease: Optional[str] = None
    municipio_code: Optional[str] = None
    departamento_code: Optional[str] = None


class ChatSource(BaseModel):
    title: str
    excerpt: str
    source_type: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSource]
    disease: Optional[str] = None
    municipio_code: Optional[str] = None
    departamento_code: Optional[str] = None


# ─── /shap ────────────────────────────────────────────────────────────────

class ShapItem(BaseModel):
    feature: str
    value: Optional[float] = None
    shap_value: float
    direction: str


class ShapResponse(BaseModel):
    disease: str
    municipio_code: str
    epi_year: int
    epi_week: int
    predicted_cases: Optional[float] = None
    outbreak_flag: Optional[bool] = None
    features: list[ShapItem]


# ─── /alerts ───────────────────────────────────────────────────────────────

class AlertItem(BaseModel):
    municipio_code: str
    departamento_code: str
    disease: str
    epi_year: int
    epi_week: int
    cases_total: int
    outbreak_threshold: float
    endemic_p25: Optional[float] = None
    endemic_p50: Optional[float] = None
    endemic_p75: Optional[float] = None
    endemic_p90: Optional[float] = None
    risk_level: str
    signals: dict


class AlertResponse(BaseModel):
    alerts: list[AlertItem]
    total: int
    latest_week: Optional[str] = None
    outbreak_threshold: float
    disease_filter: Optional[str] = None


# ─── V1 New Endpoints ────────────────────────────────────────────────────────

class TrendsItem(BaseModel):
    epi_year: int
    epi_week: int
    week_start_date: date
    disease: str
    trends_score: float

class TrendsResponse(BaseModel):
    departamento_code: str
    disease: str
    records: list[TrendsItem]

class NewsArticle(BaseModel):
    title: str
    link: str
    source: str
    published: str
    summary: Optional[str] = None
    diseases: list[str]

class MobilityODItem(BaseModel):
    epi_year: int
    epi_week: int
    municipio_code: str
    mobility_in: float
    mobility_out: float

class MobilityODResponse(BaseModel):
    municipio_code: str
    records: list[MobilityODItem]

class WhatIfRequest(BaseModel):
    municipio_code: str
    disease: str
    weeks_ahead: int = 4
    adjustments: dict[str, float]  # e.g. {"vaccination_coverage_pct": +10.0}

class WhatIfResponse(BaseModel):
    original_predictions: list[PredictionItem]
    adjusted_predictions: list[PredictionItem]
    delta_total: float

class TimeseriesResponse(BaseModel):
    municipio_code: str
    disease: str
    history: list[HistoryItem]
    predictions: list[PredictionItem]
