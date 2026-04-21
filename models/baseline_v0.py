#!/usr/bin/env python3

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from utils import add_lags, evaluate_metrics, load_dataset, split_train_test, write_report

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PARQUET = REPO_ROOT / "data/processed/curated_weekly_v0_parquet"
DEFAULT_CSV_DIR = REPO_ROOT / "data/processed/curated_weekly_v0_csv"
DEFAULT_REPORT = REPO_ROOT / "docs/metrics-baseline-v0.md"
DEFAULT_METRICS = REPO_ROOT / "models/baseline_v0_metrics.json"
DEFAULT_MODEL = REPO_ROOT / "models/baseline_v0.joblib"

CLIMATE_COLS = [
    "temp_avg_c",
    "temp_min_c",
    "temp_max_c",
    "humidity_avg_pct",
    "precipitation_mm",
]


def build_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    df = df.copy()
    df["week_start_date"] = pd.to_datetime(df["week_start_date"], errors="coerce")
    df = df.dropna(subset=["week_start_date", "epi_year", "epi_week", "cases_total"])
    for col in CLIMATE_COLS:
        if col not in df.columns:
            df[col] = np.nan
    df = add_lags(df)
    feature_cols = ["epi_year", "epi_week", "cases_lag_1", "cases_lag_2", "cases_lag_4"] + CLIMATE_COLS
    X = df[feature_cols].copy()
    for col in CLIMATE_COLS:
        X[col] = X[col].fillna(X[col].median() if not X[col].isna().all() else 0.0)
    X = pd.concat([
        X,
        pd.get_dummies(df["disease"], prefix="disease", dummy_na=False),
        pd.get_dummies(df["departamento_code"], prefix="dept", dummy_na=False),
    ], axis=1)
    return X, df["cases_total"].astype(float)


def train_model(X_train: pd.DataFrame, y_train: pd.Series) -> XGBRegressor:
    model = XGBRegressor(
        n_estimators=300, max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, objective="reg:squarederror",
        n_jobs=4, random_state=42,
    )
    model.fit(X_train, y_train)
    return model



def main() -> int:
    parser = argparse.ArgumentParser(description="Baseline v0 with XGBoost")
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

    X_train, y_train = build_features(train_df)
    X_test, y_test = build_features(test_df)

    model = train_model(X_train, y_train)
    y_pred = model.predict(X_test)

    metrics = evaluate_metrics(y_test.to_numpy(), y_pred, args.outbreak_threshold)

    write_report(Path(args.report), "Baseline v0", metrics, len(train_df), len(test_df), X_train.shape[1])
    Path(args.metrics).write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    joblib.dump(model, Path(args.model))

    print(f"[ok] baseline metrics saved to {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
