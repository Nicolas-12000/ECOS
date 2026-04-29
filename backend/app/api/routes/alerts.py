"""Alerts endpoint — surfaces municipalities with active outbreak predictions."""

import logging

from fastapi import APIRouter, Query

from app.services.epidemiology import VALID_DISEASES, OUTBREAK_THRESHOLD

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/alerts",
    summary="Alertas activas de brote por enfermedad",
)
def alerts(
    disease: str | None = Query(None, description="Filtrar por enfermedad (opcional)"),
    limit: int = Query(50, ge=1, le=200),
):
    """
    Retorna los municipios con mayor riesgo de brote basándose en los datos
    más recientes del dataset curado. No requiere ejecutar predicción en
    tiempo real — usa las últimas observaciones y señales.
    """
    from app.services.epidemiology import _load_df

    try:
        df = _load_df()
    except FileNotFoundError:
        return {"alerts": [], "message": "No curated data available. Run generate_demo_data.py first."}

    # Get the most recent week
    latest_date = df["week_start_date"].max()
    recent = df[df["week_start_date"] == latest_date].copy()

    if disease:
        if disease not in VALID_DISEASES:
            return {"alerts": [], "message": f"disease must be one of {sorted(VALID_DISEASES)}"}
        recent = recent[recent["disease"] == disease]

    # Flag outbreak based on threshold
    recent = recent[recent["cases_total"] >= OUTBREAK_THRESHOLD]
    recent = recent.sort_values("cases_total", ascending=False).head(limit)

    alert_list = []
    for _, row in recent.iterrows():
        alert_list.append({
            "municipio_code": row["municipio_code"],
            "departamento_code": str(row.get("departamento_code", "")),
            "disease": row["disease"],
            "epi_year": int(row["epi_year"]),
            "epi_week": int(row["epi_week"]),
            "cases_total": int(row["cases_total"]),
            "outbreak_threshold": OUTBREAK_THRESHOLD,
            "risk_level": (
                "critical" if row["cases_total"] >= OUTBREAK_THRESHOLD * 3
                else "high" if row["cases_total"] >= OUTBREAK_THRESHOLD * 2
                else "moderate"
            ),
            "signals": {
                "trends_score": round(float(row.get("trends_score", 0) or 0), 2),
                "rss_mentions": int(row.get("rss_mentions", 0) or 0),
                "signals_score": round(float(row.get("signals_score", 0) or 0), 3),
            },
        })

    return {
        "alerts": alert_list,
        "total": len(alert_list),
        "latest_week": str(latest_date.date()) if latest_date else None,
        "outbreak_threshold": OUTBREAK_THRESHOLD,
        "disease_filter": disease,
    }
