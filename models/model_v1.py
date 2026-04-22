#!/usr/bin/env python3
"""
Modelo V1 — XGBoost con features exógenas (clima, vacunación, RIPS, movilidad).
Walk-forward validation para evitar data leakage temporal.
SHAP para explicabilidad por variable clave y comprobación de estabilidad entre folds.
Genera reporte comparativo vs baseline v0.
"""

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from xgboost import XGBRegressor

from utils import add_lags, evaluate_metrics, load_dataset, write_report

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PARQUET = REPO_ROOT / "data/processed/curated_weekly_v1_parquet"
DEFAULT_CSV_DIR = REPO_ROOT / "data/processed/curated_weekly_v1_csv"
DEFAULT_BASELINE_METRICS = REPO_ROOT / "models/baseline_v0_metrics.json"
DEFAULT_REPORT = REPO_ROOT / "docs/metrics-baseline-v1.md"
DEFAULT_METRICS = REPO_ROOT / "models/baseline_v1_metrics.json"
DEFAULT_MODEL = REPO_ROOT / "models/baseline_v1.joblib"

CLIMATE_COLS = ["temp_avg_c", "temp_min_c", "temp_max_c", "humidity_avg_pct", "precipitation_mm"]
EXOG_V1_COLS = ["vaccination_coverage_pct", "rips_visits_total", "mobility_index"]
ALL_NUMERIC = CLIMATE_COLS + EXOG_V1_COLS


def build_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """
    Construye X, y para un split dado.
    - Lags: 1, 2, 4 semanas.
    - Variables exógenas V1: clima + vacunación + RIPS + movilidad.
    - Dummies: disease + departamento_code.
    Nota: las columnas dummy se alinean en el caller para consistencia entre folds.
    """
    df = df.copy()
    df["week_start_date"] = pd.to_datetime(df["week_start_date"], errors="coerce")
    df = df.dropna(subset=["week_start_date", "epi_year", "epi_week", "cases_total"])

    for col in ALL_NUMERIC:
        if col not in df.columns:
            df[col] = np.nan

    df = add_lags(df)

    num_cols = ["epi_year", "epi_week", "cases_lag_1", "cases_lag_2", "cases_lag_4"] + ALL_NUMERIC
    X_num = df[num_cols].copy()
    for col in ALL_NUMERIC:
        fill = X_num[col].median() if not X_num[col].isna().all() else 0.0
        X_num[col] = X_num[col].fillna(fill)

    X_dummies = pd.concat([
        pd.get_dummies(df["disease"], prefix="disease", dummy_na=False),
        pd.get_dummies(df["departamento_code"], prefix="dept", dummy_na=False),
    ], axis=1)

    X = pd.concat([X_num, X_dummies], axis=1)
    y = df["cases_total"].astype(float)
    return X, y


def align_columns(X_train: pd.DataFrame, X_test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Fuerza que train y test tengan exactamente las mismas columnas dummy.
    El test puede no tener todos los departamentos o enfermedades del train.
    """
    all_cols = sorted(set(X_train.columns) | set(X_test.columns))
    X_train = X_train.reindex(columns=all_cols, fill_value=0)
    X_test = X_test.reindex(columns=all_cols, fill_value=0)
    return X_train, X_test


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


def walk_forward_validation(
    df: pd.DataFrame,
    splits: list[tuple[pd.Timestamp, pd.Timestamp]],
    threshold: float,
) -> list[dict]:
    """
    Walk-forward: para cada fold (train_end, test_end),
    entrena en [inicio, train_end] y evalúa en (train_end, test_end].
    Retorna métricas por fold para analizar estabilidad temporal.
    """
    fold_metrics = []
    for i, (train_end, test_end) in enumerate(splits):
        train_df = df[df["week_start_date"] <= train_end].copy()
        test_df = df[(df["week_start_date"] > train_end) & (df["week_start_date"] <= test_end)].copy()
        if len(train_df) < 100 or len(test_df) < 10:
            print(f"[skip] fold {i+1}: insufficient data (train={len(train_df)}, test={len(test_df)})")
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
    """Computa SHAP mean absolute values. Retorna lista ordenada por importancia."""
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
    """
    Genera splits temporales walk-forward:
    Usa los últimos n_folds * 6 meses como área de test, avanzando 6 meses por fold.
    """
    max_date = df["week_start_date"].max()
    min_date = df["week_start_date"].min()
    total_weeks = (max_date - min_date).days // 7
    # Reserve at least 70% for first train
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

    # Load v0 baseline for comparison
    v0_metrics = {}
    if baseline_metrics_path.exists():
        v0_metrics = json.loads(baseline_metrics_path.read_text())

    lines = [
        "# Baseline V1 — Métricas y Comparación",
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
        f"- Recall: {final_metrics['recall']:.4f}   ← métrica prioritaria en salud pública",
        f"- F1: {final_metrics['f1']:.4f}",
        f"- TP/FP/FN: {final_metrics['tp']}/{final_metrics['fp']}/{final_metrics['fn']}",
    ]

    if v0_metrics:
        delta_mae = final_metrics["mae"] - v0_metrics.get("mae", 0)
        delta_recall = final_metrics["recall"] - v0_metrics.get("recall", 0)
        lines += [
            "",
            "## Comparación vs Baseline V0",
            f"| Métrica | V0 | V1 | Delta |",
            f"|---|---|---|---|",
            f"| MAE | {v0_metrics.get('mae', 'N/A'):.4f} | {final_metrics['mae']:.4f} | {delta_mae:+.4f} |",
            f"| RMSE | {v0_metrics.get('rmse', 'N/A'):.4f} | {final_metrics['rmse']:.4f} | {final_metrics['rmse'] - v0_metrics.get('rmse', 0):+.4f} |",
            f"| Recall | {v0_metrics.get('recall', 'N/A'):.4f} | {final_metrics['recall']:.4f} | {delta_recall:+.4f} |",
            f"| F1 | {v0_metrics.get('f1', 'N/A'):.4f} | {final_metrics['f1']:.4f} | {final_metrics['f1'] - v0_metrics.get('f1', 0):+.4f} |",
        ]

    if fold_metrics:
        lines += ["", "## Walk-Forward Validation (Estabilidad Temporal)", ""]
        lines.append("| Fold | Train end | Test end | MAE | Recall |")
        lines.append("|---|---|---|---|---|")
        for f in fold_metrics:
            lines.append(f"| {f['fold']} | {f['train_end']} | {f['test_end']} | {f['mae']:.2f} | {f['recall']:.3f} |")

    if shap_features:
        lines += ["", "## SHAP Feature Importance (Top 10)", ""]
        for item in shap_features[:10]:
            lines.append(f"- **{item['feature']}**: {item['shap_importance']:.4f}")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Model V1: XGBoost + exógenas + SHAP + walk-forward")
    parser.add_argument("--input-parquet", default=str(DEFAULT_PARQUET))
    parser.add_argument("--input-csv", default=str(DEFAULT_CSV_DIR))
    parser.add_argument("--baseline-metrics", default=str(DEFAULT_BASELINE_METRICS))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--metrics", default=str(DEFAULT_METRICS))
    parser.add_argument("--model", default=str(DEFAULT_MODEL))
    parser.add_argument("--folds", type=int, default=3)
    parser.add_argument("--outbreak-threshold", type=float, default=5.0)
    args = parser.parse_args()

    df = load_dataset(Path(args.input_parquet), Path(args.input_csv))
    df["week_start_date"] = pd.to_datetime(df["week_start_date"], errors="coerce")
    df = df.dropna(subset=["week_start_date", "epi_year", "epi_week", "cases_total"])
    df = df.sort_values("week_start_date").reset_index(drop=True)

    print(f"[info] Dataset: {len(df)} filas | {df['week_start_date'].min()} – {df['week_start_date'].max()}")

    # Walk-forward validation (estabilidad temporal)
    splits = build_splits(df, n_folds=args.folds)
    fold_metrics = walk_forward_validation(df, splits, args.outbreak_threshold)

    # Modelo final: entrena en 80% más reciente, evalúa en 20% más reciente
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

    # SHAP sobre el test set del modelo final
    shap_features = compute_shap_importance(model, X_test)
    if shap_features:
        final_metrics["top_shap_features"] = shap_features[:10]
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

    print(f"[ok] V1 — MAE={final_metrics['mae']:.2f} Recall={final_metrics['recall']:.3f}")
    print(f"[ok] Reporte: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
