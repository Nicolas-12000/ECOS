# Modelo final — Métricas y comparación

- Train rows (último fold): 164265
- Test rows (último fold): 40773
- Features: 60

## Regresión
- MAE: 6.7977
- RMSE: 16.4281
- R2: 0.7300

## Clasificación de brote
- Threshold: 5.00
- Precision: 0.7687
- Recall: 0.9080
- F1: 0.8325
- TP/FP/FN: 16144/4859/1636

## Walk-forward validation

| Fold | Train end | Test end | MAE | Recall |
|---|---|---|---|---|
| 1 | 2018-03-05 | 2019-10-07 | 12.58 | 0.386 |
| 2 | 2019-10-07 | 2021-05-10 | 10.52 | 0.441 |
| 3 | 2021-05-10 | 2022-12-12 | 5.98 | 0.911 |
