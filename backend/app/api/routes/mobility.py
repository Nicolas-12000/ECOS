from fastapi import APIRouter, Query, HTTPException
from app.schemas.epidemiology import MobilityODResponse, MobilityODItem
from app.services.epidemiology import get_mobility

router = APIRouter()

@router.get("/mobility/od", response_model=MobilityODResponse, summary="Flujos de movilidad por municipio")
def get_mobility_od(
    municipio_code: str = Query(..., description="Código DANE municipio (5 dígitos)"),
    limit: int = Query(52, ge=1, le=260)
):
    df = get_mobility(municipio_code, limit=limit)
    if df.empty:
        raise HTTPException(status_code=404, detail="No mobility data found")

    records = [
        MobilityODItem(
            epi_year=int(row["epi_year"]),
            epi_week=int(row["epi_week"]),
            municipio_code=municipio_code,
            mobility_in=float(row["mobility_in"]) if row["mobility_in"] is not None else 0.0,
            mobility_out=float(row["mobility_out"]) if row["mobility_out"] is not None else 0.0
        )
        for _, row in df.iterrows()
    ]

    return MobilityODResponse(
        municipio_code=municipio_code,
        records=records
    )
