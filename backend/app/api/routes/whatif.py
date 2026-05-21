from fastapi import APIRouter, HTTPException
from app.schemas.epidemiology import WhatIfRequest, WhatIfResponse, PredictionItem
from app.services.prediction import predict_cases
from app.services.epidemiology import VALID_DISEASES

router = APIRouter()

@router.post("/whatif", response_model=WhatIfResponse, summary="Simulación What-if")
def what_if(req: WhatIfRequest):
    """
    Compara la predicción base con una predicción ajustada por variables exógenas
    (ej: aumento de vacunación, disminución de movilidad).
    """
    if req.disease not in VALID_DISEASES:
        raise HTTPException(status_code=422, detail=f"disease must be one of {sorted(VALID_DISEASES)}")

    try:
        # Original
        original = predict_cases(req.municipio_code, req.disease, weeks_ahead=req.weeks_ahead)
        # Adjusted
        adjusted = predict_cases(req.municipio_code, req.disease, weeks_ahead=req.weeks_ahead, adjustments=req.adjustments)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    total_orig = sum(p["predicted_cases"] for p in original)
    total_adj = sum(p["predicted_cases"] for p in adjusted)

    return WhatIfResponse(
        original_predictions=[PredictionItem(**p) for p in original],
        adjusted_predictions=[PredictionItem(**p) for p in adjusted],
        delta_total=round(total_adj - total_orig, 2)
    )
