from fastapi import APIRouter, Query, HTTPException
from app.schemas.epidemiology import TrendsResponse, TrendsItem
from app.services.epidemiology import get_signals, VALID_DISEASES

router = APIRouter()

@router.get("/trends", response_model=TrendsResponse, summary="Tendencias de búsqueda por departamento")
def get_trends(
    departamento_code: str = Query(..., description="Código DANE departamento (2 dígitos)"),
    disease: str = Query(..., description="dengue | chikungunya | zika | malaria"),
    limit: int = Query(52, ge=1, le=260)
):
    if disease not in VALID_DISEASES:
        raise HTTPException(status_code=422, detail=f"disease must be one of {sorted(VALID_DISEASES)}")
    
    df = get_signals(departamento_code, disease, limit=limit)
    if df.empty or "trends_score" not in df.columns:
        raise HTTPException(status_code=404, detail="No trends data found")

    records = [
        TrendsItem(
            epi_year=int(row["epi_year"]),
            epi_week=int(row["epi_week"]),
            week_start_date=row["week_start_date"].date() if hasattr(row["week_start_date"], "date") else row["week_start_date"],
            disease=disease,
            trends_score=float(row["trends_score"]) if row["trends_score"] is not None else 0.0
        )
        for _, row in df.iterrows() if row["trends_score"] is not None
    ]

    return TrendsResponse(
        departamento_code=departamento_code,
        disease=disease,
        records=records
    )
