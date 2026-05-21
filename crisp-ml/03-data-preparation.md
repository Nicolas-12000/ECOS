# Fase 3: Preparación de Datos (Data Preparation)

En esta fase del proyecto siguiendo la metodología CRISP-ML, integramos todos nuestros esfuerzos de limpieza e indexación cruzada entre múltiples bases de datos de `datos.gov.co` en un solo motor de procesamiento a gran escala: Apache Spark. 

## Arquitectura de Transformación (PySpark Pipeline)

La herramienta principal para la preparación de datos de ECOS se encuentra en el script `scripts/curate_weekly_spark.py`. Su labor consiste en unificar cinco (5) conjuntos de datos sumamente diferentes (tanto en granularidad como en formato y periodicidad) dentro de una única base maestra granular semanal (`Parquet/CSV`). 

El dataset resultante asegura la consistencia e integridad relacional de `municipios`, `semanas epidemiológicas` y las respectivas enfermedades objeto (`Dengue`, `Chikungunya`, `Zika`, `Malaria`).

### Pipeline Base:
1. **Ingesta de SIVIGILA Historico:** Almacenamiento maestro. Filtramos años válidos y extraemos la base que guiará el modelado (Target: `cases_total` por enfermedad y localidad).
2. **Cruce Climático (IDEAM):** El clima (temp_avg, precipitaciones, humedad) viene a grano mensual o estaciones históricas. Se promedia a meses numéricos y se cruza usando el mes correspondiente de la fecha semanal a procesar.
3. **Senales Médicas Preeliminares (RIPS):** Se leen atenciones RIPS para extraer de ellos diagnósticos CIE10 y poder correlacionar cruces asíncronos entre picos de "sospechas médicas" en urgencias vs los "boletines confirmados".
4. **Agentes Exógenos:** 
    - **Movilidad Intermunicipal:** Conteo de flujo semanal agregando despachos y pasajeros.
    - **Vacunación:** Porcentaje de cobertura global departamental del año asociado.

## Optimizaciones a Nivel de Producción (High Definition)

Dado que `SIVIGILA` consolida millones de registros desde hace más de una década, la canalización implementada emplea tácticas "Nativas de Apache Spark (Native Functions)" descartando de manera estricta el uso de *User Defined Functions (UDFs)* de Python.

- **String Translations:** Sustituir regex local de python o `unicodedata` con las propiedades integradas de `F.translate()` permitiendo distribuir correctamente en Workers de Java los string-matchings.
- **DANE Parsing:** Se estandarizaron los cruces y validaciones espaciales a través de `F.lpad()` para rellenar códigos DANE que han perdido ceros al ser parseados.
- **ISOCalendar Nativo (Time Travel Engine):** Se configuraron los cálculos de tiempos semanales mediante el formato puro de PySpark `date_format('xxxx')` determinando con un solo tick computacional, el año, semana o día de la semana para los cruces temporales evitando cuellos de botella asincrónicos. 

Este enfoque garantiza tiempos de reconstrucción bajo los 2 a 3 minutos, listos para integracion CICD en ecosistemas cloud de MinSalud en versiones estables V1 de los datos procesados.
