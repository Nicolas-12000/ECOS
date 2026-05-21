#!/usr/bin/env python3
"""Generate synthetic demo data so the backend can run without the full Spark pipeline.

Creates:
  - data/processed/curated_weekly_csv/  (CSV files)
  - models/final_model.joblib           (trained XGBoost model)

Usage:
    python scripts/generate_demo_data.py
"""

import datetime as dt
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from xgboost import XGBRegressor

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_CSV = REPO_ROOT / "data" / "processed" / "curated_weekly_csv"
MODEL_OUT = REPO_ROOT / "models" / "final_model.joblib"

# ── Representative municipalities (code, depto_code, name) ─────────────────
MUNICIPIOS = [
    ("05001", "05", "Medellín"),
    ("08001", "08", "Barranquilla"),
    ("11001", "11", "Bogotá"),
    ("13001", "13", "Cartagena"),
    ("15001", "15", "Tunja"),
    ("17001", "17", "Manizales"),
    ("19001", "19", "Popayán"),
    ("20001", "20", "Valledupar"),
    ("23001", "23", "Montería"),
    ("25001", "25", "Agua de Dios"),
    ("27001", "27", "Quibdó"),
    ("41001", "41", "Neiva"),
    ("44001", "44", "Riohacha"),
    ("47001", "47", "Santa Marta"),
    ("50001", "50", "Villavicencio"),
    ("52001", "52", "Pasto"),
    ("54001", "54", "Cúcuta"),
    ("63001", "63", "Armenia"),
    ("66001", "66", "Pereira"),
    ("68001", "68", "Bucaramanga"),
    ("73001", "73", "Ibagué"),
    ("76001", "76", "Cali"),
    ("91001", "91", "Leticia"),
    ("99001", "99", "Puerto Carreño"),
]

DISEASES = ["dengue", "chikungunya", "zika", "malaria"]

# Seasonality parameters per disease (peak weeks, base cases)
DISEASE_PARAMS = {
    "dengue":       {"base": 3.0, "amplitude": 12.0, "peak_week": 16, "noise": 2.5},
    "chikungunya":  {"base": 0.8, "amplitude": 4.0,  "peak_week": 20, "noise": 1.0},
    "zika":         {"base": 0.3, "amplitude": 2.0,  "peak_week": 18, "noise": 0.5},
    "malaria":      {"base": 1.5, "amplitude": 6.0,  "peak_week": 40, "noise": 1.5},
}

# Regional risk multiplier (higher in Caribe/Pacífico)
REGION_RISK = {
    "05": 1.2, "08": 1.8, "11": 0.7, "13": 1.6, "15": 0.4,
    "17": 0.6, "19": 1.0, "20": 1.7, "23": 1.5, "25": 0.5,
    "27": 2.0, "41": 1.3, "44": 1.9, "47": 1.7, "50": 1.1,
    "52": 0.9, "54": 1.0, "63": 0.7, "66": 0.8, "68": 0.9,
    "73": 1.1, "76": 1.4, "91": 1.8, "99": 1.5,
}


def _seasonal_cases(week: int, params: dict, risk: float, rng: np.random.Generator) -> float:
    """Generate seasonal case count with sinusoidal pattern."""
    phase = 2 * np.pi * (week - params["peak_week"]) / 52
    seasonal = params["base"] + params["amplitude"] * max(0, np.cos(phase))
    noise = rng.normal(0, params["noise"])
    return max(0.0, (seasonal + noise) * risk)


def generate_curated_data(start_year: int = 2018, end_year: int = 2024) -> pd.DataFrame:
    """Generate a synthetic curated weekly dataset."""
    rng = np.random.default_rng(42)
    rows = []

    start = dt.date.fromisocalendar(start_year, 1, 1)
    end = dt.date.fromisocalendar(end_year, 52, 1)
    current = start

    while current <= end:
        iso_year, iso_week, _ = current.isocalendar()
        for mun_code, dept_code, _ in MUNICIPIOS:
            risk = REGION_RISK.get(dept_code, 1.0)
            for disease in DISEASES:
                params = DISEASE_PARAMS[disease]
                cases = _seasonal_cases(iso_week, params, risk, rng)

                # Climate (tropical baseline with seasonal variation)
                temp_avg = 24 + 4 * np.sin(2 * np.pi * iso_week / 52) + rng.normal(0, 1)
                temp_min = temp_avg - 4 - rng.exponential(1)
                temp_max = temp_avg + 5 + rng.exponential(1)
                humidity = 70 + 10 * np.cos(2 * np.pi * (iso_week - 10) / 52) + rng.normal(0, 3)
                precip = max(0, 80 + 60 * np.cos(2 * np.pi * (iso_week - 15) / 52) + rng.normal(0, 20))

                # Exogenous signals
                vacc_cov = min(100, max(0, 75 + rng.normal(0, 10)))
                rips = max(0, int(cases * 1.3 + rng.normal(0, 2)))
                mobility = max(0, 50 + rng.normal(0, 15))
                trends = max(0, cases * 0.8 + rng.normal(0, 1))
                rss_ment = max(0, int(rng.poisson(max(0, cases * 0.3))))
                sig_score = min(1.0, max(0, (trends * 0.6 + rss_ment * 0.4) / 10))

                rows.append({
                    "municipio_code": mun_code,
                    "departamento_code": dept_code,
                    "disease": disease,
                    "epi_year": iso_year,
                    "epi_week": iso_week,
                    "week_start_date": current.isoformat(),
                    "cases_total": int(round(cases)),
                    "temp_avg_c": round(temp_avg, 1),
                    "temp_min_c": round(temp_min, 1),
                    "temp_max_c": round(temp_max, 1),
                    "humidity_avg_pct": round(humidity, 1),
                    "precipitation_mm": round(precip, 1),
                    "vaccination_coverage_pct": round(vacc_cov, 1),
                    "rips_visits_total": rips,
                    "mobility_index": round(mobility, 1),
                    "trends_score": round(trends, 2),
                    "rss_mentions": rss_ment,
                    "signals_score": round(sig_score, 3),
                })
        current += dt.timedelta(weeks=1)

    return pd.DataFrame(rows)


def train_demo_model(df: pd.DataFrame) -> None:
    """Train a lightweight XGBoost model on the demo data."""
    sys.path.insert(0, str(REPO_ROOT / "models"))
    from model_pipeline import align_columns, build_features

    df["week_start_date"] = pd.to_datetime(df["week_start_date"])
    df = df.sort_values("week_start_date").reset_index(drop=True)

    cutoff = df["week_start_date"].quantile(0.8)
    train_df = df[df["week_start_date"] <= cutoff]
    test_df = df[df["week_start_date"] > cutoff]

    X_train, y_train = build_features(train_df)
    X_test, _ = build_features(test_df)
    X_train, X_test = align_columns(X_train, X_test)

    model = XGBRegressor(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.08,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="reg:squarederror",
        n_jobs=4,
        random_state=42,
    )
    model.fit(X_train, y_train)

    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_OUT)
    print(f"[ok] Model saved → {MODEL_OUT} ({X_train.shape[1]} features)")


def main() -> int:
    print("[info] Generating demo curated data...")
    df = generate_curated_data()
    print(f"[info] Generated {len(df)} rows ({df['disease'].nunique()} diseases, "
          f"{df['municipio_code'].nunique()} municipalities, "
          f"{df['epi_year'].nunique()} years)")

    # Save CSV
    OUTPUT_CSV.mkdir(parents=True, exist_ok=True)
    csv_path = OUTPUT_CSV / "curated_demo.csv"
    df.to_csv(csv_path, index=False)
    print(f"[ok] CSV saved → {csv_path}")

    # Train model
    print("[info] Training demo XGBoost model...")
    train_demo_model(df)

    print("\n✅ Demo data ready! Start the backend with:")
    print("   cd backend && uvicorn app.main:app --reload")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
