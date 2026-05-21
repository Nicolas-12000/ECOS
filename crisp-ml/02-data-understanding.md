# Fase 2 — Comprensión de los Datos

## Fuentes primarias (datos.gov.co)

### Dataset 1 — SIVIGILA (2007–2022)
- **Volumen:** ~10M+ registros, 168 MB en CSV crudo.
- **Granularidad:** Casos por municipio, semana epidemiológica, evento de salud pública.
- **Variables clave:** `ANO`, `SEMANA`, `COD_DPTO_O`, `COD_MUN_O`, `Nombre_evento`, `conteo`.
- **Calidad observada:**
  - Códigos DANE inconsistentes en algunos años (dígitos faltantes, padding incorrecto).
  - Periodo COVID (2020–2021) presenta subnotificación significativa en arbovirosis.
  - Eventos se identifican por texto (`Nombre_evento`), no por código estándar único.
- **Tratamiento:** Normalización DANE a 2 dígitos (departamento) y 5 dígitos (municipio), filtrado de años válidos (1900–2100), eliminación de registros sin código geográfico.

### Dataset 2 — Normales Climatológicas IDEAM
- **Volumen:** 2.3 MB, estaciones por municipio.
- **Granularidad:** Promedios mensuales por estación y parámetro.
- **Variables clave:** Temperatura (min, media, max), humedad relativa, precipitación.
- **Calidad observada:**
  - Valores numéricos con comas decimales (formato europeo).
  - Nombres de departamentos con acentos y variaciones de escritura.
  - Múltiples periodos de referencia (1961–1990, 1981–2010, 1991–2020).
- **Tratamiento:** Normalización de texto (acentos, variantes), conversión de comas a puntos, pivoteo de meses a filas, promediado por municipio/departamento/mes.

### Dataset 3 — Vacunación por Departamento
- **Volumen:** 81 KB, coberturas anuales por departamento y biológico.
- **Variables clave:** Departamento, año, cobertura porcentual.
- **Calidad observada:**
  - Nombres de columnas varían entre años (encoding Latin-1).
  - Coberturas mayores a 100% en algunos departamentos (posible doble conteo).
- **Tratamiento:** Normalización de nombres de columnas, promedio de coberturas por departamento/año, join por código DANE del departamento.

### Dataset 4 — RIPS (Prestaciones de Salud)
- **Volumen:** ~1.3 GB (vista agregada) / ~4 GB (detallado).
- **Granularidad:** Atenciones por diagnóstico CIE-10, municipio y año.
- **Variables clave:** Código diagnóstico, número de atenciones, departamento, municipio.
- **Calidad observada:**
  - Formato de columnas con DANE embebido en etiquetas ("05541 - Peñol").
  - Diagnósticos CIE-10 relevantes: A90/A91 (dengue), A920 (chikungunya), A925 (zika), B50-B54 (malaria).
- **Tratamiento:** Extracción de códigos DANE desde etiquetas, mapeo CIE-10 a enfermedad, agregación anual por municipio/enfermedad.

### Dataset 5 — Movilidad Nacional (Intermunicipal)
- **Volumen:** 407 MB, flujos de pasajeros intermunicipales.
- **Variables clave:** Municipio origen, municipio destino, fecha despacho, pasajeros.
- **Calidad observada:**
  - Fechas en múltiples formatos (YYYY-MM-DD, MM/DD/YYYY).
  - `epi_year` se deriva del calendario, no de ISO week.
- **Tratamiento:** Parsing robusto de fechas, normalización de códigos DANE, cálculo de índice de movilidad (pasajeros entrantes + salientes por municipio/semana).

## Fuentes externas (señales tempranas)

### Google Trends
- Señal de búsquedas por síntomas de enfermedades a nivel nacional.
- Granularidad mensual, interpolada a semanas ISO.
- Rango: 0–100 (índice relativo de búsqueda).

### RSS de medios colombianos
- Conteo de menciones epidemiológicas en feeds de El Tiempo, El Colombiano, El Heraldo, entre otros.
- Clasificación por enfermedad y relevancia mediante keywords.
- Granularidad semanal.

## Análisis exploratorio

- **Distribución temporal:** Ciclos epidémicos bianuales visibles para dengue (picos en semanas 10–20 y 40–50).
- **Cobertura geográfica:** 32 departamentos y >1100 municipios en SIVIGILA.
- **Enfermedades predominantes:** Dengue >80% de registros, seguido de malaria, chikungunya y zika.
- **Datos faltantes:** Periodo COVID (2020–2021) con caída significativa en notificaciones de arbovirosis. Tratado como dato real (la subnotificación es un fenómeno legítimo, no un error de datos).

## Dataset curado final

El pipeline PySpark (`curate_weekly_spark.py`) produce un dataset unificado con las siguientes dimensiones:
- **Clave primaria:** `(epi_year, epi_week, municipio_code, disease)`
- **Variables epidemiológicas:** `cases_total`
- **Variables climáticas:** `temp_avg_c`, `temp_min_c`, `temp_max_c`, `humidity_avg_pct`, `precipitation_mm`
- **Variables exógenas:** `vaccination_coverage_pct`, `rips_visits_total`, `mobility_index`, `mobility_hotspot_score`
- **Señales tempranas:** `trends_score`, `rss_mentions`
