import logging
from pathlib import Path
from functools import lru_cache

import joblib
import pandas as pd

from app.services.epidemiology import (
    OUTBREAK_THRESHOLD,
    VALID_DISEASES,
    get_history,
    get_last_known_features,
    calculate_endemic_channel,
    classify_endemic_risk,
)
from models.hybrid_model import EcosHybridModel

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH_FINAL = REPO_ROOT / "models/final_model.joblib"

CLIMATE_COLS = [
    "temp_avg_c",
    "temp_min_c",
    "temp_max_c",
    "humidity_avg_pct",
    "precipitation_mm",
    "temp_avg_c_actual",
    "temp_min_c_actual",
    "temp_max_c_actual",
    "humidity_avg_pct_actual",
    "precipitation_mm_actual",
]
EXOG_COLS = [
    "vaccination_coverage_pct",
    "rips_visits_total",
    "mobility_in",
    "mobility_out",
    "mobility_index",
    "trends_score",
    "rss_mentions",
    "signals_score",
]


@lru_cache(maxsize=1)
def load_hybrid_model():
    """Load the unified hybrid model artifact."""
    if MODEL_PATH_FINAL.exists():
        logger.info("Loading hybrid prediction model from %s", MODEL_PATH_FINAL)
        try:
            return EcosHybridModel(MODEL_PATH_FINAL)
        except Exception as e:
            logger.error("Failed to load hybrid model: %s", e)
            return None
    return None


def _build_input_row(row: pd.Series, lag_rows: pd.DataFrame, weeks_ahead: int, adjustments: dict[str, float] | None = None) -> pd.DataFrame:
    numeric = {
        "epi_year": int(row["epi_year"]),
        "epi_week": int(row["epi_week"]) + weeks_ahead,
        "cases_lag_1": float(lag_rows["cases_total"].iloc[0]) if len(lag_rows) >= 1 else 0.0,
        "cases_lag_2": float(lag_rows["cases_total"].iloc[1]) if len(lag_rows) >= 2 else 0.0,
        "cases_lag_4": float(lag_rows["cases_total"].iloc[3]) if len(lag_rows) >= 4 else 0.0,
    }
    for col in CLIMATE_COLS + EXOG_COLS:
        val = float(row[col]) if col in row.index and pd.notna(row[col]) else 0.0
        if adjustments and col in adjustments:
            val += adjustments[col]
        numeric[col] = val
    return pd.DataFrame([numeric])


def predict_cases(municipio_code: str, disease: str, weeks_ahead: int = 2, adjustments: dict[str, float] | None = None) -> list[dict]:
    if disease not in VALID_DISEASES:
        raise ValueError(f"disease must be one of {sorted(VALID_DISEASES)}")
    if not (1 <= weeks_ahead <= 4):
        raise ValueError("weeks_ahead must be between 1 and 4")

    hybrid = load_hybrid_model()
    if hybrid is None:
        raise FileNotFoundError("Model not available. Run the training pipeline first.")

    last_row = get_last_known_features(municipio_code, disease)
    if last_row is None:
        raise FileNotFoundError(f"No historical data for municipio_code={municipio_code} disease={disease}")

    history = get_history(municipio_code, disease, limit=10)
    history = history.sort_values("week_start_date", ascending=False).reset_index(drop=True)

    predictions = []
    last_week = int(last_row["epi_week"])
    last_year = int(last_row["epi_year"])

    history_local = history.copy()
    last_row_local = last_row.copy()

    for step in range(1, weeks_ahead + 1):
        target_week = last_week + step
        target_year = last_year
        if target_week > 52:
            target_week -= 52
            target_year += 1

        X_row = _build_input_row(last_row_local, history_local, weeks_ahead=step, adjustments=adjustments)
        
        try:
            import datetime
            week_start = datetime.date.fromisocalendar(target_year, target_week, 1)
        except Exception:
            week_start = None

        # Predict residual (XGBoost) + SHAP
        residual_pred, shap_values = hybrid.predict_residual(X_row)
        
        # Get Prophet baseline
        prophet_pred = 0.0
        if week_start:
            ds = pd.Timestamp(week_start)
            prophet_pred = hybrid.get_prophet_baseline(municipio_code, disease, ds)

        predicted = max(0.0, prophet_pred + residual_pred)
        
        # Endemic channel check
        channel = calculate_endemic_channel(municipio_code, disease, target_week)
        risk_level = classify_endemic_risk(predicted, channel)
        threshold = channel.get("p90") or channel.get("p75") or OUTBREAK_THRESHOLD

        predictions.append(
            {
                "epi_year": target_year,
                "epi_week": target_week,
                "week_start_date": week_start,
                "disease": disease,
                "municipio_code": municipio_code,
                "departamento_code": str(last_row_local.get("departamento_code", "")),
                "predicted_cases": round(predicted, 2),
                "outbreak_flag": predicted >= threshold,
                "outbreak_threshold": threshold,
                "endemic_risk": risk_level,
                "shap_values": shap_values
            }
        )

        # Inject prediction for next horizon
        new_row = last_row_local.copy()
        new_row["epi_week"] = target_week
        new_row["epi_year"] = target_year
        new_row["week_start_date"] = week_start
        new_row["cases_total"] = int(round(predicted))
        
        history_local = pd.concat([pd.DataFrame([new_row]), history_local], ignore_index=True)
        last_row_local = new_row

    return predictions
