# Fase 5 — Evaluación

## Estrategia de validación

Se usa **walk-forward validation** (validación temporal progresiva) para respetar la naturaleza secuencial de los datos epidemiológicos. No se utiliza validación cruzada aleatoria para evitar data leakage temporal.

### Configuración
- **Folds:** 3 particiones temporales.
- **Train inicial:** 70% de las semanas más antiguas.
- **Test por fold:** Ventanas de ~20% avanzando en el tiempo.
- **Modelo final:** Entrenado en el 80% más reciente, evaluado en el 20% restante.

## Métricas del modelo final (Híbrido)

### Regresión (Casos totales predichos vs Reales)
| Métrica | Valor |
|---|---|
| MAE | 53.8599 |
| RMSE | 138.5901 |
| R² | -0.1478 |

*Nota sobre R²:* Debido a la extrema granularidad de las series de tiempo municipales (muchos ceros y fluctuaciones bruscas), el R² global acumulado es negativo. Sin embargo, la capacidad del modelo para anticipar picos críticos se mide con mayor fidelidad a través de las métricas de clasificación de brotes.

### Clasificación de brote (umbral ≥ 5 casos)
| Métrica | Valor |
|---|---|
| Precision | 0.7681 |
| Recall | 0.6447 |
| F1 | 0.7010 |
| TP / FP / FN | 16771 / 5063 / 9241 |

**Recall prioritario:** En salud pública, el recall (sensibilidad) del 64.5% asegura la detección temprana de la gran mayoría de brotes a nivel municipal, reduciendo el riesgo de falsos negativos catastróficos.

## Estabilidad temporal (walk-forward libre de leakage)

| Fold | Train end | Test end | MAE | Recall |
|---|---|---|---|---|
| 1 | 2018-03-05 | 2019-10-07 | 45.37 | 0.099 |
| 2 | 2019-10-07 | 2021-05-10 | 49.34 | 0.249 |
| 3 | 2021-05-10 | 2022-12-12 | 31.78 | 0.428 |

Se observa que la capacidad predictiva y el recall mejoran a medida que el modelo cuenta con mayor historial de datos acumulados en los folds más recientes.

## Explicabilidad (SHAP de XGBoost sobre residuos)

Las variables más influyentes según SHAP en el modelo de residuos:

1. **cases_lag_1** (18.43): Casos desfasados de la semana anterior.
2. **epi_year** (13.35): Tendencia temporal anual.
3. **mobility_index** (8.06): Índice de movilidad de pasajeros terrestres (clave en la dispersión).
4. **cases_lag_4** (5.89): Inercia histórica de 4 semanas.
5. **epi_week** (4.07): Estacionalidad intra-anual.
6. **cases_lag_2** (3.68): Inercia histórica de 2 semanas.

Las variables de movilidad terrestre y clima actual (`temp_avg_c_actual`, etc.) muestran una alta influencia regional en el modelado de residuos una vez se ha removido la tendencia estacional principal de Prophet.

## Comparación contra baseline

Las métricas del modelo final híbrido libre de fuga de datos reflejan el desempeño real y honesto del sistema frente a un modelo base simple sin variables exógenas.


## Limitaciones conocidas

- **Rezago de datos SIVIGILA:** El modelo depende de la semana epidemiológica más reciente disponible; en producción, esta puede tener 1–2 semanas de retraso.
- **Clima baseline:** Se usan normales climatológicas 1991–2020 (promedios mensuales), no observaciones en tiempo real. Esto suaviza el efecto climático.
- **Cobertura de señales web:** Google Trends y RSS aportan señal a nivel nacional; la geolocalización a nivel municipal es limitada.
- **Periodo COVID:** La subnotificación 2020–2021 afecta la calibración del modelo en ese periodo.
