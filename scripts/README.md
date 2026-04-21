# Scripts

Utility scripts for data ingestion, training, and evaluation.

- download_datasets.py: Download raw datasets defined in scripts/datasets.json (some are manual).
- datasets.json: Registry of raw datasets and download URLs.
- curate_weekly_v0_spark.py: PySpark pipeline for curated_weekly_v0 (SIVIGILA + IDEAM normals).
- curate_weekly_v1_spark.py: PySpark pipeline for curated_weekly_v1 (adds vacunacion, movilidad, RIPS view).
- validate_curated_v0_spark.py: Validation checks for curated_weekly_v0 output.
- version_snapshot.py: Generate snapshot hash/manifest for curated outputs.
