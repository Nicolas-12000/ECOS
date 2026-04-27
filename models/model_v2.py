#!/usr/bin/env python3
"""
Modelo V2 — XGBoost con features exógenas de V1 + Señales Tempranas (Trends/RSS).
Incluye walk-forward validation y generación de SHAP para entender el impacto de las señales tempranas.
"""

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from xgboost import XGBRegressor

from utils import add_lags, evaluate_metrics, load_dataset

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PARQUET_V1 = REPO_ROOT / "data/processed/curated_weekly_parquet"
DEFAULT_CSV_V1 = REPO_ROOT / "data/processed/curated_weekly_csv"
DEFAULT_SIGNALS = REPO_ROOT / "data/external/signals_weekly_v2_parquet"

DEFAULT_BASELINE_METRICS = REPO_ROOT / "models/baseline_v1_metrics.json"
DEFAULT_REPORT = REPO_ROOT / "docs/metrics-baseline-v2.md"
DEFAULT_METRICS = REPO_ROOT / "models/baseline_v2_metrics.json"
DEFAULT_MODEL = REPO_ROOT / "models/baseline_v2.joblib"

CLIMATE_COLS = ["temp_avg_c", "temp_min_c", "temp_max_c", "humidity_avg_pct", "precipitation_mm"]
EXOG_V1_COLS = ["vaccination_coverage_pct", "rips_visits_total", "mobility_index"]
SIGNALS_V2_COLS = ["trends_score", "rss_mentions_sum"]
ALL_NUMERIC = CLIMATE_COLS + EXOG_V1_COLS + SIGNALS_V2_COLS


def build_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Construye X, y para un split dado."""
    df = df.copy()
    df["week_start_date"] = pd.to_datetime(df["week_start_date"], errors="coerce")
    df = df.dropna(subset=["week_start_date", "epi_year", "epi_week", "cases_total"])

    for col in ALL_NUMERIC:
        if col not in df.columns:
            df[col] = np.nan

    df = add_lags(df)

    num_cols = ["epi_year", "epi_week", "cases_lag_1", "cases_lag_2", "cases_lag_4"] + ALL_NUMERIC
    X_num = df[num_cols].copy()
    
    # Impute missing values
    for col in ALL_NUMERIC:
        fill = X_num[col].median() if not X_num[col].isna().all() else 0.0
        # If still nan (all were nan), fallback to 0.0
        if pd.isna(fill):
            fill = 0.0
        X_num[col] = X_num[col].fillna(fill)

    X_dummies = pd.concat([
        pd.get_dummies(df["disease"], prefix="disease", dummy_na=False),
        pd.get_dummies(df["departamento_code"], prefix="dept", dummy_na=False),
    ], axis=1)

    X = pd.concat([X_num, X_dummies], axis=1)
    y = df["cases_total"].astype(float)
    return X, y


def align_columns(X_train: pd.DataFrame, X_test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fuerza la alineación de columnas (para dummies inconsistentes)."""
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
        importance = pd.DataFrame({
            "feature": X_test.columns,
            "shap_importance": np.abs(shap_values).mean(axis=0),
        }).sort_values("shap_importance", ascending=False)
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


def write_comparison_report(
    report_path: Path,
    final_metrics: dict,
    fold_metrics: list[dict],
    shap_features: list[dict],
    baseline_metrics_path: Path,
    train_rows: int,
    test_rows: int,
    n_features: int,
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)

    v1_metrics = {}
    if baseline_metrics_path.exists():
        v1_metrics = json.loads(baseline_metrics_path.read_text())

    lines = [
        "# Baseline V2 — Impacto de Señales Tempranas (Trends/RSS)",
        "",
        f"- Train rows (último fold): {train_rows}",
        f"- Test rows (último fold): {test_rows}",
        f"- Features: {n_features}",
        "",
        "## Regresión",
        f"- MAE: {final_metrics['mae']:.4f}",
        f"- RMSE: {final_metrics['rmse']:.4f}",
        f"- R2: {final_metrics['r2']:.4f}",
        "",
        "## Clasificación de brote",
        f"- Threshold: {final_metrics['threshold']:.2f}",
        f"- Precision: {final_metrics['precision']:.4f}",
        f"- Recall: {final_metrics['recall']:.4f}",
        f"- F1: {final_metrics['f1']:.4f}",
        f"- TP/FP/FN: {final_metrics['tp']}/{final_metrics['fp']}/{final_metrics['fn']}",
    ]

    if v1_metrics:
        delta_mae = final_metrics["mae"] - v1_metrics.get("mae", 0)
        delta_recall = final_metrics["recall"] - v1_metrics.get("recall", 0)
        lines += [
            "",
            "## Comparación V2 vs V1 (Dataset base)",
            f"| Métrica | V1 | V2 | Delta |",
            f"|---|---|---|---|",
            f"| MAE | {v1_metrics.get('mae', 'N/A'):.4f} | {final_metrics['mae']:.4f} | {delta_mae:+.4f} |",
            f"| RMSE | {v1_metrics.get('rmse', 'N/A'):.4f} | {final_metrics['rmse']:.4f} | {final_metrics['rmse'] - v1_metrics.get('rmse', 0):+.4f} |",
            f"| Recall | {v1_metrics.get('recall', 'N/A'):.4f} | {final_metrics['recall']:.4f} | {delta_recall:+.4f} |",
            f"| F1 | {v1_metrics.get('f1', 'N/A'):.4f} | {final_metrics['f1']:.4f} | {final_metrics['f1'] - v1_metrics.get('f1', 0):+.4f} |",
        ]

    if fold_metrics:
        lines += ["", "## Walk-Forward Validation", ""]
        lines.append("| Fold | Train end | Test end | MAE | Recall |")
        lines.append("|---|---|---|---|---|")
        for f in fold_metrics:
            lines.append(f"| {f['fold']} | {f['train_end']} | {f['test_end']} | {f['mae']:.2f} | {f['recall']:.3f} |")

    if shap_features:
        lines += ["", "## SHAP Feature Importance (Top 15)", ""]
        lines.append("Verifica el ranking de `trends_score` y `rss_mentions_sum`:")
        lines.append("")
        for item in shap_features[:15]:
            lines.append(f"- **{item['feature']}**: {item['shap_importance']:.4f}")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-parquet", default=str(DEFAULT_PARQUET_V1))
    parser.add_argument("--input-csv", default=str(DEFAULT_CSV_V1))
    parser.add_argument("--signals-parquet", default=str(DEFAULT_SIGNALS))
    parser.add_argument("--baseline-metrics", default=str(DEFAULT_BASELINE_METRICS))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--metrics", default=str(DEFAULT_METRICS))
    parser.add_argument("--model", default=str(DEFAULT_MODEL))
    parser.add_argument("--folds", type=int, default=3)
    parser.add_argument("--outbreak-threshold", type=float, default=5.0)
    args = parser.parse_args()

    # Cargar base
    df_base = load_dataset(Path(args.input_parquet), Path(args.input_csv))
    df_base["epi_year"] = df_base["epi_year"].astype(int)
    df_base["epi_week"] = df_base["epi_week"].astype(int)
    
    # Cargar señales (v2)
    signals_file = Path(args.signals_parquet)
    if not signals_file.exists():
        print(f"[error] No signals dataset found at {signals_file}. Run curate_signals_spark.py first.")
        return 1
        
    df_signals = pd.read_parquet(signals_file)
    df_signals["epi_year"] = df_signals["epi_year"].astype(int)
    df_signals["epi_week"] = df_signals["epi_week"].astype(int)
    
    # Left join by year, week, disease. Note: External signals are national, so they broadcast to all regions
    df = pd.merge(df_base, df_signals, on=["epi_year", "epi_week", "disease"], how="left")

    df["week_start_date"] = pd.to_datetime(df["week_start_date"], errors="coerce")
    df = df.dropna(subset=["week_start_date", "epi_year", "epi_week", "cases_total"])
    df = df.sort_values("week_start_date").reset_index(drop=True)

    print(f"[info] Join dataset V2: {len(df)} filas | {df['week_start_date'].min()} – {df['week_start_date'].max()}")

    splits = build_splits(df, n_folds=args.folds)
    fold_metrics = walk_forward_validation(df, splits, args.outbreak_threshold)

    cutoff = df["week_start_date"].quantile(0.8)
    train_df = df[df["week_start_date"] <= cutoff].copy()
    test_df = df[df["week_start_date"] > cutoff].copy()

    X_train, y_train = build_features(train_df)
    X_test, y_test = build_features(test_df)
    X_train, X_test = align_columns(X_train, X_test)

    print(f"[info] Entrenando modelo final V2 ({len(train_df)} train, {len(test_df)} test, {X_train.shape[1]} features)...")
    model = train_model(X_train, y_train)
    y_pred = model.predict(X_test)

    final_metrics = evaluate_metrics(y_test.to_numpy(), y_pred, args.outbreak_threshold)
    if fold_metrics:
        final_metrics["walk_forward_folds"] = fold_metrics

    shap_features = compute_shap_importance(model, X_test)
    if shap_features:
        final_metrics["top_shap_features"] = shap_features[:15]
        print("[info] Top 5 variables SHAP:")
        for item in shap_features[:5]:
            print(f"  {item['feature']}: {item['shap_importance']:.4f}")

    write_comparison_report(
        Path(args.report),
        final_metrics,
        fold_metrics,
        shap_features,
        Path(args.baseline_metrics),
        len(train_df),
        len(test_df),
        X_train.shape[1],
    )

    Path(args.metrics).parent.mkdir(parents=True, exist_ok=True)
    Path(args.metrics).write_text(json.dumps(final_metrics, indent=2), encoding="utf-8")
    Path(args.model).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, Path(args.model))

    print(f"[ok] V2 — MAE={final_metrics['mae']:.2f} Recall={final_metrics['recall']:.3f} F1={final_metrics['f1']:.3f}")
    print(f"[ok] Reporte: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
