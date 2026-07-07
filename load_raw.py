from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
RAW_DIR = ROOT / "data" / "raw"

TABLE_FILES = {
    "hospitals_general": "hospitals_general.csv",
    "hospitals_readmissions": "hospitals_readmissions.csv",
    "hospitals_patient_experience": "hospitals_patient_experience.csv",
    "hospitals_timely_care": "hospitals_timely_care.csv",
    "hospitals_general_2022": "hospitals_general_2022.csv",
    "hospitals_readmissions_2022": "hospitals_readmissions_2022.csv",
    "hospitals_general_2021": "hospitals_general_2021.csv",
    "hospitals_readmissions_2021": "hospitals_readmissions_2021.csv",
    "cdc_places_county": "cdc_places_county.csv",
}

NULL_STRINGS = {"not available", "too few to report", "n/a", "na", "not applicable", "", "nan", "none", "null"}


def db_url() -> str:
    import os
    user = os.getenv("POSTGRES_USER", "hospital_user")
    password = os.getenv("POSTGRES_PASSWORD", "hospital_password")
    db = os.getenv("POSTGRES_DB", "hospital_db")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"


def clean_column(col: str) -> str:
    col = str(col).strip().lower()
    col = re.sub(r"[^a-z0-9]+", "_", col)
    col = re.sub(r"_+", "_", col).strip("_")
    if re.match(r"^\d", col):
        col = "col_" + col
    return col


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    seen: dict[str, int] = {}
    new_cols = []
    for col in df.columns:
        base = clean_column(col)
        count = seen.get(base, 0)
        seen[base] = count + 1
        new_cols.append(base if count == 0 else f"{base}_{count + 1}")
    df.columns = new_cols
    return df


def normalize_numeric_series(s: pd.Series) -> pd.Series:
    return pd.to_numeric(
        s.astype(str)
         .str.replace("%", "", regex=False)
         .str.replace(",", "", regex=False)
         .replace({v: np.nan for v in NULL_STRINGS}),
        errors="coerce",
    )


def first_existing(df: pd.DataFrame, names: list[str]) -> pd.Series | None:
    for name in names:
        if name in df.columns:
            return df[name]
    return None


def add_alias(df: pd.DataFrame, target: str, candidates: list[str], default=None) -> None:
    if target in df.columns:
        return
    series = first_existing(df, candidates)
    if series is not None:
        df[target] = series
    else:
        df[target] = default


def add_canonical_columns(df: pd.DataFrame, table: str) -> pd.DataFrame:
    df = df.copy()
    if table.startswith("hospitals_general"):
        add_alias(df, "provider_id", ["facility_id", "provider_id", "cms_certification_number_ccn"])
        add_alias(df, "hospital_name", ["facility_name", "hospital_name"])
        add_alias(df, "city", ["citytown", "city"])
        add_alias(df, "zip_code", ["zip_code", "zip"])
        add_alias(df, "address", ["address"])
        add_alias(df, "state", ["state"])
        add_alias(df, "hospital_type", ["hospital_type"])
        add_alias(df, "hospital_ownership", ["hospital_ownership", "ownership"])
        add_alias(df, "overall_rating", ["hospital_overall_rating", "overall_rating"])
    elif table.startswith("hospitals_readmissions"):
        add_alias(df, "provider_id", ["facility_id", "provider_id"])
        add_alias(df, "hospital_name", ["facility_name", "hospital_name"])
        add_alias(df, "state", ["state"])
        add_alias(df, "measure_name", ["measure_name", "measure"])
        add_alias(df, "measure_id", ["measure_id"])
        add_alias(df, "score", ["score", "excess_readmission_ratio", "predicted_readmission_rate", "number_of_readmissions"])
        add_alias(df, "compared_to_national", ["compared_to_national", "compared_to_national_rate"])
    elif table == "hospitals_patient_experience":
        add_alias(df, "provider_id", ["facility_id", "provider_id"])
        add_alias(df, "hospital_name", ["facility_name", "hospital_name"])
        add_alias(df, "state", ["state"])
        add_alias(df, "measure_name", ["hcahps_measure_id", "hcahps_question", "measure_name", "hcahps_answer_description"])
        add_alias(df, "measure_id", ["hcahps_measure_id", "measure_id"])
        add_alias(df, "score", ["hcahps_linear_mean_value", "linear_mean_value", "patient_survey_star_rating", "hcahps_answer_percent", "score"])
    elif table == "hospitals_timely_care":
        add_alias(df, "provider_id", ["facility_id", "provider_id"])
        add_alias(df, "hospital_name", ["facility_name", "hospital_name"])
        add_alias(df, "state", ["state"])
        add_alias(df, "measure_name", ["measure_name", "measure"])
        add_alias(df, "measure_id", ["measure_id"])
        add_alias(df, "score", ["score"])
    elif table == "cdc_places_county":
        add_alias(df, "county_fips", ["locationid", "countyfips", "county_fips", "geolocationid"])
        add_alias(df, "state", ["stateabbr", "state_abbr", "state"])
        add_alias(df, "county_name", ["locationname", "county_name"])
        add_alias(df, "measure_id", ["measureid", "measure_id"])
        add_alias(df, "measure", ["measure", "measure_name"])
        add_alias(df, "data_value", ["data_value", "datavalue"])
    return df


def load_table(engine, table: str, csv_file: str) -> dict:
    path = RAW_DIR / csv_file
    if not path.exists():
        raise FileNotFoundError(f"Missing data file: {path}. Run python download_data.py first.")
    df = pd.read_csv(path, low_memory=False)
    csv_rows = len(df)
    df = standardize_columns(df)
    df = add_canonical_columns(df, table)
    df["source_file"] = csv_file
    df["loaded_at"] = datetime.now(timezone.utc)
    df.to_sql(table, engine, schema="raw", if_exists="replace", index=False, method="multi", chunksize=1000)
    with engine.connect() as conn:
        db_rows = conn.execute(text(f'SELECT COUNT(*) FROM raw."{table}"')).scalar_one()
    status = "PASS" if db_rows == csv_rows else "FAIL"
    print(f"{status} raw.{table}: {db_rows:,} rows loaded, {len(df.columns):,} columns loaded")
    return {"table": table, "csv_rows": csv_rows, "db_rows": db_rows, "columns": len(df.columns), "status": status}


def main() -> int:
    engine = create_engine(db_url(), pool_pre_ping=True)
    run_details = []
    status = "success"
    started = datetime.now(timezone.utc)
    try:
        for table, csv_file in TABLE_FILES.items():
            run_details.append(load_table(engine, table, csv_file))
        failures = [r for r in run_details if r["status"] != "PASS"]
        if failures:
            status = "failed"
            raise RuntimeError(f"Row-count validation failed for: {[f['table'] for f in failures]}")
    except Exception:
        status = "failed"
        raise
    finally:
        completed = datetime.now(timezone.utc)
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO raw.hospital_pipeline_runs (pipeline_stage, status, started_at, completed_at, details)
                VALUES (:stage, :status, :started, :completed, CAST(:details AS JSONB))
            """), {
                "stage": "load_raw",
                "status": status,
                "started": started,
                "completed": completed,
                "details": json.dumps(run_details),
            })
    print("\nRaw load validation complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
