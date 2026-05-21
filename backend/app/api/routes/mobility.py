from fastapi import APIRouter, Query, HTTPException
from app.schemas.epidemiology import MobilityODResponse, MobilityODItem, MobilityArcResponse, MobilityArcItem
from app.services.epidemiology import get_mobility, get_mobility_od_map as load_mobility_od_map

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


@router.get("/mobility/od-map", response_model=MobilityArcResponse, summary="Mapa OD agregado por departamento")
def get_mobility_od_map(limit: int = Query(200, ge=10, le=1000)):
    df = load_mobility_od_map(limit=limit)
    if df.empty:
        raise HTTPException(status_code=404, detail="No OD mobility data found")

    records = [
        MobilityArcItem(
            origin_code=str(row["origin_code"]),
            dest_code=str(row["dest_code"]),
            origin_lat=float(row["origin_lat"]),
            origin_lon=float(row["origin_lon"]),
            dest_lat=float(row["dest_lat"]),
            dest_lon=float(row["dest_lon"]),
            passengers=float(row["passengers"]),
        )
        for _, row in df.iterrows()
    ]

    return MobilityArcResponse(arcs=records, total=len(records))
