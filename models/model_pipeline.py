"""Reusable feature engineering and validation helpers for the final ECOS model."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from xgboost import XGBRegressor

MODELS_ROOT = Path(__file__).resolve().parent
if str(MODELS_ROOT) not in sys.path:
    sys.path.insert(0, str(MODELS_ROOT))

from utils import add_lags, evaluate_metrics


CLIMATE_COLS = ["temp_avg_c", "temp_min_c", "temp_max_c", "humidity_avg_pct", "precipitation_mm"]
EXOG_COLS = [
    "vaccination_coverage_pct",
    "rips_visits_total",
    "mobility_index",
    "trends_score",
    "rss_mentions",
    "signals_score",
]


def build_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Builds X and y for a single split."""
    df = df.copy()
    df["week_start_date"] = pd.to_datetime(df["week_start_date"], errors="coerce")
    df = df.dropna(subset=["week_start_date", "epi_year", "epi_week", "cases_total"])

    for col in CLIMATE_COLS + EXOG_COLS:
        if col not in df.columns:
            df[col] = np.nan

    df = add_lags(df)

    num_cols = ["epi_year", "epi_week", "cases_lag_1", "cases_lag_2", "cases_lag_4"] + CLIMATE_COLS + EXOG_COLS
    X_num = df[num_cols].copy()
    for col in CLIMATE_COLS + EXOG_COLS:
        fill = X_num[col].median() if not X_num[col].isna().all() else 0.0
        if pd.isna(fill):
            fill = 0.0
        X_num[col] = X_num[col].fillna(fill)

    X_dummies = pd.concat(
        [
            pd.get_dummies(df["disease"], prefix="disease", dummy_na=False),
            pd.get_dummies(df["departamento_code"], prefix="dept", dummy_na=False),
        ],
        axis=1,
    )

    X = pd.concat([X_num, X_dummies], axis=1)
    y = df["cases_total"].astype(float)
    return X, y


def align_columns(X_train: pd.DataFrame, X_test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Aligns training and test columns so dummy variables stay consistent."""
    all_cols = sorted(set(X_train.columns) | set(X_test.columns))
    X_train = X_train.reindex(columns=all_cols, fill_value=0)
    X_test = X_test.reindex(columns=all_cols, fill_value=0)
    return X_train, X_test


def train_model(X_train: pd.DataFrame, y_train: pd.Series) -> XGBRegressor:
    model = XGBRegressor(
        n_estimators=500,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="reg:squarederror",
        n_jobs=4,
        random_state=42,
    )
    model.fit(X_train, y_train)
    return model


def walk_forward_validation(
    df: pd.DataFrame,
    splits: list[tuple[pd.Timestamp, pd.Timestamp]],
    threshold: float,
) -> list[dict]:
    fold_metrics = []
    for i, (train_end, test_end) in enumerate(splits):
        train_df = df[df["week_start_date"] <= train_end].copy()
        test_df = df[(df["week_start_date"] > train_end) & (df["week_start_date"] <= test_end)].copy()
        if len(train_df) < 100 or len(test_df) < 10:
            print(f"[skip] fold {i+1}: insufficient data")
            continue

        X_train, y_train = build_features(train_df)
        X_test, y_test = build_features(test_df)
        X_train, X_test = align_columns(X_train, X_test)

        model = train_model(X_train, y_train)
        y_pred = model.predict(X_test)
        m = evaluate_metrics(y_test.to_numpy(), y_pred, threshold)
        m["fold"] = i + 1
        m["train_end"] = str(train_end.date())
        m["test_end"] = str(test_end.date())
        m["train_rows"] = len(train_df)
        m["test_rows"] = len(test_df)
        fold_metrics.append(m)
        print(f"[fold {i+1}] MAE={m['mae']:.2f} RMSE={m['rmse']:.2f} recall={m['recall']:.3f}")

    return fold_metrics


def compute_shap_importance(model: XGBRegressor, X_test: pd.DataFrame) -> list[dict]:
    try:
        import shap

        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_test)
        importance = pd.DataFrame(
            {
                "feature": X_test.columns,
                "shap_importance": np.abs(shap_values).mean(axis=0),
            }
        ).sort_values("shap_importance", ascending=False)
        return importance.to_dict(orient="records")
    except ImportError:
        print("[warn] shap not installed — skipping SHAP computation")
        return []


def build_splits(df: pd.DataFrame, n_folds: int = 3) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    max_date = df["week_start_date"].max()
    min_date = df["week_start_date"].min()
    total_weeks = (max_date - min_date).days // 7
    train_weeks = int(total_weeks * 0.7)
    fold_weeks = (total_weeks - train_weeks) // n_folds

    splits = []
    for i in range(n_folds):
        train_end = min_date + pd.Timedelta(weeks=train_weeks + i * fold_weeks)
        test_end = train_end + pd.Timedelta(weeks=fold_weeks)
        if test_end > max_date:
            test_end = max_date
        splits.append((train_end, test_end))
    return splits
