#!/usr/bin/env python3

import argparse
import json
import random
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

DEFAULT_CONFIG = Path(__file__).with_name("datasets.json")
CHUNK_SIZE = 1024 * 1024


def load_config(path: Path) -> tuple[dict, list[dict]]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    defaults = data.get("defaults", {})
    datasets = data.get("datasets", [])
    return defaults, datasets


def build_download_url(dataset: dict, defaults: dict) -> str | None:
    if dataset.get("type") == "socrata":
        host = dataset.get("host", defaults.get("host", "www.datos.gov.co"))
        file_format = dataset.get("format", defaults.get("format", "csv"))
        dataset_id = dataset.get("id")
        if not dataset_id:
            return None
        return f"https://{host}/api/views/{dataset_id}/rows.{file_format}?accessType=DOWNLOAD"
    return dataset.get("url")


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def should_skip(path: Path, force: bool) -> bool:
    if force:
        return False
    return path.exists() and path.stat().st_size > 0


def wait_for_host(host: str, last_by_host: dict, min_delay: float) -> None:
    last_time = last_by_host.get(host)
    if last_time is None:
        return
    elapsed = time.time() - last_time
    if elapsed < min_delay:
        time.sleep(min_delay - elapsed)


def download_url(url: str, dest: Path, defaults: dict, last_by_host: dict) -> None:
    min_delay = float(defaults.get("min_delay_seconds", 1.5))
    timeout = float(defaults.get("timeout_seconds", 120))
    max_retries = int(defaults.get("max_retries", 5))
    user_agent = defaults.get("user_agent", "ecos-datasets/1.0")

    parsed = urlparse(url)
    host = parsed.netloc
    tmp_path = dest.with_suffix(dest.suffix + ".partial")

    for attempt in range(max_retries):
        wait_for_host(host, last_by_host, min_delay)
        request = urllib.request.Request(url, headers={"User-Agent": user_agent})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                last_by_host[host] = time.time()
                ensure_parent_dir(tmp_path)
                with tmp_path.open("wb") as handle:
                    while True:
                        chunk = response.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        handle.write(chunk)
            tmp_path.replace(dest)
            return
        except urllib.error.HTTPError as exc:
            last_by_host[host] = time.time()
            if exc.code in (429, 500, 502, 503, 504):
                backoff = (2 ** attempt) + random.random()
                time.sleep(backoff)
                continue
            raise
        except Exception:
            last_by_host[host] = time.time()
            if attempt < max_retries - 1:
                backoff = (2 ** attempt) + random.random()
                time.sleep(backoff)
                continue
            raise


def iter_selected(datasets: list[dict], only_keys: set[str] | None) -> list[dict]:
    if not only_keys:
        return datasets
    return [dataset for dataset in datasets if dataset.get("key") in only_keys]


def main() -> int:
    parser = argparse.ArgumentParser(description="Download datasets defined in scripts/datasets.json")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Path to datasets.json")
    parser.add_argument("--only", nargs="*", help="Download only datasets matching these keys")
    parser.add_argument("--force", action="store_true", help="Re-download even if files exist")
    args = parser.parse_args()

    config_path = Path(args.config).expanduser().resolve()
    defaults, datasets = load_config(config_path)
    only_keys = set(args.only) if args.only else None

    repo_root = Path(__file__).resolve().parents[1]
    last_by_host: dict[str, float] = {}

    for dataset in iter_selected(datasets, only_keys):
        key = dataset.get("key", "unknown")
        dtype = dataset.get("type", "")

        if dtype == "manual":
            output = dataset.get("output", "")
            url = dataset.get("url", "")
            print(f"[manual] {key}: {url} -> {output}")
            continue

        url = build_download_url(dataset, defaults)
        if not url:
            print(f"[skip] {key}: missing download URL")
            continue

        output = dataset.get("output")
        if not output:
            print(f"[skip] {key}: missing output path")
            continue

        dest = (repo_root / output).resolve()
        if should_skip(dest, args.force):
            print(f"[skip] {key}: exists -> {dest}")
            continue

        print(f"[download] {key}: {url} -> {dest}")
        try:
            download_url(url, dest, defaults, last_by_host)
        except Exception as exc:
            print(f"[error] {key}: {exc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
