# Diccionario de Datos (ECOS)

Este documento describe la estructura de datos del ecosistema ECOS completo: (1) el dataset curado semanal que resulta de la fase de Ingesta en PySpark y alimenta los modelos de predicción y Power BI, y (2) las demás entidades de datos que el sistema genera y expone — feature store completo, noticias clasificadas, alertas de Google Trends, definición operacional de brote y endpoints de la API. Existe para que el asistente RAG de ECOS pueda responder con precisión preguntas sobre qué significa cada variable, de dónde sale, y qué tan confiable es.

### Dataset curado base (grano semanal, por municipio y enfermedad — `Parquet`/`CSV`)

| Nombre de Columna | Tipo de Dato | Origen / Fuente | Descripción |
| :--- | :--- | :--- | :--- |
| **epi_year** | `INT` | SIVIGILA | Año epidemiológico. (Usualmente coincide con el calendario civil, pero se calcula basado en la lógica ISO 8601). |
| **epi_week** | `INT` | SIVIGILA | Semana epidemiológica (1 a 53). |
| **week_start_date** | `DATE` | SIVIGILA / PySpark | Fecha correspondiente al día Lunes de inicio de la semana epidemiológica especificada. |
| **week_end_date** | `DATE` | SIVIGILA / PySpark | Fecha correspondiente al día Domingo de fin de la semana epidemiológica especificada. |
| **departamento_code** | `STRING` | SIVIGILA | Código DANE del departamento (2 dígitos de longitud estricta). |
| **departamento_name** | `STRING` | SIVIGILA | Nombre oficial del departamento. |
| **municipio_code** | `STRING` | SIVIGILA | Código DANE del municipio (5 dígitos, incluye el de departamento). |
| **municipio_name** | `STRING` | SIVIGILA | Nombre oficial del municipio. |
| **event_code** | `INT` | SIVIGILA | Código del evento de interés en salud pública (eg. 210 para Dengue). |
| **event_name** | `STRING` | SIVIGILA | Nombre del evento clínico. |
| **disease** | `STRING` | Reglas de Negocio | Enfermedad objeto de estudio agrupada: `dengue`, `chikungunya`, `zika`, o `malaria`. |
| **cases_total** | `INT` | SIVIGILA | Total de casos probables y confirmados reportados en la semana para el municipio y enfermedad. (Columna target para métricas). |
| **temp_avg_c** | `FLOAT` | Clima IDEAM | Temperatura media histórica reportada en Celsius, asociada al municipio y mes correspondiente a la semana. |
| **temp_min_c** | `FLOAT` | Clima IDEAM | Temperatura mínima histórica en Celsius. |
| **temp_max_c** | `FLOAT` | Clima IDEAM | Temperatura máxima histórica en Celsius. |
| **precipitation_mm**| `FLOAT` | Clima IDEAM | Milímetros cúbicos promedio de lluvia/precipitación. |
| **vaccination_coverage_pct** | `FLOAT` | Minsalud | Cobertura anual de vacunación reportada a nivel departamental, en porcentaje (0-100%). |
| **temp_avg_c_actual** | `FLOAT` | OpenMeteo / IDEAM | Temperatura promedio real medida en Celsius para la semana epidemiológica específica. |
| **temp_min_c_actual** | `FLOAT` | OpenMeteo / IDEAM | Temperatura mínima real en Celsius para la semana. |
| **temp_max_c_actual** | `FLOAT` | OpenMeteo / IDEAM | Temperatura máxima real en Celsius para la semana. |
| **precipitation_mm_actual** | `FLOAT` | OpenMeteo / IDEAM | Precipitación real acumulada en milímetros para la semana. |
| **rips_visits_total** | `FLOAT` | RIPS (MinSalud) | Número total de consultas médicas registradas para sintomatología asociada en el municipio. |
| **mobility_in** | `FLOAT` | Flujos Terrestres | Volumen total estimado de pasajeros ingresando al municipio. |
| **mobility_out** | `FLOAT` | Flujos Terrestres | Volumen total estimado de pasajeros saliendo del municipio. |
| **mobility_index** | `FLOAT` | Modelos de Movilidad | Índice normalizado de movilidad humana general en la zona. |
| **trends_score** | `FLOAT` | Google Trends | Puntuación de volumen de búsquedas de términos relacionados en Google para el departamento. |
| **rss_mentions** | `FLOAT` | Medios RSS | Cantidad de menciones o artículos de noticias locales sobre brotes en medios regionales. |
| **signals_score** | `FLOAT` | Alertas ECOS | Puntaje consolidado de señales de alerta temprana basadas en exógenas. |


## Transformaciones Base (Full HD - Nativo)

Todos los valores de texto (`_name` y agrupaciones) reciben el siguiente tratamiento nativo de Apache Spark, sin UDFs:
1. Normalización de tildes (acentos).
2. Mayúsculas totales (`UPPER`).
3. Limpieza de puntos y consolidación de espacios múltiples.

Los códigos se formatean al estándar DANE validando exclusivamente dígitos numéricos y padding inicial con "0" de ser requerido. Las fechas se procesan nativamente determinando los cortes precisos bajo ISO Week formatting (`"xxxx-'W'ww-u"`).

## Convenciones y Mapeos de Referencia

Esta sección existe para que el asistente de RAG pueda resolver referencias temporales o textuales que aparezcan en preguntas de usuario (ej. "casos de dengue en marzo") y las traduzca correctamente a los campos numéricos del dataset (`epi_week`, `week_start_date`, etc.).

### Mapeo Mes → Número (para cruces con `week_start_date` / `week_end_date`)

| Mes | Número |
| :--- | :---: |
| Enero | 01 |
| Febrero | 02 |
| Marzo | 03 |
| Abril | 04 |
| Mayo | 05 |
| Junio | 06 |
| Julio | 07 |
| Agosto | 08 |
| Septiembre | 09 |
| Octubre | 10 |
| Noviembre | 11 |
| Diciembre | 12 |

> Nota: como el grano del dataset es semanal (`epi_week`), una consulta por mes debe traducirse a un rango de fechas (ej. "marzo" → `week_start_date` entre `YYYY-03-01` y `YYYY-03-31`) y luego filtrar las semanas epidemiológicas que caen dentro de ese rango, no a un único número de mes.

### Mapeo Día de la Semana → Número (ISO 8601, usado en `"xxxx-'W'ww-u"`)

| Día | Número ISO |
| :--- | :---: |
| Lunes | 1 |
| Martes | 2 |
| Miércoles | 3 |
| Jueves | 4 |
| Viernes | 5 |
| Sábado | 6 |
| Domingo | 7 |

### Alias comunes de enfermedades (para resolver sinónimos en preguntas de usuario)

| Alias / término coloquial | Valor normalizado en `disease` |
| :--- | :--- |
| dengue, dengue clásico, dengue grave | `dengue` |
| chikungunya, chik-v, fiebre chikungunya | `chikungunya` |
| zika, virus zika | `zika` |
| malaria, paludismo | `malaria` |

### Escala de referencia para `signals_score`

`signals_score` es un puntaje **consolidado** que resume varias señales de alerta temprana (Trends + noticias) en un solo número. El proyecto aún no define la fórmula exacta de consolidación — eso queda pendiente de que el equipo de modelado la fije. Lo que **sí** está definido y es real (ver clasificación de Trends más abajo) es el criterio para las señales individuales que lo alimentan, así que esta tabla se deja como placeholder hasta que exista la fórmula:

| Rango | Interpretación |
| :--- | :--- |
| 0.0 – 0.3 | Señal baja / sin alerta |
| 0.3 – 0.6 | Señal moderada / vigilancia |
| 0.6 – 1.0 | Señal alta / posible brote |

> ⚠️ Placeholder — reemplazar cuando el equipo defina cómo se calcula `signals_score` a partir de `trend_nacional_zscore`, `trend_dpto_zscore` y `score_alerta_noticias`.

---

## Definición Operacional de "Brote" (usada para todas las métricas del modelo)

> **Brote** = semana en la que los casos reportados superan el **percentil 75 del canal endémico histórico** del mismo municipio, para la misma semana epidemiológica, calculado sobre los últimos 5 años disponibles, **excluyendo 2020 y 2021** (ruido COVID). Metodología alineada con el INS Colombia.

| Percentil del canal endémico | Significado |
| :--- | :--- |
| p25 | Límite inferior de la zona de seguridad |
| p50 | Mediana histórica (comportamiento típico) |
| **p75** | **Umbral de alerta → si se supera, la semana se clasifica como BROTE (Y=1)** |
| p90 | Umbral de epidemia (severidad alta dentro de un brote) |

Esta definición es la que fija el threshold de clasificación binaria sobre el que se calculan AUC-ROC, sensibilidad (recall) y tasa de falsa alarma. El asistente debe usar esta definición si le preguntan "¿qué cuenta como brote en ECOS?" — no inventar un umbral distinto.

---

## Variables del Feature Store Completo (por municipio + semana epidemiológica)

Estas son todas las variables que alimentan el modelo Prophet + XGBoost, más allá de las columnas del dataset curado base descritas arriba. Van organizadas por grupo, tal como en la arquitectura del proyecto.

### Epidemiológicas (SIVIGILA + RIPS)

| Variable | Tipo | Descripción |
| :--- | :--- | :--- |
| **casos_dengue / casos_chiku / casos_malaria / casos_zika** | `INT` | Casos por enfermedad, en rezagos t-1, t-2, t-4 semanas. |
| **atenciones_cie10_dengue** | `FLOAT` | Consultas RIPS con diagnóstico CIE-10 asociado a dengue, semana t-1. |
| **divergencia_rips_sivigila** | `FLOAT` | Diferencia entre atenciones RIPS y casos SIVIGILA — se usa como **señal de subnotificación activa**, no como conteo absoluto de casos (ver limitación ⑤ en Ecos.md). |

### Climáticas

| Variable | Tipo | Descripción |
| :--- | :--- | :--- |
| **temp_max / temp_min / temp_media** | `FLOAT` | Temperaturas en °C (IDEAM histórico + Open-Meteo actual). |
| **humedad_relativa** | `FLOAT` | Porcentaje de humedad relativa. |
| **precipitacion** | `FLOAT` | Milímetros de precipitación. |

### Movilidad

| Variable | Tipo | Descripción |
| :--- | :--- | :--- |
| **pasajeros_entrantes_semana / pasajeros_salientes_semana** | `INT` | Volumen de pasajeros OD intermunicipal, dataset MinTransporte. |
| **conectividad_municipios_alerta** | `INT` | Cuántos municipios conectados por movilidad están actualmente en alerta — mide riesgo de importación de casos. |

> Nota: el dataset de movilidad puede estar desactualizado (pre-2020). Si la fecha de corte es anterior a 2020, la variable se pondera con menor peso en XGBoost (limitación ⑥).

### Señales tempranas — Google Trends (enfoque híbrido nacional + departamental)

| Variable | Tipo | Descripción |
| :--- | :--- | :--- |
| **trend_nacional_dengue / _malaria / _chiku / _zika** | `FLOAT` (0-100) | Índice de búsquedas Google Trends a nivel Colombia, siempre disponible. Peso en el modelo: 5-8% del feature importance. |
| **trend_nacional_zscore** | `FLOAT` | Desviaciones estándar del índice nacional actual vs. su media histórica. Variable que entra directamente al modelo (peso `0.3`, ver tabla de pesos abajo). |
| **trend_dpto_dengue** (y equivalentes por enfermedad) | `FLOAT` o `NULL` | Índice departamental — solo válido para los 9 departamentos con volumen suficiente (ver tabla abajo). `NULL` si Google no reporta datos, **nunca se imputa**. |
| **trend_dpto_zscore** | `FLOAT` | Desviación departamental vs. histórico del mismo departamento/keyword. Peso reducido (`0.15`). |
| **trend_dpto_disponible** | `BOOL` | Indica si el dato departamental es válido para esa fila (evita que el modelo o el RAG traten un `NULL` como cero). |

**Departamentos con Trends departamental válido** (cobertura de internet >40% y volumen suficiente):
Antioquia, Valle del Cauca, Atlántico, Cundinamarca, Santander, Bolívar, Nariño (zona urbana de Pasto), Huila, Tolima. Para el resto del país (Vaupés, Guainía, Vichada, Amazonas, Chocó rural, San Andrés) la predicción se apoya solo en clima + SIVIGILA + RIPS.

**Clasificación estadística de un spike de Trends** (aplica igual a nivel nacional y departamental, usando z-score vs. la media histórica de la misma serie):

| Z-score | Nivel de alerta | Interpretación |
| :--- | :--- | :--- |
| < 2.0 SD | 🟢 VERDE | Normal |
| 2.0 – 2.9 SD | 🟡 AMARILLA | Atención pública elevada |
| ≥ 3.0 SD | 🔴 ROJA | Atención pública muy elevada |

### Señales tempranas — Noticias scrapeadas

| Variable | Tipo | Descripción |
| :--- | :--- | :--- |
| **menciones_medios_dpto** | `INT` | Conteo de noticias epidemiológicas relevantes, semana t-1. |
| **score_alerta_noticias** | `FLOAT` (0-1) | Promedio de los `alert_score` (ver modelo de noticias abajo) de los artículos del departamento en la semana. |

> El peso de las noticias en el modelo se ajusta por **densidad mediática histórica** del departamento: un artículo sobre un departamento con poca cobertura mediática (ej. Chocó) pesa más que uno sobre Bogotá, para compensar el sesgo de que los medios cubren más las ciudades grandes (limitación ⑦).

### Estructurales (anuales, nivel departamental)

| Variable | Tipo | Descripción |
| :--- | :--- | :--- |
| **cobertura_vacunacion_dpt** | `FLOAT` | % de cobertura de vacunación, Minsalud. Solo a nivel departamental — no se extrapola al municipio (limitación ④). |
| **indice_pobreza_multidimensional** | `FLOAT` | IPM municipal — usado como proxy de acceso a servicios de salud, ya que sí tiene resolución municipal (a diferencia de vacunación). |
| **cobertura_acueducto / cobertura_alcantarillado** | `FLOAT` | % de cobertura de servicios públicos, factor asociado a criaderos de vector. |

### Variables objetivo (target)

| Variable | Tipo | Descripción |
| :--- | :--- | :--- |
| **prob_brote_2sem** | `FLOAT` (0-1) | Probabilidad de brote (según la definición de canal endémico p75) en las próximas 2 semanas. Salida de clasificación. |
| **casos_predichos_2sem** | `INT` | Casos esperados en 2 semanas. Salida de regresión (Prophet + XGBoost residual). |
| **casos_predichos_4sem** | `INT` | Casos esperados en 4 semanas. |

### Pesos de features en XGBoost (feature importance controlado)

Estos pesos son una decisión de diseño explícita para que las señales con sesgo geográfico conocido (Trends, noticias) no dominen sobre las fuentes confiables (clima, SIVIGILA, RIPS):

| Variable | Peso |
| :--- | :---: |
| temperatura_media / humedad_relativa / precipitacion | 1.0 |
| casos_semana_anterior / casos_4sem_anteriores | 1.0 |
| atenciones_cie10 (RIPS) | 0.9 |
| pasajeros_entrantes | 0.8 |
| menciones_medios | 0.6 |
| trend_nacional | 0.3 |
| trend_departamental | 0.15 |

---

## Etiquetas de Confiabilidad (para que el RAG matice sus respuestas)

### Por enfermedad (según años de datos históricos disponibles)

| Enfermedad | Datos desde | Ciclos observados | Confianza del modelo | Meta AUC-ROC | IC de predicción |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Dengue | 2007 | 8+ | Alta | > 0.85 | ±12% |
| Malaria | 2007 | Endémica continua | Alta | > 0.83 | ±15% |
| Chikungunya | 2014 | 2 | Media | > 0.78 | ±22% |
| Zika | 2015 | 1 | Baja | > 0.72 | ±30% |

> El RAG debe advertir explícitamente cuando responda sobre zika o chikungunya que el intervalo de confianza es más ancho por menor histórico disponible.

### Por tipo de zona (subnotificación estructural de SIVIGILA)

| Zona | Confiabilidad del dato base |
| :--- | :--- |
| Bogotá, Medellín (grandes capitales) | Alta |
| Otras capitales departamentales | Media |
| Municipios rurales sin IPS cercana | Baja — subnotificación estimada 50-70% (OPS/INS) |

---

## Modelo de Datos — Noticias Scrapeadas

Estructura de cada artículo clasificado que alimenta el Dashboard 4 y el RAG (endpoint `GET /api/v1/news`):

| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| **id** | `STRING` | Identificador único del artículo. |
| **title** | `STRING` | Titular. |
| **source** | `STRING` | Medio de origen (ej. "La Opinión", "El Heraldo"). |
| **source_url** | `STRING` | URL del artículo original. |
| **published_at** | `DATE` | Fecha de publicación. |
| **disease** | `STRING` | Una de: `dengue`, `chikungunya`, `malaria`, `zika`, `general`. |
| **department** | `STRING` | Departamento mencionado, extraído por NER (spaCy `es_core_news_sm`). |
| **municipality** | `STRING` (opcional) | Municipio, si el NER lo detectó. |
| **alert_score** | `FLOAT` (0-1) | Score de urgencia/sentimiento del clasificador NLP. |
| **alert_level** | `STRING` | `alta`, `media`, o `baja` — derivado de `alert_score` (los cortes numéricos exactos no están definidos aún en el proyecto; pendiente de calibración por el equipo). |
| **snippet** | `STRING` | Primeros ~200 caracteres del artículo. |

**Fuentes RSS monitoreadas:** El Tiempo, Noticias RCN, Caracol Radio, El Heraldo (Caribe), El Colombiano (Antioquia), La Opinión (Nariño), Diario del Huila, más boletines PDF oficiales del INS.

**Términos de alerta usados para filtrar artículos relevantes:** dengue, chikungunya, malaria, zika, brote, alerta sanitaria, epidemia, mosquito, vector, casos confirmados, secretaría de salud, emergencia sanitaria.

---

## Tabla de Equivalencias DANE (normalización de códigos históricos)

El histórico SIVIGILA 2007–2022 tiene códigos DANE inconsistentes porque se crearon municipios nuevos y se reasignaron códigos en ese periodo (ej. Riosucio en Chocó, varios en Nariño). Existe una tabla de mapeo (`data/raw/divipola_historico.csv`, fuente DIVIPOLA del DANE) con esta estructura:

| Campo | Descripción |
| :--- | :--- |
| **cod_dane_historico** | Código DANE tal como aparece en registros antiguos. |
| **cod_dane_vigente** | Código DANE vigente a 2023, al que se debe normalizar. |
| **municipio** | Nombre del municipio. |
| **dpto** | Departamento. |
| **año_cambio** | Año en que ocurrió el cambio de código. |

Todo `JOIN` sobre `municipio_code` en el pipeline PySpark pasa primero por esta tabla de equivalencias para evitar municipios "fantasma" o pérdida silenciosa de registros históricos.

---

## Referencia de Endpoints (para que el RAG sepa qué datos vienen de dónde)

| Endpoint | Devuelve |
| :--- | :--- |
| `GET /api/v1/predictions` | `prob_brote_2sem`, `casos_predichos_2sem/4sem` por dpto/municipio/semana |
| `GET /api/v1/alerts/active` | Alertas activas actuales (🔴🟡🟢) |
| `GET /api/v1/shap` | Contribución SHAP por variable para una predicción específica |
| `GET /api/v1/trends` | Índices `trend_nacional_*` y `trend_dpto_*` + alerta estadística (VERDE/AMARILLA/ROJA) |
| `GET /api/v1/news` | Feed de noticias clasificadas (estructura de arriba) |
| `GET /api/v1/mobility/od` | Flujos origen-destino enriquecidos con `risk_score` |
| `GET /api/v1/timeseries` | Serie histórica de casos + predicción |
| `POST /api/v1/chat` | Endpoint del RAG conversacional |
| `POST /api/v1/whatif` | Simulador de escenarios |
| `GET /api/v1/report/pdf` | Reporte PDF automático por departamento |