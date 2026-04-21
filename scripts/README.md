# Scripts

Utility scripts for data ingestion, training, and evaluation.

- download_datasets.py: Download raw datasets defined in scripts/datasets.json (some are manual).
- datasets.json: Registry of raw datasets and download URLs.
- curate_weekly_spark.py: PySpark pipeline for curated_weekly v0/v1 (use --version and --features).
- validate_curated_v0_spark.py: Validation checks for curated_weekly_v0 output.
- version_snapshot.py: Generate snapshot hash/manifest for curated outputs.
