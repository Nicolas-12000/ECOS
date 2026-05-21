from fastapi import APIRouter, Query, HTTPException
from app.schemas.epidemiology import TimeseriesResponse, HistoryItem, PredictionItem
from app.services.epidemiology import get_history, VALID_DISEASES
from app.services.prediction import predict_cases

router = APIRouter()

@router.get("/timeseries", response_model=TimeseriesResponse, summary="Historia y predicción unificadas")
def get_timeseries(
    municipio_code: str = Query(...),
    disease: str = Query(...),
    weeks_history: int = Query(52, ge=1, le=156),
    weeks_ahead: int = Query(4, ge=1, le=4)
):
    if disease not in VALID_DISEASES:
        raise HTTPException(status_code=422, detail=f"disease must be one of {sorted(VALID_DISEASES)}")

    try:
        history_df = get_history(municipio_code, disease, limit=weeks_history)
        predictions_raw = predict_cases(municipio_code, disease, weeks_ahead=weeks_ahead)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    history_records = [
        HistoryItem(
            epi_year=int(row["epi_year"]),
            epi_week=int(row["epi_week"]),
            week_start_date=row["week_start_date"].date() if hasattr(row["week_start_date"], "date") else row["week_start_date"],
            disease=row["disease"],
            municipio_code=row["municipio_code"],
            departamento_code=row["departamento_code"],
            cases_total=int(row["cases_total"]),
            temp_avg_c=float(row["temp_avg_c"]) if row.get("temp_avg_c") else None,
            precipitation_mm=float(row["precipitation_mm"]) if row.get("precipitation_mm") else None
        )
        for _, row in history_df.iterrows()
    ]

    return TimeseriesResponse(
        municipio_code=municipio_code,
        disease=disease,
        history=history_records,
        predictions=[PredictionItem(**p) for p in predictions_raw]
    )
