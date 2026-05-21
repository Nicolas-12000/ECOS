from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.epidemiology import calculate_endemic_channel, VALID_DISEASES

router = APIRouter()

class EndemicChannelResponse(BaseModel):
    municipio_code: str
    disease: str
    epi_week: int
    p25: Optional[float] = None
    p50: Optional[float] = None
    p75: Optional[float] = None
    p90: Optional[float] = None
    n: int

@router.get("/endemic/{municipio_code}/{disease}/{epi_week}", response_model=EndemicChannelResponse)
def get_endemic_channel(municipio_code: str, disease: str, epi_week: int):
    """
    Retorna el canal endémico (percentiles históricos) para un municipio, 
    enfermedad y semana epidemiológica dados.
    """
    if disease not in VALID_DISEASES:
        raise HTTPException(status_code=422, detail=f"disease must be one of {sorted(VALID_DISEASES)}")
    if not (1 <= epi_week <= 53):
        raise HTTPException(status_code=422, detail="epi_week must be between 1 and 53")

    result = calculate_endemic_channel(municipio_code, disease, epi_week)
    
    if result["n"] == 0:
        raise HTTPException(status_code=404, detail="No historical data found for the given parameters")

    return EndemicChannelResponse(
        municipio_code=municipio_code,
        disease=disease,
        epi_week=epi_week,
        **result
    )
