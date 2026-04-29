-- Supabase demo schema for ECOS
-- Apply with: psql "$SUPABASE_DB_URL" -f infra/sql/supabase_demo_schema.sql

create extension if not exists pgcrypto;

create table if not exists public.curated_weekly (
    epi_year integer not null,
    epi_week integer not null,
    week_start_date date not null,
    week_end_date date,
    departamento_code text not null,
    departamento_name text,
    municipio_code text not null,
    municipio_name text,
    event_code integer,
    event_name text,
    disease text not null,
    cases_total integer not null default 0,
    temp_avg_c double precision not null default 0,
    temp_min_c double precision not null default 0,
    temp_max_c double precision not null default 0,
    precipitation_mm double precision not null default 0,
    vaccination_coverage_pct double precision not null default 0,
    inserted_at timestamptz not null default now(),
    primary key (epi_year, epi_week, municipio_code, disease)
);

create index if not exists idx_curated_weekly_date on public.curated_weekly (week_start_date);
create index if not exists idx_curated_weekly_depto on public.curated_weekly (departamento_code);
create index if not exists idx_curated_weekly_disease on public.curated_weekly (disease);

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

-- Demo mode: allow read for anon if using public dashboard.
alter table public.curated_weekly enable row level security;
alter table public.predictions_demo enable row level security;

do $$
begin
    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'curated_weekly' and policyname = 'public_read_curated_weekly'
    ) then
        create policy public_read_curated_weekly
        on public.curated_weekly
        for select
        using (true);
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'public' and tablename = 'predictions_demo' and policyname = 'public_read_predictions_demo'
    ) then
        create policy public_read_predictions_demo
        on public.predictions_demo
        for select
        using (true);
    end if;
end $$;
