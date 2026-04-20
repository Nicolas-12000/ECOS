#!/usr/bin/env python3

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from xgboost import XGBRegressor

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


def load_dataset(parquet_path: Path, csv_dir: Path) -> pd.DataFrame:
    if parquet_path.exists():
        return pd.read_parquet(parquet_path)

    if csv_dir.exists():
        csv_files = sorted(csv_dir.glob("*.csv"))
        if not csv_files:
            csv_files = sorted(csv_dir.glob("*.csv.gz"))
        if not csv_files:
            raise FileNotFoundError("No CSV files found in curated CSV directory")
        return pd.concat([pd.read_csv(path) for path in csv_files], ignore_index=True)

    raise FileNotFoundError("Curated dataset not found")


def add_lags(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["municipio_code", "disease", "week_start_date"]).copy()
    for lag in (1, 2, 4):
        df[f"cases_lag_{lag}"] = (
            df.groupby(["municipio_code", "disease"])['cases_total']
            .shift(lag)
            .fillna(0)
        )
    return df


def split_train_test(df: pd.DataFrame, quantile: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    cutoff = df["week_start_date"].quantile(quantile)
    train = df[df["week_start_date"] <= cutoff].copy()
    test = df[df["week_start_date"] > cutoff].copy()
    return train, test


def build_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    df = df.copy()
    df["week_start_date"] = pd.to_datetime(df["week_start_date"], errors="coerce")
    df = df.dropna(subset=["week_start_date", "epi_year", "epi_week", "cases_total"])

    for col in CLIMATE_COLS:
        if col not in df.columns:
            df[col] = np.nan

    df = add_lags(df)

    feature_cols = [
        "epi_year",
        "epi_week",
        "cases_lag_1",
        "cases_lag_2",
        "cases_lag_4",
    ] + CLIMATE_COLS

    X = df[feature_cols].copy()
    for col in CLIMATE_COLS:
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
        n_estimators=300,
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


def evaluate(y_true: np.ndarray, y_pred: np.ndarray, threshold: float) -> dict:
    mae = mean_absolute_error(y_true, y_pred)
    rmse = root_mean_squared_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)

    actual_outbreak = y_true >= threshold
    pred_outbreak = y_pred >= threshold

    tp = int((actual_outbreak & pred_outbreak).sum())
    fp = int((~actual_outbreak & pred_outbreak).sum())
    fn = int((actual_outbreak & ~pred_outbreak).sum())

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "r2": float(r2),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "threshold": float(threshold),
        "tp": tp,
        "fp": fp,
        "fn": fn,
    }


def write_report(
    report_path: Path,
    metrics: dict,
    train_rows: int,
    test_rows: int,
    features: int,
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Baseline v0 - Metricas",
        "",
        f"- Train rows: {train_rows}",
        f"- Test rows: {test_rows}",
        f"- Features: {features}",
        "",
        "## Regresion",
        f"- MAE: {metrics['mae']:.4f}",
        f"- RMSE: {metrics['rmse']:.4f}",
        f"- R2: {metrics['r2']:.4f}",
        "",
        "## Clasificacion de brote",
        f"- Threshold casos: {metrics['threshold']:.2f}",
        f"- Precision: {metrics['precision']:.4f}",
        f"- Recall: {metrics['recall']:.4f}",
        f"- F1: {metrics['f1']:.4f}",
        f"- TP/FP/FN: {metrics['tp']}/{metrics['fp']}/{metrics['fn']}",
    ]

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


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

    metrics = evaluate(y_test.to_numpy(), y_pred, args.outbreak_threshold)

    write_report(Path(args.report), metrics, len(train_df), len(test_df), X_train.shape[1])
    Path(args.metrics).write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    joblib.dump(model, Path(args.model))

    print(f"[ok] baseline metrics saved to {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
