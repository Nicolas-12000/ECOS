-- ==============================================================================
-- ECOS Supabase init (Part 2): Fact Tables
-- ==============================================================================

SET statement_timeout = '10min';

CREATE TABLE IF NOT EXISTS public.fact_avg_cases_annual (
    epi_year INTEGER,
    departamento_code VARCHAR(2) REFERENCES public.dim_departamentos(departamento_code),
    disease VARCHAR(50),
    avg_weekly_cases DOUBLE PRECISION,
    PRIMARY KEY (epi_year, departamento_code, disease)
);

CREATE TABLE IF NOT EXISTS public.fact_climate_monthly (
    departamento_code VARCHAR(2) REFERENCES public.dim_departamentos(departamento_code),
    month_num INTEGER,
    temp_avg_c DOUBLE PRECISION,
    temp_min_c DOUBLE PRECISION,
    temp_max_c DOUBLE PRECISION,
    precipitation_mm DOUBLE PRECISION,
    PRIMARY KEY (departamento_code, month_num)
);

CREATE TABLE IF NOT EXISTS public.fact_vaccination_annual (
    epi_year INTEGER,
    departamento_code VARCHAR(2) REFERENCES public.dim_departamentos(departamento_code),
    vaccination_coverage_pct DOUBLE PRECISION,
    PRIMARY KEY (epi_year, departamento_code)
);

CREATE TABLE IF NOT EXISTS public.fact_core_weekly (
    epi_year INTEGER,
    epi_week INTEGER,
    week_start_date DATE,
    week_end_date DATE,
    month_num INTEGER,
    departamento_code VARCHAR(2) REFERENCES public.dim_departamentos(departamento_code),
    municipio_code VARCHAR(5) REFERENCES public.dim_municipios(municipio_code),
    event_code INTEGER,
    disease VARCHAR(50),
    cases_total INTEGER,
    temp_avg_c DOUBLE PRECISION,
    temp_min_c DOUBLE PRECISION,
    temp_max_c DOUBLE PRECISION,
    precipitation_mm DOUBLE PRECISION,
    temp_avg_c_actual DOUBLE PRECISION,
    temp_min_c_actual DOUBLE PRECISION,
    temp_max_c_actual DOUBLE PRECISION,
    precipitation_mm_actual DOUBLE PRECISION,
    vaccination_coverage_pct DOUBLE PRECISION,
    rips_visits_total DOUBLE PRECISION,
    mobility_in DOUBLE PRECISION,
    mobility_out DOUBLE PRECISION,
    mobility_index DOUBLE PRECISION,
    trends_score DOUBLE PRECISION,
    rss_mentions DOUBLE PRECISION,
    signals_score DOUBLE PRECISION,
    PRIMARY KEY (epi_year, epi_week, municipio_code, disease)
);

-- ==========================================
-- FACTS schema alignment (safe for existing DBs)
-- ==========================================

ALTER TABLE public.fact_core_weekly
    ALTER COLUMN rss_mentions TYPE DOUBLE PRECISION
    USING rss_mentions::double precision;
