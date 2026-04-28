import logging

from fastapi import APIRouter, HTTPException, Query

from app.schemas.epidemiology import SignalsItem, SignalsResponse
from app.services.epidemiology import VALID_DISEASES, get_signals

logger = logging.getLogger(__name__)
router = APIRouter()

FLOAT_OR_NONE = lambda v: float(v) if v is not None and str(v) != "nan" else None
INT_OR_NONE = lambda v: int(v) if v is not None and str(v) != "nan" else None


@router.get("/signals", response_model=SignalsResponse, summary="Señales tempranas por departamento y enfermedad")
def signals(
    departamento_code: str = Query(..., description="Código DANE departamento (2 dígitos)"),
    disease: str = Query(..., description="dengue | chikungunya | zika | malaria"),
    limit: int = Query(52, ge=1, le=260, description="Semanas a retornar (default 1 año)"),
):
    """
    Retorna las señales tempranas exógenas integradas para un departamento y enfermedad:
    - `rips_visits_total`: atenciones médicas reportadas (señal paralela a SIVIGILA).
    - `mobility_index`: flujo total de pasajeros intermunicipales.
    - `vaccination_coverage_pct`: cobertura de vacunación (anual replicada por semana).

    Estas señales son las features exógenas del modelo final y permiten visualizar
    en el dashboard el contexto que explica cada predicción.
    """
    if disease not in VALID_DISEASES:
        raise HTTPException(status_code=422, detail=f"disease must be one of {sorted(VALID_DISEASES)}")

    df = get_signals(departamento_code, disease, limit=limit)
    if df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No signals found for departamento_code={departamento_code} disease={disease}. "
                   "Dataset may be incomplete or missing exogenous features. Run the weekly curation pipeline.",
        )

    records = [
        SignalsItem(
            epi_year=int(row["epi_year"]),
            epi_week=int(row["epi_week"]),
            week_start_date=row["week_start_date"].date() if hasattr(row["week_start_date"], "date") else row["week_start_date"],
            departamento_code=str(row["departamento_code"]),
            disease=row["disease"],
            rips_visits_total=INT_OR_NONE(row.get("rips_visits_total")),
            mobility_index=FLOAT_OR_NONE(row.get("mobility_index")),
            vaccination_coverage_pct=FLOAT_OR_NONE(row.get("vaccination_coverage_pct")),
        )
        for _, row in df.iterrows()
    ]

    return SignalsResponse(
        departamento_code=departamento_code,
        disease=disease,
        records=records,
    )
