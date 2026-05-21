import logging

from fastapi import APIRouter, HTTPException, Query

from app.schemas.epidemiology import HistoryItem, HistoryResponse
from app.services.epidemiology import VALID_DISEASES, get_history

logger = logging.getLogger(__name__)
router = APIRouter()

FLOAT_OR_NONE = lambda v: float(v) if v is not None and str(v) != "nan" else None
INT_OR_NONE = lambda v: int(v) if v is not None else None


@router.get("/history", response_model=HistoryResponse, summary="Histórico de casos por municipio y enfermedad")
def history(
    municipio_code: str = Query(..., description="Código DANE municipio (5 dígitos)"),
    disease: str = Query(..., description="dengue | chikungunya | zika | malaria"),
    limit: int = Query(104, ge=1, le=520, description="Semanas a retornar (default 2 años)"),
):
    """
    Retorna el histórico de casos reportados en SIVIGILA para un municipio y enfermedad.
    Incluye variables climáticas disponibles (temperatura, humedad, precipitación).
    Ordenado de más reciente a más antiguo.
    """
    if disease not in VALID_DISEASES:
        raise HTTPException(status_code=422, detail=f"disease must be one of {sorted(VALID_DISEASES)}")

    df = get_history(municipio_code, disease, limit=limit)
    if df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for municipio_code={municipio_code} disease={disease}",
        )

    records = [
        HistoryItem(
            epi_year=int(row["epi_year"]),
            epi_week=int(row["epi_week"]),
            week_start_date=row["week_start_date"].date() if hasattr(row["week_start_date"], "date") else row["week_start_date"],
            disease=row["disease"],
            municipio_code=row["municipio_code"],
            departamento_code=str(row.get("departamento_code", "")),
            cases_total=int(row["cases_total"]),
            temp_avg_c=FLOAT_OR_NONE(row.get("temp_avg_c")),
            precipitation_mm=FLOAT_OR_NONE(row.get("precipitation_mm")),
        )
        for _, row in df.iterrows()
    ]

    return HistoryResponse(
        municipio_code=municipio_code,
        disease=disease,
        records=records,
    )
