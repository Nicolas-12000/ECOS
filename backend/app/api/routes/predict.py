import logging
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException

from app.schemas.epidemiology import PredictRequest, PredictResponse, PredictionItem
from app.services.epidemiology import OUTBREAK_THRESHOLD, VALID_DISEASES, get_last_known_features

logger = logging.getLogger(__name__)
router = APIRouter()

REPO_ROOT = Path(__file__).resolve().parents[4]
_MODEL_PATH_V1 = REPO_ROOT / "models/baseline_v1.joblib"
_MODEL_PATH_V0 = REPO_ROOT / "models/baseline_v0.joblib"

CLIMATE_COLS = ["temp_avg_c", "temp_min_c", "temp_max_c", "humidity_avg_pct", "precipitation_mm"]
EXOG_COLS = ["vaccination_coverage_pct", "rips_visits_total", "mobility_index"]


def _load_model():
    """Carga el modelo más reciente disponible (v1 → v0 fallback)."""
    import joblib
    for path in [_MODEL_PATH_V1, _MODEL_PATH_V0]:
        if path.exists():
            logger.info("Loading model from %s", path)
            return joblib.load(path)
    return None


def _build_input_row(row: pd.Series, lag_rows: pd.DataFrame, weeks_ahead: int) -> pd.DataFrame | None:
    """
    Construye un único vector de features para predecir `weeks_ahead` semanas adelante.
    Usa los lags disponibles en el histórico y las últimas condiciones climáticas/exógenas.
    """
    numeric = {
        "epi_year": int(row["epi_year"]),
        "epi_week": int(row["epi_week"]) + weeks_ahead,
        "cases_lag_1": float(lag_rows["cases_total"].iloc[0]) if len(lag_rows) >= 1 else 0.0,
        "cases_lag_2": float(lag_rows["cases_total"].iloc[1]) if len(lag_rows) >= 2 else 0.0,
        "cases_lag_4": float(lag_rows["cases_total"].iloc[3]) if len(lag_rows) >= 4 else 0.0,
    }
    for col in CLIMATE_COLS + EXOG_COLS:
        numeric[col] = float(row[col]) if col in row.index and pd.notna(row[col]) else 0.0

    return pd.DataFrame([numeric])


@router.post("/predict", response_model=PredictResponse, summary="Predice casos por municipio y enfermedad")
def predict(req: PredictRequest):
    """
    Predice el número de casos esperados para las próximas `weeks_ahead` semanas
    en un municipio dado para una enfermedad específica.
    Retorna el flag de alerta de brote basado en el umbral epidemiológico.
    """
    if req.disease not in VALID_DISEASES:
        raise HTTPException(status_code=422, detail=f"disease must be one of {sorted(VALID_DISEASES)}")
    if not (1 <= req.weeks_ahead <= 4):
        raise HTTPException(status_code=422, detail="weeks_ahead must be between 1 and 4")

    model = _load_model()
    if model is None:
        raise HTTPException(status_code=503, detail="Model not available. Run the training pipeline first.")

    last_row = get_last_known_features(req.municipio_code, req.disease)
    if last_row is None:
        raise HTTPException(
            status_code=404,
            detail=f"No historical data for municipio_code={req.municipio_code} disease={req.disease}",
        )

    from app.services.epidemiology import get_history
    history = get_history(req.municipio_code, req.disease, limit=10)
    history = history.sort_values("week_start_date", ascending=False).reset_index(drop=True)

    predictions = []
    last_week = int(last_row["epi_week"])
    last_year = int(last_row["epi_year"])

    for i in range(1, req.weeks_ahead + 1):
        target_week = last_week + i
        target_year = last_year
        if target_week > 52:
            target_week -= 52
            target_year += 1

        X_row = _build_input_row(last_row, history, weeks_ahead=i)
        if X_row is None:
            continue

        # Align to model feature columns
        try:
            expected_cols = model.get_booster().feature_names
            X_aligned = X_row.reindex(columns=expected_cols, fill_value=0)
        except Exception:
            X_aligned = X_row

        predicted = float(model.predict(X_aligned)[0])
        predicted = max(0.0, predicted)

        # Approximate week start date
        try:
            import datetime
            week_start = datetime.date.fromisocalendar(target_year, target_week, 1)
        except Exception:
            week_start = None

        predictions.append(PredictionItem(
            epi_year=target_year,
            epi_week=target_week,
            week_start_date=week_start,
            disease=req.disease,
            municipio_code=req.municipio_code,
            departamento_code=str(last_row.get("departamento_code", "")),
            predicted_cases=round(predicted, 2),
            outbreak_flag=predicted >= OUTBREAK_THRESHOLD,
            outbreak_threshold=OUTBREAK_THRESHOLD,
        ))

    return PredictResponse(
        municipio_code=req.municipio_code,
        disease=req.disease,
        predictions=predictions,
    )
