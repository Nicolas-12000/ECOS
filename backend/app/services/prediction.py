import logging
from pathlib import Path

import joblib
import pandas as pd

from app.services.epidemiology import OUTBREAK_THRESHOLD, VALID_DISEASES, get_history, get_last_known_features

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH_FINAL = REPO_ROOT / "models/final_model.joblib"
MODEL_PATH_FALLBACKS = [
    REPO_ROOT / "models/baseline_v2.joblib",
    REPO_ROOT / "models/baseline_v0.joblib",
]

CLIMATE_COLS = ["temp_avg_c", "temp_min_c", "temp_max_c", "humidity_avg_pct", "precipitation_mm"]
EXOG_COLS = [
    "vaccination_coverage_pct",
    "rips_visits_total",
    "mobility_index",
    "trends_score",
    "rss_mentions",
    "signals_score",
]


def load_model():
    """Load the final prediction model with a narrow fallback chain."""
    candidates = [MODEL_PATH_FINAL, *MODEL_PATH_FALLBACKS]
    for path in candidates:
        if path.exists():
            logger.info("Loading prediction model from %s", path)
            return joblib.load(path)
    return None


def _build_input_row(row: pd.Series, lag_rows: pd.DataFrame, weeks_ahead: int) -> pd.DataFrame:
    numeric = {
        "epi_year": int(row["epi_year"]),
        "epi_week": int(row["epi_week"]) + weeks_ahead,
        "cases_lag_1": float(lag_rows["cases_total"].iloc[0]) if len(lag_rows) >= 1 else 0.0,
        "cases_lag_2": float(lag_rows["cases_total"].iloc[1]) if len(lag_rows) >= 2 else 0.0,
        "cases_lag_4": float(lag_rows["cases_total"].iloc[3]) if len(lag_rows) >= 4 else 0.0,
    }
    for col in CLIMATE_COLS + EXOG_COLS:
        numeric[col] = float(row[col]) if col in row.index and pd.notna(row[col]) else 0.0
    return pd.DataFrame([numeric])


def predict_cases(municipio_code: str, disease: str, weeks_ahead: int = 2) -> list[dict]:
    if disease not in VALID_DISEASES:
        raise ValueError(f"disease must be one of {sorted(VALID_DISEASES)}")
    if not (1 <= weeks_ahead <= 4):
        raise ValueError("weeks_ahead must be between 1 and 4")

    model = load_model()
    if model is None:
        raise FileNotFoundError("Model not available. Run the training pipeline first.")

    last_row = get_last_known_features(municipio_code, disease)
    if last_row is None:
        raise FileNotFoundError(f"No historical data for municipio_code={municipio_code} disease={disease}")

    history = get_history(municipio_code, disease, limit=10)
    history = history.sort_values("week_start_date", ascending=False).reset_index(drop=True)

    predictions = []
    last_week = int(last_row["epi_week"])
    last_year = int(last_row["epi_year"])

    # Recursive forecasting: predict t+1, then inject prediction as lag for t+2, etc.
    # We maintain a local copy of `history` and `last_row` to simulate future observations.
    history_local = history.copy()
    last_row_local = last_row.copy()

    for step in range(1, weeks_ahead + 1):
        target_week = last_week + step
        target_year = last_year
        if target_week > 52:
            target_week -= 52
            target_year += 1

        X_row = _build_input_row(last_row_local, history_local, weeks_ahead=step)
        try:
            expected_cols = model.get_booster().feature_names
            X_aligned = X_row.reindex(columns=expected_cols, fill_value=0)
        except Exception:
            X_aligned = X_row

        predicted = max(0.0, float(model.predict(X_aligned)[0]))

        try:
            import datetime

            week_start = datetime.date.fromisocalendar(target_year, target_week, 1)
        except Exception:
            week_start = None

        predictions.append(
            {
                "epi_year": target_year,
                "epi_week": target_week,
                "week_start_date": week_start,
                "disease": disease,
                "municipio_code": municipio_code,
                "departamento_code": str(last_row_local.get("departamento_code", "")),
                "predicted_cases": round(predicted, 2),
                "outbreak_flag": predicted >= OUTBREAK_THRESHOLD,
                "outbreak_threshold": OUTBREAK_THRESHOLD,
            }
        )

        # Inject prediction as the newest known point so next horizon uses updated lags
        new_row = last_row_local.copy()
        new_row = new_row.copy()
        # set week/year and cases_total to the predicted value
        new_row["epi_week"] = target_week
        new_row["epi_year"] = target_year
        new_row["week_start_date"] = week_start
        new_row["cases_total"] = int(round(predicted))
        # prepend to history_local
        history_local = pd.concat([pd.DataFrame([new_row]), history_local], ignore_index=True)
        # update last_row_local for next iteration
        last_row_local = new_row

    return predictions
