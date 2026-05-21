#!/usr/bin/env python3

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = "curated_weekly"
DEFAULT_OUTPUT = REPO_ROOT / "docs/data-snapshots.json"
DEFAULT_PATHS = [
    REPO_ROOT / "data/processed/curated_weekly_parquet",
    REPO_ROOT / "data/processed/curated_weekly_csv",
]
CHUNK_SIZE = 1024 * 1024


def iter_files(paths: list[Path]) -> list[Path]:
    files = []
    for path in paths:
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            for root, _, filenames in os.walk(path):
                for name in filenames:
                    if name.startswith("_"):
                        continue
                    files.append(Path(root) / name)
    return sorted(files)


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(CHUNK_SIZE)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Create data snapshot hash manifest")
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--paths", nargs="*", default=[str(p) for p in DEFAULT_PATHS])
    args = parser.parse_args()

    paths = [Path(p).expanduser().resolve() for p in args.paths]
    files = iter_files(paths)
    if not files:
        print("[error] no files found for snapshot")
        return 1

    manifest_files = []
    total_bytes = 0
    for path in files:
        size = path.stat().st_size
        total_bytes += size
        manifest_files.append(
            {
                "path": str(path.relative_to(REPO_ROOT)),
                "bytes": size,
                "sha256": sha256_file(path),
            }
        )

    fingerprint_lines = [
        f"{item['path']}|{item['bytes']}|{item['sha256']}" for item in manifest_files
    ]
    dataset_hash = hashlib.sha256("\n".join(fingerprint_lines).encode("utf-8")).hexdigest()

    payload = {
        "dataset": args.dataset,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "paths": [str(p.relative_to(REPO_ROOT)) for p in paths],
        "file_count": len(manifest_files),
        "total_bytes": total_bytes,
        "dataset_hash": dataset_hash,
        "files": manifest_files,
    }

    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"[ok] snapshot saved -> {output_path}")
    print(f"[ok] dataset hash -> {dataset_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
