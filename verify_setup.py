from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

EXPECTED_SCHEMAS = {"raw", "staging", "intermediate", "marts"}


def check_docker() -> bool:
    try:
        subprocess.run(["docker", "info"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("PASS Docker: Docker is running")
        return True
    except Exception as exc:
        print(f"FAIL Docker: Docker is not running or not reachable ({exc})")
        return False


def build_db_url() -> str:
    user = os.getenv("POSTGRES_USER", "hospital_user")
    password = os.getenv("POSTGRES_PASSWORD", "hospital_password")
    db = os.getenv("POSTGRES_DB", "hospital_db")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"


def check_postgres() -> tuple[bool, object | None]:
    try:
        engine = create_engine(build_db_url(), pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("PASS PostgreSQL: connection succeeded")
        return True, engine
    except Exception as exc:
        print(f"FAIL PostgreSQL: connection failed ({exc})")
        return False, None


def check_schemas(engine) -> bool:
    try:
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name IN ('raw', 'staging', 'intermediate', 'marts')
            """)).fetchall()
        found = {r[0] for r in rows}
        missing = EXPECTED_SCHEMAS - found
        if missing:
            print(f"FAIL Schemas: missing {sorted(missing)}")
            return False
        print("PASS Schemas: raw, staging, intermediate, marts all exist")
        return True
    except Exception as exc:
        print(f"FAIL Schemas: could not query schemas ({exc})")
        return False


def main() -> int:
    results = []
    results.append(check_docker())
    pg_ok, engine = check_postgres()
    results.append(pg_ok)
    if engine is not None:
        results.append(check_schemas(engine))
    else:
        results.append(False)
    if all(results):
        print("\nALL CHECKS PASSED")
        return 0
    print("\nONE OR MORE CHECKS FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
