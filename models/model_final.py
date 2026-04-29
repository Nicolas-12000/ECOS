#!/usr/bin/env python3
"""
Modelo final — XGBoost con variables exógenas y señales tempranas.
Consolida el entrenamiento operativo del proyecto y genera artefactos finales.
"""

import argparse
import json
import sys
from pathlib import Path

import joblib
import pandas as pd

MODELS_ROOT = Path(__file__).resolve().parent
if str(MODELS_ROOT) not in sys.path:
    sys.path.insert(0, str(MODELS_ROOT))

from model_pipeline import (
    align_columns,
    build_features,
    build_splits,
    compute_shap_importance,
    train_model,
    walk_forward_validation,
)
from utils import evaluate_metrics, load_dataset

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PARQUET = REPO_ROOT / "data/processed/curated_weekly_parquet"
DEFAULT_CSV_DIR = REPO_ROOT / "data/processed/curated_weekly_csv"
DEFAULT_SIGNALS_PRIMARY = REPO_ROOT / "data/external/signals_weekly_parquet"
DEFAULT_SIGNALS_FALLBACK = REPO_ROOT / "data/external/signals_weekly_legacy_parquet"

DEFAULT_BASELINE_METRICS = REPO_ROOT / "models/baseline_v0_metrics.json"
DEFAULT_REPORT = REPO_ROOT / "docs/metrics-final.md"
DEFAULT_METRICS = REPO_ROOT / "models/final_model_metrics.json"
DEFAULT_MODEL = REPO_ROOT / "models/final_model.joblib"


def _load_signals() -> pd.DataFrame:
    for path in [DEFAULT_SIGNALS_PRIMARY, DEFAULT_SIGNALS_FALLBACK]:
        if path.exists():
            return pd.read_parquet(path)
    raise FileNotFoundError("Signals dataset not found. Run the signals curation pipeline first.")


def _write_final_report(
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

    baseline_metrics = {}
    if baseline_metrics_path.exists():
        baseline_metrics = json.loads(baseline_metrics_path.read_text())

    lines = [
        "# Modelo final — Métricas y comparación",
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

    if baseline_metrics:
        lines += [
            "",
            "## Comparación contra baseline",
            "| Métrica | Baseline | Final | Delta |",
            "|---|---|---|---|",
            f"| MAE | {baseline_metrics.get('mae', 'N/A'):.4f} | {final_metrics['mae']:.4f} | {final_metrics['mae'] - baseline_metrics.get('mae', 0):+.4f} |",
            f"| RMSE | {baseline_metrics.get('rmse', 'N/A'):.4f} | {final_metrics['rmse']:.4f} | {final_metrics['rmse'] - baseline_metrics.get('rmse', 0):+.4f} |",
            f"| Recall | {baseline_metrics.get('recall', 'N/A'):.4f} | {final_metrics['recall']:.4f} | {final_metrics['recall'] - baseline_metrics.get('recall', 0):+.4f} |",
            f"| F1 | {baseline_metrics.get('f1', 'N/A'):.4f} | {final_metrics['f1']:.4f} | {final_metrics['f1'] - baseline_metrics.get('f1', 0):+.4f} |",
        ]

    if fold_metrics:
        lines += ["", "## Walk-forward validation", "", "| Fold | Train end | Test end | MAE | Recall |", "|---|---|---|---|---|"]
        for fold in fold_metrics:
            lines.append(f"| {fold['fold']} | {fold['train_end']} | {fold['test_end']} | {fold['mae']:.2f} | {fold['recall']:.3f} |")

    if shap_features:
        lines += ["", "## SHAP Feature Importance (Top 10)", ""]
        for item in shap_features[:10]:
            lines.append(f"- **{item['feature']}**: {item['shap_importance']:.4f}")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Modelo final: XGBoost + exógenas + señales + SHAP")
    parser.add_argument("--input-parquet", default=str(DEFAULT_PARQUET))
    parser.add_argument("--input-csv", default=str(DEFAULT_CSV_DIR))
    parser.add_argument("--baseline-metrics", default=str(DEFAULT_BASELINE_METRICS))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--metrics", default=str(DEFAULT_METRICS))
    parser.add_argument("--model", default=str(DEFAULT_MODEL))
    parser.add_argument("--folds", type=int, default=3)
    parser.add_argument("--outbreak-threshold", type=float, default=5.0)
    args = parser.parse_args()

    df_base = load_dataset(Path(args.input_parquet), Path(args.input_csv))
    df_base["week_start_date"] = pd.to_datetime(df_base["week_start_date"], errors="coerce")
    df_base = df_base.dropna(subset=["week_start_date", "epi_year", "epi_week", "cases_total"])

    if {"trends_score", "rss_mentions", "signals_score"}.issubset(df_base.columns):
        df = df_base.copy()
    else:
        try:
            signals = _load_signals()
            signals["week_start_date"] = pd.to_datetime(signals["week_start_date"], errors="coerce")
            if {"epi_year", "epi_week", "disease"}.issubset(signals.columns):
                df = pd.merge(df_base, signals, on=["epi_year", "epi_week", "disease"], how="left")
            else:
                df = df_base.copy()
        except FileNotFoundError:
            df = df_base.copy()

    df = df.sort_values("week_start_date").reset_index(drop=True)

    print(f"[info] Dataset final: {len(df)} filas | {df['week_start_date'].min()} – {df['week_start_date'].max()}")

    splits = build_splits(df, n_folds=args.folds)
    fold_metrics = walk_forward_validation(df, splits, args.outbreak_threshold)

    cutoff = df["week_start_date"].quantile(0.8)
    train_df = df[df["week_start_date"] <= cutoff].copy()
    test_df = df[df["week_start_date"] > cutoff].copy()

    X_train, y_train = build_features(train_df)
    X_test, y_test = build_features(test_df)
    X_train, X_test = align_columns(X_train, X_test)

    print(f"[info] Entrenando modelo final ({len(train_df)} train, {len(test_df)} test, {X_train.shape[1]} features)...")
    model = train_model(X_train, y_train)
    y_pred = model.predict(X_test)

    final_metrics = evaluate_metrics(y_test.to_numpy(), y_pred, args.outbreak_threshold)
    if fold_metrics:
        final_metrics["walk_forward_folds"] = fold_metrics

    shap_features = compute_shap_importance(model, X_test)
    if shap_features:
        final_metrics["top_shap_features"] = shap_features[:10]

    _write_final_report(
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

    print(f"[ok] Final — MAE={final_metrics['mae']:.2f} Recall={final_metrics['recall']:.3f} F1={final_metrics['f1']:.3f}")
    print(f"[ok] Reporte: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
