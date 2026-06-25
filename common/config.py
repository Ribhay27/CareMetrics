from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", Path(__file__).resolve().parents[1]))
load_dotenv(PROJECT_ROOT / ".env")


def env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or value == "":
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def db_url(async_driver: bool = False, host_override: str | None = None) -> str:
    user = env("POSTGRES_USER")
    password = env("POSTGRES_PASSWORD")
    db = env("POSTGRES_DB")
    host = host_override or env("POSTGRES_HOST", "localhost")
    port = env("POSTGRES_PORT", "5432")
    driver = "postgresql+psycopg2"
    return f"{driver}://{user}:{password}@{host}:{port}/{db}"
