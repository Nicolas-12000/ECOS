import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.schemas.epidemiology import PredictRequest, PredictResponse, PredictionItem
from app.services.prediction import predict_cases
from app.services.epidemiology import VALID_DISEASES
from app.core.db import get_db_connection

logger = logging.getLogger(__name__)
router = APIRouter()


def _db_execute(query: str, params: tuple = ()) -> list:
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.fetchall()
    except Exception as e:
        logger.error("DB query error: %s", e)
        return []


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

    try:
        predictions_raw = predict_cases(req.municipio_code, req.disease, weeks_ahead=req.weeks_ahead)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        message = str(exc)
        if "No historical data" in message:
            raise HTTPException(status_code=404, detail=message) from exc
        raise HTTPException(status_code=503, detail=message) from exc

    return PredictResponse(
        municipio_code=req.municipio_code,
        disease=req.disease,
        predictions=[PredictionItem(**item) for item in predictions_raw],
    )


@router.get("/predictions", summary="Obtiene predicciones precomputadas")
def get_predictions(
    disease: Optional[str] = Query(None),
    departamento_code: Optional[str] = Query(None),
    municipio_code: Optional[str] = Query(None),
    epi_year: Optional[int] = Query(None),
    epi_week: Optional[int] = Query(None),
    limit: int = Query(10, ge=1, le=100),
):
    """
    Obtiene predicciones precomputadas almacenadas en Supabase.
    Se pueden filtrar por enfermedad, departamento, municipio, año y semana epidemiológica.
    """
    if disease and disease not in VALID_DISEASES:
        raise HTTPException(status_code=422, detail=f"disease must be one of {sorted(VALID_DISEASES)}")

    filters = []
    params = []
    if disease:
        filters.append("disease = %s")
        params.append(disease)
    if departamento_code:
        filters.append("departamento_code = %s")
        params.append(departamento_code)
    if municipio_code:
        filters.append("municipio_code = %s")
        params.append(municipio_code)
    if epi_year:
        filters.append("epi_year = %s")
        params.append(epi_year)
    if epi_week:
        filters.append("epi_week = %s")
        params.append(epi_week)

    rows = _db_execute(f"""
        SELECT 
            departamento_code, municipio_code, disease,
            epi_year, epi_week, week_start_date,
            predicted_cases, outbreak_flag, outbreak_threshold,
            endemic_risk, shap_top_factors
        FROM public.predictions
        WHERE {" AND ".join(filters) if filters else "1=1"}
        ORDER BY week_start_date DESC
        LIMIT %s
    """, tuple(params + [limit]))

    predictions = []
    for row in rows:
        predictions.append({
            "departamento_code": row[0],
            "municipio_code": row[1],
            "disease": row[2],
            "epi_year": row[3],
            "epi_week": row[4],
            "week_start_date": row[5],
            "predicted_cases": row[6],
            "outbreak_flag": row[7],
            "outbreak_threshold": row[8],
            "endemic_risk": row[9],
            "shap_top_factors": row[10],
        })

    return {"predictions": predictions}
