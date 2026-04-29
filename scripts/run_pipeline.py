#!/usr/bin/env python3
"""Master pipeline script to automate ECOS data processing.

Executes download, curation, validation, and (optional) loading steps.
"""

import argparse
import os
import sys
import subprocess
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"

def run_step(name: str, cmd: list[str], cwd: Path = REPO_ROOT):
    """Run a single pipeline step and handle errors."""
    print(f"\n{'='*60}")
    print(f" STEP: {name}")
    print(f"{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    
    start_time = time.time()
    try:
        result = subprocess.run(cmd, cwd=cwd, check=True)
        elapsed = time.time() - start_time
        print(f"\n[ok] {name} completed in {elapsed:.2f}s")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n[error] {name} failed with exit code {e.returncode}")
        return False

def main():
    parser = argparse.ArgumentParser(description="ECOS Data Pipeline Orchestrator")
    parser.add_argument("--skip-download", action="store_true", help="Skip data extraction")
    parser.add_argument("--skip-signals", action="store_true", help="Skip Trends/RSS scraping")
    parser.add_argument("--skip-curation", action="store_true", help="Skip Spark curation")
    parser.add_argument("--skip-validation", action="store_true", help="Skip data validation")
    parser.add_argument("--skip-load", action="store_true", help="Skip Supabase loading")
    parser.add_argument("--train-model", action="store_true", help="Train final model after curation")
    parser.add_argument("--db-url", default=os.getenv("SUPABASE_DB_URL"), help="Supabase DB URL")
    parser.add_argument("--force-download", action="store_true", help="Force re-download of datasets")
    
    args = parser.parse_args()
    python_exe = sys.executable

    # 1. Extraction
    if not args.skip_download:
        cmd = [python_exe, str(SCRIPTS_DIR / "download_datasets.py")]
        if args.force_download:
            cmd.append("--force")
        if not run_step("Data Extraction", cmd):
            sys.exit(1)
    else:
        print("\n[skip] Data Extraction")

    # 1b. Signals
    if not args.skip_signals:
        cmd = [python_exe, str(SCRIPTS_DIR / "fetch_signals.py")]
        if not run_step("Signals Scraping", cmd):
            sys.exit(1)
    else:
        print("\n[skip] Signals Scraping")

    # 2. Curation
    if not args.skip_curation:
        cmd = [python_exe, str(SCRIPTS_DIR / "curate_weekly_spark.py"), "--features", "vaccination"]
        if not run_step("Spark Curation", cmd):
            sys.exit(1)
    else:
        print("\n[skip] Spark Curation")

    # 3. Validation
    if not args.skip_validation:
        cmd = [python_exe, str(SCRIPTS_DIR / "validate_curated_spark.py")]
        if not run_step("Data Validation", cmd):
            sys.exit(1)
    else:
        print("\n[skip] Data Validation")

    # 3b. Model Training
    if args.train_model:
        cmd = [python_exe, str(REPO_ROOT / "models" / "model_final.py")]
        if not run_step("Model Training", cmd):
            sys.exit(1)

    # 4. Loading
    if not args.skip_load:
        if args.db_url:
            cmd = [python_exe, str(SCRIPTS_DIR / "load_curated_to_supabase.py"), "--truncate"]
            # We pass the DB URL via environment if not already there, or CLI doesn't support it directly in a clean way?
            # load_curated_to_supabase.py supports --database-url
            cmd.extend(["--database-url", args.db_url])
            if not run_step("Supabase Loading", cmd):
                sys.exit(1)
        else:
            print("\n[warn] Skipping Supabase Loading: No database URL provided (set SUPABASE_DB_URL or use --db-url)")
    else:
        print("\n[skip] Supabase Loading")

    print(f"\n{'='*60}")
    print(" PIPELINE COMPLETED SUCCESSFULLY")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
