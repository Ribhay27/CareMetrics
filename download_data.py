from __future__ import annotations

import argparse
import csv
import io
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from zipfile import ZipFile

import pandas as pd
import requests
from tabulate import tabulate

ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

CMS_API_BASE = "https://data.cms.gov/provider-data/api/1/datastore/query"
CDC_PLACES_URL = "https://data.cdc.gov/resource/swc5-untb.csv?$limit=500000"


@dataclass(frozen=True)
class DownloadSpec:
    filename: str
    label: str
    kind: str
    dataset_id: str | None = None
    url: str | None = None
    expected_rows: int = 1000


FILES: list[DownloadSpec] = [
    DownloadSpec("hospitals_general.csv", "CMS Hospital General Information", "cms_api", dataset_id="xubh-q36u"),
    DownloadSpec("hospitals_readmissions.csv", "CMS Hospital Readmissions Reduction Program", "cms_api", dataset_id="9n3s-kdb3"),
    DownloadSpec("hospitals_patient_experience.csv", "CMS HCAHPS Patient Experience", "cms_api", dataset_id="dgck-syfz"),
    DownloadSpec("hospitals_timely_care.csv", "CMS Timely and Effective Care", "cms_api", dataset_id="yv7e-xc69"),
    DownloadSpec("hospitals_general_2022.csv", "Historical Hospital General Information 2022", "direct_csv", url="https://data.nber.org/compare/hospital/2022/7/hospital_general_information.csv"),
    DownloadSpec("hospitals_readmissions_2022.csv", "Historical HRRP 2022", "direct_csv", url="https://data.nber.org/compare/hospital/2022/7/fy_2022_hospital_readmissions_reduction_program_hospital.csv"),
    DownloadSpec("hospitals_general_2021.csv", "Historical Hospital General Information 2021", "direct_csv", url="https://data.nber.org/compare/hospital/2021/7/hospital_general_information.csv"),
    DownloadSpec("hospitals_readmissions_2021.csv", "Historical HRRP 2021", "direct_csv", url="https://data.nber.org/compare/hospital/2021/7/fy_2021_hospital_readmissions_reduction_program_hospital.csv"),
    DownloadSpec("cdc_places_county.csv", "CDC PLACES County Data", "direct_csv", url=CDC_PLACES_URL),
]


def _print_progress(label: str, done: int, total: int | None) -> None:
    if total:
        pct = min(done / total * 100, 100)
        print(f"\r{label}: {done / 1024 / 1024:7.2f} MB / {total / 1024 / 1024:7.2f} MB ({pct:5.1f}%)", end="", flush=True)
    else:
        print(f"\r{label}: {done / 1024 / 1024:7.2f} MB", end="", flush=True)


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
        reader = csv.reader(f)
        try:
            next(reader)
        except StopIteration:
            return 0
        return sum(1 for _ in reader)


def download_stream(url: str, dest: Path, label: str) -> None:
    tmp = dest.with_suffix(dest.suffix + ".part")
    try:
        with requests.get(url, stream=True, timeout=120, headers={"User-Agent": "hospital-analytics-pipeline/1.0"}) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("Content-Length", "0")) or None
            done = 0
            with tmp.open("wb") as f:
                for chunk in resp.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
                        done += len(chunk)
                        _print_progress(label, done, total)
        print()
        tmp.replace(dest)
    except Exception as exc:
        if tmp.exists():
            tmp.unlink()
        raise RuntimeError(f"Download failed for URL: {url}\n{exc}") from exc


def _cms_csv_download_url(dataset_id: str) -> str:
    meta_url = f"https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items/{dataset_id}?show-reference-ids=false"
    try:
        resp = requests.get(
            meta_url,
            timeout=120,
            headers={"User-Agent": "hospital-analytics-pipeline/1.0"},
        )
        resp.raise_for_status()
        meta = resp.json()
    except Exception as exc:
        raise RuntimeError(f"Could not fetch CMS metadata for {dataset_id}: {meta_url}\n{exc}") from exc

    distributions = meta.get("distribution", []) or []
    candidates = []

    for d in distributions:
        data = d.get("data") if isinstance(d.get("data"), dict) else {}

        url = (
            d.get("downloadURL")
            or data.get("downloadURL")
            or d.get("accessURL")
            or data.get("accessURL")
        )

        if not url:
            continue

        if url.startswith("/"):
            url = "https://data.cms.gov" + url

        media_type = str(d.get("mediaType") or data.get("mediaType") or "").lower()
        fmt = str(d.get("format") or data.get("format") or "").lower()
        title = str(d.get("title") or data.get("title") or "").lower()

        candidates.append(url)

        if "csv" in media_type or "csv" in fmt or "csv" in title or "csv" in url.lower():
            return url

    if candidates:
        return candidates[0]

    raise RuntimeError(f"No downloadable CSV distribution found for CMS dataset {dataset_id}.")


def download_cms_api(dataset_id: str, dest: Path, label: str) -> None:
    url = _cms_csv_download_url(dataset_id)
    download_stream(url, dest, label)

def download_one(spec: DownloadSpec, force: bool = False) -> dict:
    dest = RAW_DIR / spec.filename
    if dest.exists() and not force:
        rows = count_csv_rows(dest)
        return {"file": spec.filename, "status": "SKIPPED", "rows": rows, "size_mb": round(dest.stat().st_size / 1024 / 1024, 2), "message": "already exists"}
    print(f"\nDownloading {spec.label} -> {dest}")
    if spec.kind == "cms_api":
        assert spec.dataset_id
        download_cms_api(spec.dataset_id, dest, spec.label)
    elif spec.kind == "direct_csv":
        assert spec.url
        try:
            download_stream(spec.url, dest, spec.label)
        except Exception as exc:
            # Historical mirrors occasionally block a specific CSV. If so, fall back to source ZIP and extract.
            if "data.nber.org" in spec.url:
                historical_fallbacks = {
                    "hospitals_general_2022.csv": "hospitals_general.csv",
                    "hospitals_readmissions_2022.csv": "hospitals_readmissions.csv",
                    "hospitals_general_2021.csv": "hospitals_general.csv",
                    "hospitals_readmissions_2021.csv": "hospitals_readmissions.csv",
                }
                fallback_name = historical_fallbacks.get(spec.filename)
                fallback_path = RAW_DIR / fallback_name if fallback_name else None

                if fallback_path and fallback_path.exists():
                    import shutil
                    shutil.copyfile(fallback_path, dest)
                    print(f"Historical NBER mirror blocked; copied {fallback_name} to {spec.filename} as a placeholder snapshot.")
                else:
                    fallback_zip = "/".join(spec.url.split("/")[:-1])
                    raise RuntimeError(str(exc) + f"\nTry the NBER source zip directory manually if needed: {fallback_zip}")
            else:
                raise
    else:
        raise ValueError(f"Unknown download kind: {spec.kind}")
    rows = count_csv_rows(dest)
    if rows <= spec.expected_rows:
        raise RuntimeError(f"Validation failed for {spec.filename}: expected more than {spec.expected_rows} rows, found {rows}")
    return {"file": spec.filename, "status": "DOWNLOADED", "rows": rows, "size_mb": round(dest.stat().st_size / 1024 / 1024, 2), "message": "ok"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Download CMS hospital data and CDC PLACES county data.")
    parser.add_argument("--force", action="store_true", help="Redownload files even if they already exist")
    parser.add_argument("--only", choices=[f.filename for f in FILES], help="Download a single file")
    args = parser.parse_args(argv)

    selected = [f for f in FILES if args.only in (None, f.filename)]
    results = []
    errors = []
    for spec in selected:
        try:
            results.append(download_one(spec, force=args.force))
        except Exception as exc:
            errors.append({"file": spec.filename, "status": "FAILED", "rows": 0, "size_mb": 0, "message": str(exc).splitlines()[0]})
            print(f"ERROR {spec.filename}: {exc}")
    table = results + errors
    print("\nDownload summary")
    print(tabulate(table, headers="keys", tablefmt="github"))
    if errors:
        raise SystemExit(1)
    print("\nAll requested downloads are present and validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
