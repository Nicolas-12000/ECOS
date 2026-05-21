# Scripts

Utility scripts for data ingestion, training, and evaluation.

- download_datasets.py: Download raw datasets defined in scripts/datasets.json (some are manual).
- datasets.json: Registry of raw datasets and download URLs.
- curate_weekly_spark.py: PySpark pipeline for curated_weekly (single canonical output in data/processed/curated_weekly_*).
- validate_curated_spark.py: Validation checks for curated_weekly output.
- version_snapshot.py: Generate snapshot hash/manifest for curated outputs.
