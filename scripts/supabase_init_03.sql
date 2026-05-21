-- ==============================================================================
-- ECOS Supabase init (Part 3): Knowledge Base + Grants
-- ==============================================================================

SET statement_timeout = '10min';

CREATE TABLE IF NOT EXISTS public.knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    metadata JSONB,
    embedding VECTOR(384)
);

-- ==========================================
-- RAW SCRAPED TABLES (staging)
-- ==========================================

CREATE TABLE IF NOT EXISTS public.raw_signals_rss (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fetched_at TIMESTAMPTZ DEFAULT now(),
    week_start_date DATE,
    disease TEXT,
    departamento_code VARCHAR(2),
    rss_mentions INTEGER
);

CREATE TABLE IF NOT EXISTS public.raw_signals_trends (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fetched_at TIMESTAMPTZ DEFAULT now(),
    week_start_date DATE,
    disease TEXT,
    departamento_code VARCHAR(2),
    trends_score DOUBLE PRECISION,
    trends_zscore DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS public.raw_open_meteo_weekly (
    departamento_code VARCHAR(2),
    week_start_date DATE,
    temp_max_c DOUBLE PRECISION,
    temp_min_c DOUBLE PRECISION,
    temp_avg_c DOUBLE PRECISION,
    precipitation_mm DOUBLE PRECISION,
    humidity_avg_pct DOUBLE PRECISION,
    fetched_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.raw_rss_articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fetched_at TIMESTAMPTZ DEFAULT now(),
    source TEXT,
    title TEXT,
    summary TEXT,
    link TEXT,
    published_at TIMESTAMPTZ,
    diseases JSONB,
    relevance_score DOUBLE PRECISION
);

-- ==========================================
-- SCRAPING schema alignment (safe for existing DBs)
-- ==========================================

ALTER TABLE public.raw_signals_trends
    ADD COLUMN IF NOT EXISTS week_start_date DATE,
    ADD COLUMN IF NOT EXISTS disease TEXT,
    ADD COLUMN IF NOT EXISTS departamento_code VARCHAR(2),
    ADD COLUMN IF NOT EXISTS trends_score DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS trends_zscore DOUBLE PRECISION;

ALTER TABLE public.raw_signals_rss
    ADD COLUMN IF NOT EXISTS week_start_date DATE,
    ADD COLUMN IF NOT EXISTS disease TEXT,
    ADD COLUMN IF NOT EXISTS departamento_code VARCHAR(2),
    ADD COLUMN IF NOT EXISTS rss_mentions INTEGER;

ALTER TABLE public.raw_open_meteo_weekly
    ADD COLUMN IF NOT EXISTS temp_max_c DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS temp_min_c DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS temp_avg_c DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS precipitation_mm DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS humidity_avg_pct DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS fetched_at TIMESTAMPTZ DEFAULT now();

ALTER TABLE public.raw_open_meteo_weekly
    DROP CONSTRAINT IF EXISTS raw_open_meteo_weekly_departamento_code_fkey;

ALTER TABLE public.raw_rss_articles
    ADD COLUMN IF NOT EXISTS source TEXT,
    ADD COLUMN IF NOT EXISTS title TEXT,
    ADD COLUMN IF NOT EXISTS summary TEXT,
    ADD COLUMN IF NOT EXISTS link TEXT,
    ADD COLUMN IF NOT EXISTS published_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS diseases JSONB,
    ADD COLUMN IF NOT EXISTS relevance_score DOUBLE PRECISION;

GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO authenticated;
