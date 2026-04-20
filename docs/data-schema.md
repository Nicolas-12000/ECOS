# Dataset curado (schema v0)

## Objetivo
Definir la estructura del dataset curado semanal a nivel municipal y enfermedad. Este dataset es la base para entrenamiento, prediccion y visualizacion en Power BI. La definicion incluye todas las fuentes planteadas en el proyecto y como se integran.

## Fuentes consideradas
- SIVIGILA historico (4hyg-wa9d) -> base de casos por semana y territorio.
- Chikungunya (nu5z-zutz) -> fuente complementaria para validar eventos y enriquecer si aplica.
- Coberturas de vacunacion (6i25-2hdt) -> cobertura anual por departamento.
- RIPS vista agregada (5e6c-5p2c) -> atenciones por diagnostico, municipio y anio (para rips_visits_total).
- RIPS oficial (4k9h-8qiu) -> respaldo detallado, opcional si se necesita mas granularidad.
- Movilidad nacional (eh75-8ah6) -> origen/destino intermunicipal con pasajeros y despachos.
- Movilidad Medellin terminal (pfsr-mdyi) -> llegadas/salidas por ruta y fecha.
- Clima nacional IDEAM - Normales climatologicas (nsz2-kzcq) -> promedios mensuales/anuales por estacion y municipio.
- API clima actual (Open-Meteo) -> series diarias gratuitas; se agregan a semana y se persisten.
- Google Trends y RSS -> senales tempranas (scraping).
- Boletines INS -> contexto y validacion (scraping).

## Grano
- Una fila por semana epidemiologica, municipio y enfermedad.
- Semana definida por (epi_year, epi_week). Se recomienda agregar week_start_date para facilitar series de tiempo.

## Clave primaria
- epi_year (int)
- epi_week (int)
- municipio_code (string, DANE 5 digitos)
- disease (string)

## Columnas requeridas (basadas en SIVIGILA 4hyg-wa9d)
- epi_year (int): anio epidemiologico (ANO).
- epi_week (int): semana epidemiologica (SEMANA).
- week_start_date (date): fecha de inicio de semana (lunes).
- week_end_date (date): fecha fin de semana (domingo).
- departamento_code (string): DANE 2 digitos (COD_DPTO_O).
- departamento_name (string): nombre del departamento (Departamento_ocurrencia).
- municipio_code (string): DANE 5 digitos (COD_MUN_O).
- municipio_name (string): nombre del municipio (Municipio_ocurrencia).
- event_code (int): codigo del evento (COD_EVE).
- event_name (string): nombre del evento (Nombre_evento).
- disease (string): normalizado desde event_name (dengue | chikungunya | zika | malaria).
- cases_total (int): total de casos de la semana (conteo).

## Columnas ambientales (clima nacional - IDEAM normales)
- temp_avg_c (float): temperatura media (normal mensual) por municipio.
- temp_min_c (float): temperatura minima (normal mensual) por municipio.
- temp_max_c (float): temperatura maxima (normal mensual) por municipio.
- humidity_avg_pct (float): humedad relativa (normal mensual) por municipio.
- precipitation_mm (float): precipitacion (normal mensual) por municipio.
- climate_station (string): estacion usada para el municipio (si aplica).

Nota: nsz2-kzcq son normales climatologicas (1961-2020), no series diarias/semanales. Se recomienda mapear el valor mensual al rango de semanas del mes. Para clima actual se usa la API Open-Meteo (diario) y se agrega a semana con los mismos campos.

## Columnas opcionales (derivadas de otras fuentes)
- trends_score (float): indice de busqueda semanal por departamento.
- media_mentions (int): conteo de menciones en medios por semana.
- signals_score (float): score combinado de senales.
- vaccination_coverage_pct (float): cobertura anual por departamento (6i25-2hdt).
- rips_visits_total (int): atenciones totales CIE10 relacionadas a eventos.
- mobility_index (float): indice de movilidad o conectividad.
- outbreak_label (bool): 1 si supera umbral definido.

## Reglas de calidad
- No nulos en clave primaria.
- Valores negativos no permitidos.
- Para clima: permitir nulos si no hay estacion cercana.

## Nombre de archivo recomendado
- data/processed/curated_weekly.parquet
- data/processed/curated_weekly.csv (opcional para inspeccion)

## Tablas auxiliares (para integracion)

### Clima nacional - IDEAM normales (nsz2-kzcq)
- periodo (string)
- par_metro (string)
- c_digo (number)
- categoria (string)
- estaci_n (string)
- municipio (string)
- departamento (string)
- ao (int)
- altitud_m (float)
- longitud (float)
- latitud (float)
- ene..dic (float)
- anual (float)

Uso: filtrar por par_metro (precipitacion, temperatura max/min/media, humedad) y pivotear por mes/municipio. Asignar normales mensuales a semanas del mes.

### Vaccination annual (6i25-2hdt)
- vaccination_year (int)
- departamento_code (string)
- departamento_name (string)
- vaccine_name (string)
- vaccination_coverage_pct (float)

Uso: se agrega como feature anual por departamento. Se replica por semana al unir con curated_weekly.

### RIPS vista agregada (5e6c-5p2c)
- Departamento (string)
- Municipio (string)
- Año (int)
- TipoAtencion (string)
- Diagnostico (string)  # CIE10
- NumeroAtenciones (int)

Uso: filtrar por CIE10 de dengue, chikungunya, zika y malaria. Agregar por mes o semana y unir por municipio. Para unir con DANE se requiere una tabla de equivalencias de nombres.

### Movilidad (datasets definidos)
#### Nacional intermunicipal (eh75-8ah6)
- MUNICIPIO_ORIGEN_RUTA (string)
- MUNICIPIO_DESTINO_RUTA (string)
- FECHA_DESPACHO (date)
- DESPACHOS (int)
- PASAJEROS (int)

Uso: agregar por semana y municipio (entradas/salidas) para crear mobility_index nacional.

#### Medellin terminal (pfsr-mdyi)
- ruta_origen (string)
- Ruta Destino (string)
- fecha salida (date)
- fecha_llegada (date)
- pasajeros (int)

Uso: agregar semanal y usar como proxy urbano/terminal para Antioquia. Requiere normalizar nombres a DANE.

Nota: el dataset CGT de Bogota disponible en datos.gov.co es inventario de sensores sin conteos; se excluye hasta encontrar un endpoint de aforo.

### Signals weekly (scraping)
- epi_year (int)
- epi_week (int)
- departamento_code (string)
- trends_score (float)
- media_mentions (int)
- signals_score (float)

Uso: se une por semana y departamento.

## Mapeo de campos (SIVIGILA -> curado)
- ANO -> epi_year
- SEMANA -> epi_week
- COD_DPTO_O -> departamento_code
- Departamento_ocurrencia -> departamento_name
- COD_MUN_O -> municipio_code
- Municipio_ocurrencia -> municipio_name
- COD_EVE -> event_code
- Nombre_evento -> event_name
- conteo -> cases_total
- disease -> derivado por mapeo desde event_name

## Mapeo de campos (Vacunacion -> features)
- CodDepto -> departamento_code
- Departamento -> departamento_name
- Ano -> vaccination_year
- Biologico -> vaccine_name
- Cobertura_de_Vacunacion -> vaccination_coverage_pct

## Catalogo de eventos (SIVIGILA)
Se define un catalogo de eventos para mapear event_name a disease. Este catalogo se versiona en docs/event-catalog.csv y contiene:

- event_code
- event_name
- disease

Ejemplo:
- 210, DENGUE, dengue
- 220, DENGUE GRAVE, dengue
- 895, CHIKUNGUNYA, chikungunya
- 862, ZIKA, zika
- 830, MALARIA FALCIPARUM, malaria
- 831, MALARIA VIVAX, malaria

## Ejemplo de fila (CSV)
```
epi_year,epi_week,week_start_date,week_end_date,departamento_code,departamento_name,municipio_code,municipio_name,event_code,event_name,disease,cases_total,temp_avg_c,temp_min_c,temp_max_c,humidity_avg_pct,precipitation_mm
2024,12,2024-03-18,2024-03-24,05,Antioquia,05001,Medellin,210,DENGUE,dengue,32,24.6,20.1,28.3,68.2,44.0
```
