# Modelo final — Métricas y comparación

- Train rows (último fold): 164265
- Test rows (último fold): 40773
- Features: 58

## Regresión
- MAE: 66.4302
- RMSE: 170.9573
- R2: -0.7466

## Clasificación de brote
- Threshold: 5.00
- Precision: 0.7681
- Recall: 0.6447
- F1: 0.7010
- TP/FP/FN: 16771/5063/9241

## Walk-forward validation

| Fold | Train end | Test end | MAE | Recall |
|---|---|---|---|---|
| 1 | 2018-03-05 | 2019-10-07 | 167.58 | 0.099 |
| 2 | 2019-10-07 | 2021-05-10 | 124.24 | 0.249 |
| 3 | 2021-05-10 | 2022-12-12 | 57.89 | 0.428 |

## SHAP Feature Importance (Top 10)

- **cases_lag_1**: 18.4327
- **epi_year**: 13.3506
- **mobility_index**: 8.0630
- **cases_lag_4**: 5.8896
- **epi_week**: 4.0739
- **cases_lag_2**: 3.6788
- **disease_dengue**: 2.8308
- **mobility_in**: 2.6964
- **vaccination_coverage_pct**: 2.4431
- **mobility_out**: 1.9760
