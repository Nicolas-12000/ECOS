import logging

from fastapi import APIRouter, HTTPException

from app.schemas.epidemiology import PredictRequest, PredictResponse, PredictionItem
from app.services.prediction import predict_cases
from app.services.epidemiology import VALID_DISEASES

logger = logging.getLogger(__name__)
router = APIRouter()

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
