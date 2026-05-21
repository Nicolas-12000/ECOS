-- ==============================================================================
-- ECOS Supabase init (Part 1): Extensions + Dimensions
-- ==============================================================================

SET statement_timeout = '10min';

-- 1. Habilitar extension para vectores
CREATE EXTENSION IF NOT EXISTS vector;

-- ==========================================
-- DIMENSIONES (Catalogos)
-- ==========================================

CREATE TABLE IF NOT EXISTS public.dim_departamentos (
    departamento_code VARCHAR(2) PRIMARY KEY,
    departamento_name VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS public.dim_municipios (
    municipio_code VARCHAR(5) PRIMARY KEY,
    departamento_code VARCHAR(2) REFERENCES public.dim_departamentos(departamento_code),
    municipio_name VARCHAR(255) NOT NULL
);

-- ==========================================
-- DIMENSIONS schema alignment (safe for existing DBs)
-- ==========================================

ALTER TABLE public.dim_departamentos
    ADD COLUMN IF NOT EXISTS region_norm TEXT,
    ADD COLUMN IF NOT EXISTS latitude DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS longitude DOUBLE PRECISION;
