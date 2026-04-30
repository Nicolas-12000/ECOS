from datetime import date

import pandas as pd

from app.services import prediction


class _FakeBooster:
    feature_names = [
        "epi_year",
        "epi_week",
        "cases_lag_1",
        "cases_lag_2",
        "cases_lag_4",
        "temp_avg_c",
        "temp_min_c",
        "temp_max_c",
        "humidity_avg_pct",
        "precipitation_mm",
        "vaccination_coverage_pct",
        "rips_visits_total",
        "mobility_index",
    ]


class _FakeModel:
    def get_booster(self):
        return _FakeBooster()

    def predict(self, frame):
        return [float(frame.iloc[0]["cases_lag_1"]) + 10.0]


def test_predict_cases_is_recursive(monkeypatch):
    history = pd.DataFrame(
        [
            {"week_start_date": date(2026, 4, 6), "cases_total": 3},
            {"week_start_date": date(2026, 3, 30), "cases_total": 2},
            {"week_start_date": date(2026, 3, 23), "cases_total": 1},
            {"week_start_date": date(2026, 3, 16), "cases_total": 0},
        ]
    )
    last_row = pd.Series(
        {
            "epi_year": 2026,
            "epi_week": 14,
            "departamento_code": "05",
            "cases_total": 3,
            "temp_avg_c": 23.0,
            "temp_min_c": 18.0,
            "temp_max_c": 29.0,
            "humidity_avg_pct": 70.0,
            "precipitation_mm": 12.0,
            "vaccination_coverage_pct": 0.8,
            "rips_visits_total": 100.0,
            "mobility_index": 1.2,
        }
    )

    monkeypatch.setattr(prediction, "load_model", lambda: _FakeModel())
    monkeypatch.setattr(prediction, "get_history", lambda municipio_code, disease, limit=10: history.copy())
    monkeypatch.setattr(prediction, "get_last_known_features", lambda municipio_code, disease: last_row.copy())

    results = prediction.predict_cases("05001", "dengue", weeks_ahead=2)

    assert [item["predicted_cases"] for item in results] == [13.0, 23.0]
    assert [item["week_start_date"] for item in results] == [date(2026, 4, 6), date(2026, 4, 13)]
