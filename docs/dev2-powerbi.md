# Guía rápida para Dev 2 (Power BI)

## Dónde están los datos
- Curado canonical (Parquet): data/processed/curated_weekly_parquet/
- Curado canonical (CSV): data/processed/curated_weekly_csv/

> Nota: data/processed esta en .gitignore. Si no existe localmente, corre el pipeline PySpark para generarlo.

## Cómo generar el curado canonical (si no existe)
1. Descarga los datasets:

```
python scripts/download_datasets.py
```

2. Asegura que Spark este activo:

```
docker compose -f infra/docker-compose.spark.yml up -d
```

3. Ejecuta:

```
docker compose -f infra/docker-compose.spark.yml exec spark-master \
  /opt/spark/bin/spark-submit /opt/spark/work/scripts/curate_weekly_spark.py \
  --version full \
  --sivigila /opt/spark/work/data/raw/sivigila_4hyg-wa9d.csv \
  --clima /opt/spark/work/data/raw/clima_normales_ideam_nsz2-kzcq.csv \
  --out-parquet /opt/spark/work/data/processed/curated_weekly_parquet \
  --out-csv /opt/spark/work/data/processed/curated_weekly_csv
```

4. Copia los outputs a tu workspace si los generaste en el contenedor:

```
  docker cp spark-master:/opt/spark/work/data/processed/curated_weekly_csv data/processed/curated_weekly_csv
```

## Importar en Power BI
1. Usa el CSV en data/processed/curated_weekly_csv/ (solo hay un part file).
2. Si se usa PostgreSQL local, conecta con el conector PostgreSQL y apunta al esquema/dataset curado.
3. Columnas clave:
   - epi_year, epi_week
   - week_start_date, week_end_date
   - departamento_code, departamento_name
   - municipio_code, municipio_name
   - disease, cases_total
   - temp_avg_c, temp_min_c, temp_max_c, humidity_avg_pct, precipitation_mm

## Layout recomendado
- Mapa por departamento
- Serie temporal de casos
- Filtros por enfermedad, departamento, rango de fechas

## Validación rápida
- Verifica que epi_week esté entre 1 y 53.
- Verifica que cases_total no tenga negativos.
