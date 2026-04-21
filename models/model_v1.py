#!/usr/bin/env python3

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from xgboost import XGBRegressor

import shap  # New requirement for SHAP summary
from utils import add_lags, evaluate_metrics, load_dataset, split_train_test, write_report

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PARQUET = REPO_ROOT / "data/processed/curated_weekly_v1_parquet"
DEFAULT_CSV_DIR = REPO_ROOT / "data/processed/curated_weekly_v1_csv"
DEFAULT_REPORT = REPO_ROOT / "docs/metrics-baseline-v1.md"
DEFAULT_METRICS = REPO_ROOT / "models/baseline_v1_metrics.json"
DEFAULT_MODEL = REPO_ROOT / "models/baseline_v1.joblib"

# V1 adds rips_visits_total, mobility_index, vaccination_coverage_pct
CLIMATE_COLS = [
    "temp_avg_c",
    "temp_min_c",
    "temp_max_c",
    "humidity_avg_pct",
    "precipitation_mm",
]
NEW_V1_COLS = [
    "vaccination_coverage_pct",
    "rips_visits_total",
    "mobility_index",
]


def build_features_v1(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    df = df.copy()
    df["week_start_date"] = pd.to_datetime(df["week_start_date"], errors="coerce")
    df = df.dropna(subset=["week_start_date", "epi_year", "epi_week", "cases_total"])

    for col in CLIMATE_COLS + NEW_V1_COLS:
        if col not in df.columns:
            df[col] = np.nan

    df = add_lags(df)

    feature_cols = [
        "epi_year",
        "epi_week",
        "cases_lag_1",
        "cases_lag_2",
        "cases_lag_4",
    ] + CLIMATE_COLS + NEW_V1_COLS

    X = df[feature_cols].copy()
    # Impute missing values with medians
    for col in CLIMATE_COLS + NEW_V1_COLS:
        if X[col].isna().all():
            fill_value = 0.0
        else:
            fill_value = X[col].median()
        X[col] = X[col].fillna(fill_value)

    X = pd.concat(
        [
            X,
            pd.get_dummies(df["disease"], prefix="disease", dummy_na=False),
            pd.get_dummies(df["departamento_code"], prefix="dept", dummy_na=False),
        ],
        axis=1,
    )

    y = df["cases_total"].astype(float)
    return X, y


def train_model(X_train: pd.DataFrame, y_train: pd.Series) -> XGBRegressor:
    model = XGBRegressor(
        n_estimators=400,
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Baseline V1 with XGBoost & SHAP")
    parser.add_argument("--input-parquet", default=str(DEFAULT_PARQUET))
    parser.add_argument("--input-csv", default=str(DEFAULT_CSV_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--metrics", default=str(DEFAULT_METRICS))
    parser.add_argument("--model", default=str(DEFAULT_MODEL))
    parser.add_argument("--split-quantile", type=float, default=0.8)
    parser.add_argument("--outbreak-threshold", type=float, default=5.0)
    args = parser.parse_args()

    df = load_dataset(Path(args.input_parquet), Path(args.input_csv))
    df["week_start_date"] = pd.to_datetime(df["week_start_date"], errors="coerce")
    df = df.dropna(subset=["week_start_date", "epi_year", "epi_week", "cases_total"])

    train_df, test_df = split_train_test(df, args.split_quantile)

    X_train, y_train = build_features_v1(train_df)
    X_test, y_test = build_features_v1(test_df)

    print("[info] Training V1 model...")
    model = train_model(X_train, y_train)
    y_pred = model.predict(X_test)

    # SHAP explainer
    print("[info] Computing SHAP values...")
    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_test)
        
        # Calculate mean absolute SHAP value for each feature
        feature_importance = pd.DataFrame({
            "feature": X_test.columns,
            "importance": np.abs(shap_values).mean(axis=0)
        }).sort_values('importance', ascending=False)
        print("[info] Top 5 Features (SHAP):")
        print(feature_importance.head(5).to_string(index=False))
        
        # Optionally, save this to metrics if you want to output it formally
        top_features_list = feature_importance.head(10).to_dict(orient="records")
    except ImportError:
        print("[warn] module 'shap' not found. Skipping SHAP computation.")
        top_features_list = []

    metrics = evaluate_metrics(y_test.to_numpy(), y_pred, args.outbreak_threshold)
    if top_features_list:
        metrics["top_shap_features"] = top_features_list

    write_report(Path(args.report), "Baseline v1", metrics, len(train_df), len(test_df), X_train.shape[1])
    # Append SHAP analysis to report
    if top_features_list:
        with Path(args.report).open("a") as f:
            f.write("\n## SHAP Feature Importance (Top 10)\n")
            for item in top_features_list:
                f.write(f"- **{item['feature']}**: {item['importance']:.4f}\n")

    Path(args.metrics).write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    joblib.dump(model, Path(args.model))

    print(f"[ok] baseline v1 metrics saved to {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
