from __future__ import annotations

import os
import re
from pathlib import Path

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

try:
    from common.config import db_url
except Exception:
    db_url = None


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMO_DB_PATH = PROJECT_ROOT / "data" / "demo" / "caremetrics_demo.sqlite"

REQUIRED_POSTGRES_ENV = [
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "POSTGRES_DB",
]


def should_use_demo_db() -> bool:
    """Use SQLite demo data on Streamlit Cloud when Postgres env vars are missing."""
    if os.getenv("USE_DEMO_DB") == "1":
        return True

    missing_postgres_env = any(not os.getenv(key) for key in REQUIRED_POSTGRES_ENV)
    return missing_postgres_env


def normalize_sql_for_demo(sql: str) -> str:
    """Translate Postgres schema-qualified table names into SQLite table names."""
    replacements = {
        "marts.": "marts__",
        "intermediate.": "intermediate__",
        "staging.": "staging__",
        "raw.": "raw__",
    }

    demo_sql = sql

    for postgres_prefix, sqlite_prefix in replacements.items():
        demo_sql = demo_sql.replace(postgres_prefix, sqlite_prefix)

    demo_sql = re.sub(r"\bILIKE\b", "LIKE", demo_sql, flags=re.IGNORECASE)

    return demo_sql


@st.cache_resource
def get_connection():
    if should_use_demo_db():
        if not DEMO_DB_PATH.exists():
            raise FileNotFoundError(
                f"Demo database not found at {DEMO_DB_PATH}. "
                "Run the demo export script first."
            )

        return create_engine(
            f"sqlite:///{DEMO_DB_PATH}",
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
        )

    if db_url is None:
        raise RuntimeError("Could not import db_url from common.config.")

    return create_engine(db_url(), pool_pre_ping=True)


@st.cache_data(ttl=300)
def run_query(sql: str, params: dict | None = None) -> pd.DataFrame:
    if should_use_demo_db():
        demo_sql = normalize_sql_for_demo(sql)
        return pd.read_sql_query(demo_sql, get_connection(), params=params or {})

    return pd.read_sql(text(sql), get_connection(), params=params or {})
