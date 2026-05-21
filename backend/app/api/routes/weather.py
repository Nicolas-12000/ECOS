from __future__ import annotations

import csv
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from app.services.weather import fetch_open_meteo_weekly

router = APIRouter()

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_CSV_PATH = REPO_ROOT / "data/raw/open_meteo_weekly.csv"


@router.get(
    "/weather/weekly",
    summary="Open-Meteo weekly signals (optional snapshot)",
)
def weather_weekly(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date: str = Query(..., description="YYYY-MM-DD"),
    municipio_code: str | None = Query(None, description="DANE municipio (optional)"),
    departamento_code: str | None = Query(None, description="DANE departamento (optional)"),
    save_csv: bool = Query(False, description="Append results to data/raw/open_meteo_weekly.csv"),
):
    try:
        weekly = fetch_open_meteo_weekly(lat, lon, start_date, end_date)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    rows = []
    for item in weekly:
        rows.append(
            {
                "week_start_date": item.week_start_date,
                "municipio_code": municipio_code,
                "departamento_code": departamento_code,
                "temperature_2m_max": item.temperature_2m_max,
                "temperature_2m_min": item.temperature_2m_min,
                "temperature_2m_mean": item.temperature_2m_mean,
                "precipitation_sum": item.precipitation_sum,
                "relative_humidity_2m_mean": item.relative_humidity_2m_mean,
            }
        )

    if save_csv:
        DEFAULT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        write_header = not DEFAULT_CSV_PATH.exists()
        with DEFAULT_CSV_PATH.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys())) if rows else None
            if writer and write_header:
                writer.writeheader()
            if writer:
                writer.writerows(rows)

    return {"data": rows}
