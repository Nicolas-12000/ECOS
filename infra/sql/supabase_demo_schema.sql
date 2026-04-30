-- Supabase demo schema for ECOS
-- Apply with: psql "$SUPABASE_DB_URL" -f infra/sql/supabase_demo_schema.sql

create extension if not exists pgcrypto;

--------------------------------------------------------------------------------
-- 1. DIMENSION TABLES
--------------------------------------------------------------------------------

create table if not exists public.dim_departamentos (
    departamento_code text primary key,
    departamento_name text not null,
    region_norm text,
    latitude double precision,
    longitude double precision
);

create table if not exists public.dim_municipios (
    municipio_code text primary key,
    municipio_name text not null,
    departamento_code text not null references public.dim_departamentos(departamento_code)
);

create index if not exists idx_dim_municipios_depto on public.dim_municipios (departamento_code);

--------------------------------------------------------------------------------
-- 2. FACT TABLES
--------------------------------------------------------------------------------

create table if not exists public.fact_avg_cases_annual (
    departamento_code text not null references public.dim_departamentos(departamento_code),
    epi_year integer not null,
    disease text not null,
    avg_weekly_cases double precision,
    primary key (departamento_code, epi_year, disease)
);

create table if not exists public.fact_climate_monthly (
    month_num integer not null,
    precipitation_mm double precision,
    humidity_avg_pct double precision,
    temp_min_c double precision,
    temp_avg_c double precision,
    temp_max_c double precision,
    departamento_code text not null references public.dim_departamentos(departamento_code),
    primary key (departamento_code, month_num)
);

create table if not exists public.fact_vaccination_annual (
    departamento_code text not null references public.dim_departamentos(departamento_code),
    epi_year integer not null,
    vaccination_coverage_pct double precision,
    primary key (departamento_code, epi_year)
);

create table if not exists public.fact_core_weekly (
    epi_year integer not null,
    epi_week integer not null,
    week_start_date date not null,
    week_end_date date,
    month_num integer,
    departamento_code text not null references public.dim_departamentos(departamento_code),
    municipio_code text not null references public.dim_municipios(municipio_code),
    event_code integer,
    disease text not null,
    cases_total integer not null default 0,
    temp_avg_c double precision,
    temp_min_c double precision,
    temp_max_c double precision,
    humidity_avg_pct double precision,
    precipitation_mm double precision,
    vaccination_coverage_pct double precision,
    rips_visits_total double precision,
    mobility_index double precision,
    trends_score double precision,
    rss_mentions double precision,
    signals_score double precision,
    inserted_at timestamptz not null default now(),
    primary key (epi_year, epi_week, municipio_code, disease)
);

create index if not exists idx_fact_core_weekly_date on public.fact_core_weekly (week_start_date);
create index if not exists idx_fact_core_weekly_depto on public.fact_core_weekly (departamento_code);
create index if not exists idx_fact_core_weekly_disease on public.fact_core_weekly (disease);

--------------------------------------------------------------------------------
-- 3. PREDICTIONS TABLE
--------------------------------------------------------------------------------

create table if not exists public.predictions_demo (
    id uuid primary key default gen_random_uuid(),
    created_at timestamptz not null default now(),
    epi_year integer not null,
    epi_week integer not null,
    week_start_date date,
    disease text not null,
    municipio_code text not null,
    departamento_code text,
    predicted_cases double precision not null,
    outbreak_flag boolean not null,
    outbreak_threshold double precision not null default 5.0,
    model_version text not null default 'baseline'
);

create index if not exists idx_predictions_demo_lookup
    on public.predictions_demo (disease, departamento_code, municipio_code, epi_year, epi_week);

--------------------------------------------------------------------------------
-- 4. ROW LEVEL SECURITY (RLS)
--------------------------------------------------------------------------------

-- Demo mode: allow read for anon if using public dashboard.
alter table public.dim_departamentos enable row level security;
alter table public.dim_municipios enable row level security;
alter table public.fact_avg_cases_annual enable row level security;
alter table public.fact_climate_monthly enable row level security;
alter table public.fact_vaccination_annual enable row level security;
alter table public.fact_core_weekly enable row level security;
alter table public.predictions_demo enable row level security;

do $$
declare
    t text;
begin
    for t in
        select unnest(array[
            'dim_departamentos',
            'dim_municipios',
            'fact_avg_cases_annual',
            'fact_climate_monthly',
            'fact_vaccination_annual',
            'fact_core_weekly',
            'predictions_demo'
        ])
    loop
        if not exists (
            select 1 from pg_policies
            where schemaname = 'public' and tablename = t and policyname = 'public_read_' || t
        ) then
            execute format('create policy public_read_%I on public.%I for select using (true)', t, t);
        end if;
    end loop;
end $$;

--------------------------------------------------------------------------------
-- 5. KNOWLEDGE BASE FOR RAG
--------------------------------------------------------------------------------

create table if not exists public.knowledge_base (
    id uuid primary key default gen_random_uuid(),
    title text not null,
    content text not null,
    source_path text,
    metadata jsonb default '{}'::jsonb,
    created_at timestamptz not null default now()
);

alter table public.knowledge_base enable row level security;

create policy public_read_knowledge_base on public.knowledge_base
    for select using (true);

-- Full-text search index for Spanish
create index if not exists idx_knowledge_base_content 
    on public.knowledge_base using gin(to_tsvector('spanish', content));
