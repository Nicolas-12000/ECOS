import logging

from fastapi import APIRouter, HTTPException, Query

from app.schemas.epidemiology import SignalsItem, SignalsResponse
from app.services.epidemiology import VALID_DISEASES, get_signals

logger = logging.getLogger(__name__)
router = APIRouter()

FLOAT_OR_NONE = lambda v: float(v) if v is not None and str(v) != "nan" else None


@router.get("/signals", response_model=SignalsResponse, summary="Señales tempranas por departamento y enfermedad")
def signals(
    departamento_code: str = Query(..., description="Código DANE departamento (2 dígitos)"),
    disease: str = Query(..., description="dengue | chikungunya | zika | malaria"),
    limit: int = Query(52, ge=1, le=260, description="Semanas a retornar (default 1 año)"),
):
    """
    Retorna señales tempranas agregadas a nivel departamental:
    vacunación, RIPS, movilidad y señales web (Trends/RSS).
    Ordenado de más reciente a más antiguo.
    """
    if disease not in VALID_DISEASES:
        raise HTTPException(status_code=422, detail=f"disease must be one of {sorted(VALID_DISEASES)}")

    df = get_signals(departamento_code, disease, limit=limit)
    if df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No signals found for departamento_code={departamento_code} disease={disease}",
        )

    records = [
        SignalsItem(
            epi_year=int(row["epi_year"]),
            epi_week=int(row["epi_week"]),
            week_start_date=row["week_start_date"].date() if hasattr(row["week_start_date"], "date") else row["week_start_date"],
            departamento_code=str(row.get("departamento_code", "")),
            disease=row["disease"],
            vaccination_coverage_pct=FLOAT_OR_NONE(row.get("vaccination_coverage_pct")),
            rips_visits_total=FLOAT_OR_NONE(row.get("rips_visits_total")),
            mobility_index=FLOAT_OR_NONE(row.get("mobility_index")),
            trends_score=FLOAT_OR_NONE(row.get("trends_score")),
            rss_mentions=FLOAT_OR_NONE(row.get("rss_mentions")),
            signals_score=FLOAT_OR_NONE(row.get("signals_score")),
        )
        for _, row in df.iterrows()
    ]

    return SignalsResponse(
        departamento_code=departamento_code,
        disease=disease,
        records=records,
    )
