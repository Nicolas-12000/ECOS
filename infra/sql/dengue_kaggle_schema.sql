-- Schema for Dengue Kaggle dataset
-- Apply with: psql "$SUPABASE_DB_URL" -f infra/sql/dengue_kaggle_schema.sql

create schema if not exists analytics;

create table if not exists analytics.dengue_kaggle_dataset (
    ano integer not null,
    semana integer not null,
    departamento text,
    municipio text not null,
    enfermedad text not null default 'Dengue',
    casos_totales integer not null default 0,
    temperatura_promedio double precision,
    precipitacion_promedio double precision,
    calidad_aire_promedio double precision,
    vacunacion text,
    cantidad_hospitales integer,
    latitud double precision,
    longitud double precision,
    brote text,
    -- Added fields that might be specific to this dataset
    poblacion integer,
    incidencia double precision,
    primary key (ano, semana, municipio, enfermedad)
);

create index if not exists idx_dengue_kaggle_departamento
    on analytics.dengue_kaggle_dataset (departamento);

create index if not exists idx_dengue_kaggle_municipio
    on analytics.dengue_kaggle_dataset (municipio);

create index if not exists idx_dengue_kaggle_ano_semana
    on analytics.dengue_kaggle_dataset (ano, semana);
