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

### Model V1 (SHAP Enriched)
`models/model_v1.py`
Proceso que integra por completo nuestra lógica de negocio basada en captaciones de métricas tempranas:
- **Agentes Clínicos (`rips_visits_total`):** Incremento de urgencias médicas registradas preliminarmente.
- **Vulnerabilidad Inmune:** Porcentaje de población vacunada en la etapa epidemiológica a clasificar.
- **Densidad Viral Dinámica (`mobility_index`):** Transmisiones estimadas entre flujos municipales (terminales terrestres).

#### Transparencia Predictiva (Explicabilidad SHAP)
Acuerdos institucionales exigen que cualquier alerta sanitaria esté altamente sustentada legalmente. Por ende, el algoritmo V1 finaliza la regresión entregando el `SHAP Feature Importance Plot`. La métrica descodificada de SHAP (Shapley Additive exPlanations) entrega de forma humana la ponderación matemática del por qué el algoritmo concluyó que un brote comenzará, p. ej.: *"El modelo ha emitido la alerta fundamentándose en un alza del ratio de 24% en RIPS, más la lluvia máxima (40mm) y las tendencias rezagadas del chikungunya hace 2 semanas"*.
