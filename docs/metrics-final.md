# Modelo final — Impacto de Señales Tempranas (Trends/RSS)

- Train rows (último fold): 265175
- Test rows (último fold): 65684
- Features: 54

## Regresión
- MAE: 2.8293
- RMSE: 8.7044
- R2: 0.8087

## Clasificación de brote
- Threshold: 5.00
- Precision: 0.8314
- Recall: 0.7730
- F1: 0.8012
- TP/FP/FN: 15759/3195/4627

## Comparación contra baseline
| Métrica | Baseline | Final | Delta |
|---|---|---|---|
| MAE | 2.8016 | 2.8293 | +0.0277 |
| RMSE | 8.3986 | 8.7044 | +0.3058 |
| Recall | 0.7718 | 0.7730 | +0.0012 |
| F1 | 0.8008 | 0.8012 | +0.0004 |

## Walk-Forward Validation

| Fold | Train end | Test end | MAE | Recall |
|---|---|---|---|---|
| 1 | 2018-03-05 | 2019-10-07 | 2.67 | 0.755 |
| 2 | 2019-10-07 | 2021-05-10 | 2.93 | 0.755 |
| 3 | 2021-05-10 | 2022-12-12 | 2.87 | 0.758 |

## SHAP Feature Importance (Top 15)

Verifica el ranking de `trends_score` y `rss_mentions_sum`:

- **cases_lag_1**: 5.9139
- **cases_lag_2**: 1.6977
- **cases_lag_4**: 0.6932
- **epi_week**: 0.2985
- **epi_year**: 0.2264
- **disease_malaria**: 0.0955
- **dept_76**: 0.0775
- **dept_5**: 0.0509
- **dept_27**: 0.0468
- **dept_52**: 0.0424
- **disease_dengue**: 0.0415
- **dept_23**: 0.0240
- **disease_zika**: 0.0229
- **dept_13**: 0.0203
- **dept_8**: 0.0179