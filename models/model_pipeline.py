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


CLIMATE_COLS = [
    "temp_avg_c",
    "temp_min_c",
    "temp_max_c",
    "precipitation_mm",
    "temp_avg_c_actual",
    "temp_min_c_actual",
    "temp_max_c_actual",
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


def build_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Builds X and y for a single split using cases_total as target."""
    return build_features_with_target(df, target_col="cases_total")


def build_features_with_target(df: pd.DataFrame, target_col: str) -> tuple[pd.DataFrame, pd.Series]:
    """Builds X and y for a single split using a custom target column."""
    df = df.copy()
    df["week_start_date"] = pd.to_datetime(df["week_start_date"], errors="coerce")
    df = df.dropna(subset=["week_start_date", "epi_year", "epi_week", target_col])

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
    y = df[target_col].astype(float)
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


def fit_prophet_series(df_series: pd.DataFrame):
    from prophet import Prophet
    from prophet.make_holidays import make_holidays_df

    # Add Colombian holidays
    colombia_holidays = make_holidays_df(year_list=df_series['ds'].dt.year.unique(), country='CO')
    
    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        holidays=colombia_holidays,
        interval_width=0.9,
    )
    model.fit(df_series)
    return model


def build_prophet_models(df: pd.DataFrame, min_weeks: int, max_series: int) -> dict:
    prophet_models: dict[str, object] = {}
    groups = (
        df.groupby(["municipio_code", "disease"], dropna=True)
        .size()
        .sort_values(ascending=False)
    )

    for (municipio_code, disease), count in groups.items():
        if count < min_weeks:
            continue
        key = f"{municipio_code}:{disease}"
        if len(prophet_models) >= max_series:
            break

        subset = df[(df["municipio_code"] == municipio_code) & (df["disease"] == disease)].copy()
        subset = subset.sort_values("week_start_date")
        series = subset[["week_start_date", "cases_total"]].rename(
            columns={"week_start_date": "ds", "cases_total": "y"}
        )
        try:
            prophet_models[key] = fit_prophet_series(series)
        except Exception:
            continue

    return prophet_models


def apply_prophet_residuals(df: pd.DataFrame, prophet_models: dict) -> pd.DataFrame:
    df = df.copy()
    df["prophet_yhat"] = pd.NA

    for key, model in prophet_models.items():
        municipio_code, disease = key.split(":", 1)
        subset_idx = df.index[(df["municipio_code"] == municipio_code) & (df["disease"] == disease)]
        if subset_idx.empty:
            continue
        subset = df.loc[subset_idx].sort_values("week_start_date")
        frame = subset[["week_start_date"]].rename(columns={"week_start_date": "ds"})
        try:
            forecast = model.predict(frame)
        except Exception:
            continue
        df.loc[subset_idx, "prophet_yhat"] = forecast["yhat"].to_numpy()

    df["prophet_yhat"] = pd.to_numeric(df["prophet_yhat"], errors="coerce")
    df["residual"] = df["cases_total"] - df["prophet_yhat"].fillna(0)
    return df


def walk_forward_validation(
    df: pd.DataFrame,
    splits: list[tuple[pd.Timestamp, pd.Timestamp]],
    threshold: float,
    use_prophet: bool = False,
    prophet_min_weeks: int = 104,
    prophet_max_series: int = 2000,
) -> list[dict]:
    fold_metrics = []
    for i, (train_end, test_end) in enumerate(splits):
        train_df = df[df["week_start_date"] <= train_end].copy()
        test_df = df[(df["week_start_date"] > train_end) & (df["week_start_date"] <= test_end)].copy()
        if len(train_df) < 100 or len(test_df) < 10:
            print(f"[skip] fold {i+1}: insufficient data")
            continue

        if use_prophet:
            try:
                # Entrenar Prophet SOLO con train_df
                prophet_models = build_prophet_models(train_df, prophet_min_weeks, prophet_max_series)
                # Calcular residuos para train_df y test_df
                train_df_feat = apply_prophet_residuals(train_df, prophet_models)
                test_df_feat = apply_prophet_residuals(test_df, prophet_models)
                
                X_train, y_train = build_features_with_target(train_df_feat, target_col="residual")
                X_test, y_test = build_features_with_target(test_df_feat, target_col="residual")
            except Exception as e:
                print(f"[warn] fold {i+1}: Fallo al construir/aplicar Prophet ({e}). Usando cases_total.")
                X_train, y_train = build_features(train_df)
                X_test, y_test = build_features(test_df)
                use_prophet = False
        else:
            X_train, y_train = build_features(train_df)
            X_test, y_test = build_features(test_df)

        X_train, X_test = align_columns(X_train, X_test)
        model = train_model(X_train, y_train)
        y_pred = model.predict(X_test)
        if use_prophet:
            prophet_yhat_test = test_df_feat["prophet_yhat"].fillna(0).to_numpy()
            y_pred_total = np.clip(prophet_yhat_test + y_pred, 0, None)
            y_true_total = test_df_feat["cases_total"].to_numpy()
            m = evaluate_metrics(y_true_total, y_pred_total, threshold)
        else:
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
