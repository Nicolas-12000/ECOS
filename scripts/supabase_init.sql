-- ==============================================================================
-- SCRIPT DE INICIALIZACIÓN: ECOS BASE DE DATOS (SUPABASE / POSTGRESQL)
-- ==============================================================================
-- Instrucciones: Copia y pega todo este código en el "SQL Editor" de Supabase
-- y dale a "Run" (Ejecutar). 
-- 
-- NOTA: El comando 'IF NOT EXISTS' asegura que si la tabla ya está creada, 
-- no se romperá ni se borrará la data actual, pero creará lo que haga falta.
-- ==============================================================================

-- 1. Habilitar extensión para Inteligencia Artificial (Vectores RAG)
CREATE EXTENSION IF NOT EXISTS vector;

-- ==========================================
-- DIMENSIONES (Catálogos)
-- ==========================================

-- Catálogo de Departamentos
CREATE TABLE IF NOT EXISTS public.dim_departamentos (
    departamento_code VARCHAR(2) PRIMARY KEY,
    departamento_name VARCHAR(255) NOT NULL
);

-- Catálogo de Municipios
CREATE TABLE IF NOT EXISTS public.dim_municipios (
    municipio_code VARCHAR(5) PRIMARY KEY,
    departamento_code VARCHAR(2) REFERENCES public.dim_departamentos(departamento_code),
    municipio_name VARCHAR(255) NOT NULL
);

-- ==========================================
-- TABLAS DE HECHOS (Métricas)
-- ==========================================

-- Promedio Anual de Casos (Por Departamento)
CREATE TABLE IF NOT EXISTS public.fact_avg_cases_annual (
    epi_year INTEGER,
    departamento_code VARCHAR(2) REFERENCES public.dim_departamentos(departamento_code),
    disease VARCHAR(50),
    avg_weekly_cases DOUBLE PRECISION,
    PRIMARY KEY (epi_year, departamento_code, disease)
);

-- Clima Histórico Mensual (IDEAM - Por Departamento)
CREATE TABLE IF NOT EXISTS public.fact_climate_monthly (
    departamento_code VARCHAR(2) REFERENCES public.dim_departamentos(departamento_code),
    month_num INTEGER,
    temp_avg_c DOUBLE PRECISION,
    temp_min_c DOUBLE PRECISION,
    temp_max_c DOUBLE PRECISION,
    precipitation_mm DOUBLE PRECISION,
    PRIMARY KEY (departamento_code, month_num)
);

-- Cobertura de Vacunación Anual (Por Departamento)
CREATE TABLE IF NOT EXISTS public.fact_vaccination_annual (
    epi_year INTEGER,
    departamento_code VARCHAR(2) REFERENCES public.dim_departamentos(departamento_code),
    vaccination_coverage_pct DOUBLE PRECISION,
    PRIMARY KEY (epi_year, departamento_code)
);

-- Tabla Core Semanal (La sábana principal con el cruce de modelos e IA)
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
    rss_mentions INTEGER,
    signals_score DOUBLE PRECISION,
    PRIMARY KEY (epi_year, epi_week, municipio_code, disease)
);

-- ==========================================
-- BASE DE CONOCIMIENTO (Chatbot RAG)
-- ==========================================

-- Tabla para almacenar los embeddings de documentos y boletines
CREATE TABLE IF NOT EXISTS public.knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    metadata JSONB,
    embedding VECTOR(384) -- Ajustado al modelo sentence-transformers/all-MiniLM-L6-v2 usado en el proyecto
);

-- ==========================================
-- MANTENIMIENTO: Actualización de permisos
-- ==========================================
-- Asegurarnos de que el API anónimo de Supabase (PostgREST) pueda leer los datos
-- para que el frontend Next.js o los Dashboards puedan consumirlos si es necesario.
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO authenticated;
