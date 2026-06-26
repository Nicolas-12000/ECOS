# Fase 4: Modelado Predictivo (Modeling)

Esta fase comprende la estructuración, entrenamiento y evaluación de los modelos de Machine Learning utilizados en ECOS para detectar alertas epidemiológicas tempranas.

## Estrategia de Ingesta y Feature Engineering (KISS & DRY)
Hemos evitado sobre-normalizar las variables tabulares (optando por `Wide Tables` generadas en la Fase 3) maximizando la compresión nativa de XGBoost. 

A través del archivo maestro `models/utils.py`, automatizamos las siguientes técnicas base de series temporales:
1. **Lags Predictivos:** Variables predictoras desfasadas iterativamente 1, 2 y 4 semanas atrás (`cases_lag_{lag}`) forzando al algoritmo a detectar el pico de incubación inicial (comúnmente 1 a 3 semanas documentado por epidemiólogos).
2. **One-Hot-Encoding Local:** Codificación departamental dummy para que el modelo reconozca biomas fijos (ej. la Guajira tiene variables nulas frente a las recurrentes variables endémicas del Pacífico).
3. **Walk-Forward Validation:** Utilización conservadora de regresión asíncrona (el set de Train es inferior estricto a las fechas target del set de evaluación de validación) impidiendo cualquier `Data Leakage`.

## Modelos en Producción

### Baseline V0
`models/baseline_v0.py`
Considerado el "Cold Start" mínimo. Predice empleando puramente:
- El tracking retrospectivo de casos reportados SIVIGILA.
- Funciones meteorológicas agrupadas mensuales.

### Modelo Final Híbrido (Prophet + XGBoost)
`models/model_final.py`
Nuestra arquitectura de producción integra un modelo híbrido para capturar simultáneamente la tendencia histórica a largo plazo y las señales tempranas:
1. **Línea base con Prophet:** Ajusta curvas de tendencia, estacionalidad anual y semanal de forma independiente para cada par de municipio y enfermedad. Se entrena **estrictamente en el conjunto histórico** (libre de target leakage).
2. **Residuos con XGBoost:** El modelo XGBoost se entrena para predecir el residuo (casos reales menos la estimación de Prophet). XGBoost se nutre de variables exógenas de corto plazo:
   - **Agentes Clínicos (`rips_visits_total`):** Incremento de urgencias médicas registradas preliminarmente.
   - **Vulnerabilidad Inmune (`vaccination_coverage_pct`):** Cobertura de vacunación anual.
   - **Densidad Viral Dinámica (`mobility_index`):** Flujos de pasajeros intermunicipales terrestres.
   - **Señales Web y Medios (`trends_score`, `rss_mentions`):** Búsquedas en Google y noticias locales georreferenciadas.
3. **Predicción Combinada:** La inferencia final se obtiene sumando la estimación estacional de Prophet y el residuo predicho por XGBoost, recortada a 0 en caso de valores negativos: $\hat{y}_{\text{total}} = \max(0, \hat{y}_{\text{prophet}} + \hat{y}_{\text{residual}})$.

#### Transparencia Predictiva (Explicabilidad SHAP)
El algoritmo finaliza entregando la importancia de variables por SHAP (Shapley Additive exPlanations) calculada sobre el estimador XGBoost, lo que permite auditar legal y técnicamente cada alerta sanitaria en lenguaje natural.

