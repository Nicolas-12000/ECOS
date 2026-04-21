# Diccionario de Datos Curados (ECOS v1)

Este documento describe con detalle la estructura de datos que resulta de la fase de Ingesta y Curado en PySpark. Corresponde al dataset final que consumen los modelos de predicción y el dashboard de Power BI. Este archivo consolidado en `Parquet` y `CSV` tiene grano semanal, por municipio y por tipo de enfermedad.

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
| **humidity_avg_pct**| `FLOAT` | Clima IDEAM | Porcentaje promedio de humedad relativa. |
| **precipitation_mm**| `FLOAT` | Clima IDEAM | Milímetros cúbicos promedio de lluvia/precipitación. |
| **vaccination_coverage_pct** | `FLOAT` | Minsalud | Cobertura anual reportada a nivel departamental, en porcentaje (0-100%). |
| **rips_visits_total** | `BIGINT` | RIPS (MinSalud) | Cantidad total de atenciones recibidas en la red de clínicas que reportaron códigos CIE-10 asociados a la enfermedad en este territorio y año. |
| **mobility_index** | `FLOAT` | Terminales (DATOS) | Conteo total de volumen de pasajeros ingresando y saliendo del municipio durante la semana. |

## Transformaciones Base (Full HD - Nativo)

Todos los valores de texto (`_name` y agrupaciones) reciben el siguiente tratamiento nativo de Apache Spark, sin UDFs:
1. Normalización de tildes (acentos).
2. Mayúsculas totales (`UPPER`).
3. Limpieza de puntos y consolidación de espacios múltiples.

Los códigos se formatean al estándar DANE validando exclusivamente dígitos numéricos y padding inicial con "0" de ser requerido. Las fechas se procesan nativamente determinando los cortes precisos bajo ISO Week formatting (`"xxxx-'W'ww-u"`).
