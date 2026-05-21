-- Schema for ANOVA dataset in Supabase/Postgres
-- Apply with: psql "$SUPABASE_DB_URL" -f infra/sql/anova_dataset_schema.sql

create schema if not exists analytics;

create table if not exists analytics.anova_dataset (
    ano integer not null,
    semana integer not null,
    departamento text not null,
    municipio text not null,
    enfermedad text not null,
    casos_totales integer not null,
    temperatura_promedio double precision,
    precipitacion_promedio double precision,
    calidad_aire_promedio double precision,
    vacunacion text,
    cantidad_hospitales integer,
    latitud double precision,
    longitud double precision,
    brote text,
    primary key (ano, semana, departamento, municipio, enfermedad)
);

create index if not exists idx_anova_dataset_enfermedad
    on analytics.anova_dataset (enfermedad);

create index if not exists idx_anova_dataset_departamento
    on analytics.anova_dataset (departamento);

create index if not exists idx_anova_dataset_municipio
    on analytics.anova_dataset (municipio);

create index if not exists idx_anova_dataset_brote
    on analytics.anova_dataset (brote);

create index if not exists idx_anova_dataset_ano_semana
    on analytics.anova_dataset (ano, semana);
