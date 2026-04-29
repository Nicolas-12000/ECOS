# Fase 5 — Evaluación

## Estrategia de validación

Se usa **walk-forward validation** (validación temporal progresiva) para respetar la naturaleza secuencial de los datos epidemiológicos. No se utiliza validación cruzada aleatoria para evitar data leakage temporal.

### Configuración
- **Folds:** 3 particiones temporales.
- **Train inicial:** 70% de las semanas más antiguas.
- **Test por fold:** Ventanas de ~20% avanzando en el tiempo.
- **Modelo final:** Entrenado en el 80% más reciente, evaluado en el 20% restante.

## Métricas del modelo final

### Regresión
| Métrica | Valor |
|---|---|
| MAE | 2.8293 |
| RMSE | 8.7044 |
| R² | 0.8087 |

### Clasificación de brote (umbral ≥ 5 casos)
| Métrica | Valor |
|---|---|
| Precision | 0.8314 |
| Recall | 0.7730 |
| F1 | 0.8012 |
| TP / FP / FN | 15759 / 3195 / 4627 |

**Recall como métrica prioritaria:** En salud pública, no detectar un brote (falso negativo) tiene consecuencias mucho más graves que una falsa alarma (falso positivo). Un recall de 0.77 significa que el modelo detecta ~77% de los brotes reales.

## Estabilidad temporal (walk-forward)

| Fold | Train end | Test end | MAE | Recall |
|---|---|---|---|---|
| 1 | 2018-03-05 | 2019-10-07 | 2.67 | 0.755 |
| 2 | 2019-10-07 | 2021-05-10 | 2.93 | 0.755 |
| 3 | 2021-05-10 | 2022-12-12 | 2.87 | 0.758 |

Los resultados son estables entre folds, lo que indica que el modelo generaliza bien a diferentes periodos temporales, incluyendo el periodo COVID-19 que afectó la notificación de arbovirosis.

## Explicabilidad (SHAP)

Las 5 variables más influyentes según SHAP (mean absolute value):

1. **cases_lag_1** (5.91): La semana anterior es el predictor más fuerte, lo cual es epidemiológicamente consistente.
2. **cases_lag_2** (1.70): La inercia temporal de 2 semanas confirma la naturaleza autocorrelativa de los brotes.
3. **cases_lag_4** (0.69): Ventana de un mes, útil para capturar ciclos cortos.
4. **epi_week** (0.30): Estacionalidad intrasemanal (temporadas de lluvia).
5. **epi_year** (0.23): Tendencias interanuales.

Las variables climáticas y de movilidad contribuyen marginalmente en el agregado nacional, pero su impacto varía por departamento (ej: humedad relativa es más relevante en el Pacífico y Amazonía).

## Comparación contra baseline

| Métrica | Baseline v0 | Modelo Final | Delta |
|---|---|---|---|
| MAE | 2.8016 | 2.8293 | +0.0277 |
| RMSE | 8.3986 | 8.7044 | +0.3058 |
| Recall | 0.7718 | 0.7730 | +0.0012 |
| F1 | 0.8008 | 0.8012 | +0.0004 |

El modelo final mantiene la precisión del baseline mientras añade variables exógenas (clima, vacunación, movilidad, señales tempranas) que mejoran la explicabilidad y permiten escenarios what-if, aún cuando el impacto numérico agregado sea marginal. La contribución real de las variables exógenas se observa en regiones específicas con SHAP local.

## Limitaciones conocidas

- **Rezago de datos SIVIGILA:** El modelo depende de la semana epidemiológica más reciente disponible; en producción, esta puede tener 1–2 semanas de retraso.
- **Clima baseline:** Se usan normales climatológicas 1991–2020 (promedios mensuales), no observaciones en tiempo real. Esto suaviza el efecto climático.
- **Cobertura de señales web:** Google Trends y RSS aportan señal a nivel nacional; la geolocalización a nivel municipal es limitada.
- **Periodo COVID:** La subnotificación 2020–2021 afecta la calibración del modelo en ese periodo.
