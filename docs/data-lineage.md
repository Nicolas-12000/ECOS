# Data Lineage (ECOS)

## Objetivo
Dejar trazabilidad clara de como se construye el dataset curado v0 desde las fuentes originales.

## Fuentes (raw)
- SIVIGILA historico: data/raw/sivigila_4hyg-wa9d.csv
- IDEAM normales climatologicas: data/raw/clima_normales_ideam_nsz2-kzcq.csv

## Transformaciones principales
1. Ingesta con PySpark (scripts/curate_weekly_spark.py --version v0).
2. Limpieza: trim de llaves, filtros de semana/anio validos.
3. Agregacion semanal por municipio y enfermedad.
4. Enriquecimiento con clima IDEAM por municipio y mes.
5. Salida en Parquet + CSV curados.

## Salidas (curated v0)
- data/processed/curated_weekly_v0_parquet/
- data/processed/curated_weekly_v0_csv/

## Versionado y snapshot
El snapshot se genera con:

```
python scripts/version_snapshot.py
```

Salida:
- docs/data-snapshots.json (hash + lista de archivos)

## Validaciones
- scripts/validate_curated_v0_spark.py

## Nota
Los archivos de data/processed no se versionan en git; el snapshot permite reproducir y auditar la version de datos usada.
