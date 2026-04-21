import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error

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
            df.groupby(["municipio_code", "disease"])["cases_total"]
            .shift(lag)
            .fillna(0)
        )
    return df

def split_train_test(df: pd.DataFrame, quantile: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    cutoff = df["week_start_date"].quantile(quantile)
    train = df[df["week_start_date"] <= cutoff].copy()
    test = df[df["week_start_date"] > cutoff].copy()
    return train, test

def evaluate_metrics(y_true: np.ndarray, y_pred: np.ndarray, threshold: float) -> dict:
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
    model_name: str,
    metrics: dict,
    train_rows: int,
    test_rows: int,
    features: int,
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {model_name} - Metricas",
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
