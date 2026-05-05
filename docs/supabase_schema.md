# Esquema de Base de Datos (Supabase / PostgreSQL)

Este documento define la estructura oficial de la base de datos de ECOS desplegada en Supabase, diseñada bajo un modelo de **Esquema en Estrella (Star Schema)** optimizado para consultas analíticas rápidas desde Next.js, Plotly Dash y Power BI.

## Dependencias Requeridas
Para que el pipeline de ingesta a Supabase funcione (`scripts/supabase_pipeline.py`), el entorno debe contar con las siguientes dependencias de Python (ya incluidas en el `requirements.txt`):
* `psycopg[binary]` (Adaptador PostgreSQL moderno y de alto rendimiento)
* `pandas` (Manejo de dataframes)
* `python-dotenv` (Gestión de credenciales seguras)

## Arquitectura de Tablas

Las tablas deben crearse en Supabase (o cualquier PostgreSQL) en el siguiente orden para respetar las restricciones de llaves foráneas (Foreign Keys).

### 1. Dimensiones (Catálogos)

**`dim_departamentos`**
Contiene el catálogo DANE de departamentos.
* `departamento_code` (VARCHAR) - **Primary Key** (ej. "05" para Antioquia)
* `departamento_name` (VARCHAR)

**`dim_municipios`**
Contiene el catálogo DANE de municipios.
* `municipio_code` (VARCHAR) - **Primary Key** (ej. "05001" para Medellín)
* `departamento_code` (VARCHAR) - **Foreign Key** -> `dim_departamentos.departamento_code`
* `municipio_name` (VARCHAR)

---

### 2. Tablas de Hechos (Facts)

**`fact_avg_cases_annual`**
Histórico anual de promedios de casos para calcular alertas y líneas base.
* `epi_year` (INTEGER) - **Primary Key**
* `municipio_code` (VARCHAR) - **Primary Key**, **Foreign Key** -> `dim_municipios.municipio_code`
* `disease` (VARCHAR) - **Primary Key** (dengue, zika, chikungunya, malaria)
* `avg_cases` (FLOAT)

**`fact_climate_monthly`**
Normales climatológicas históricas del IDEAM.
* `municipio_code` (VARCHAR) - **Primary Key**, **Foreign Key** -> `dim_municipios.municipio_code`
* `month` (INTEGER) - **Primary Key** (1-12)
* `temp_avg_c` (FLOAT)
* `temp_min_c` (FLOAT)
* `temp_max_c` (FLOAT)
* `humidity_avg_pct` (FLOAT)
* `precipitation_mm` (FLOAT)

**`fact_vaccination_annual`**
Coberturas de vacunación departamental.
* `vaccination_year` (INTEGER) - **Primary Key**
* `departamento_code` (VARCHAR) - **Primary Key**, **Foreign Key** -> `dim_departamentos.departamento_code`
* `vaccine_name` (VARCHAR) - **Primary Key**
* `vaccination_coverage_pct` (FLOAT)

**`fact_core_weekly`** *(Tabla Principal)*
Contiene la sábana curada con el cruce semanal epidemiológico, señales de alerta y cruce climático. Es la tabla más pesada y la que consumen los dashboards.
* `epi_year` (INTEGER) - **Primary Key**
* `epi_week` (INTEGER) - **Primary Key**
* `municipio_code` (VARCHAR) - **Primary Key**, **Foreign Key** -> `dim_municipios.municipio_code`
* `disease` (VARCHAR) - **Primary Key**
* `week_start_date` (DATE)
* `week_end_date` (DATE)
* `cases_total` (INTEGER)
* `trends_score` (FLOAT) - Índice de búsqueda en Google Trends
* `trends_zscore` (FLOAT) - Desviación estándar de búsquedas
* `rss_mentions` (INTEGER) - Menciones en medios locales

---

### 3. Base de Conocimiento (IA)

**`knowledge_base`**
Utilizada por el sistema RAG (Chatbot) para responder preguntas usando vectorización (pgvector).
* `id` (UUID) - **Primary Key**
* `content` (TEXT) - Párrafo del documento o boletín
* `metadata` (JSONB) - Metadatos (fuente, fecha, url)
* `embedding` (VECTOR) - Representación vectorial matemática del texto

## Notas de Despliegue
1. Al ejecutar `python scripts/supabase_pipeline.py --truncate`, el script usa el comando `TRUNCATE TABLE ... CASCADE` para limpiar de forma segura todas las tablas antes de inyectar la carga semanal nueva mediante el comando super-rápido `COPY FROM STDIN`.
2. Supabase usa la variable de entorno `SUPABASE_DB_URL` configurada en el `.env` (puerto 6543 usando el pooler para soportar conexiones concurrentes altas).
