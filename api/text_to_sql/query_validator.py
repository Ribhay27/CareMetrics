from __future__ import annotations

import re
import sqlparse
from sqlalchemy import text
from api.db import get_engine

ALLOWED_TABLES = {"mart_hospital_performance", "mart_readmission_risk", "mart_regional_summary"}
FORBIDDEN = re.compile(r"\b(insert|update|delete|drop|alter|truncate|create|grant|revoke|copy|execute|call)\b", re.I)


def _load_columns() -> dict[str, set[str]]:
    with get_engine().connect() as conn:
        rows = conn.execute(text("""
            select table_name, column_name
            from information_schema.columns
            where table_schema='marts'
        """)).fetchall()
    cols: dict[str, set[str]] = {}
    for t, c in rows:
        cols.setdefault(t, set()).add(c)
    return cols


def _extract_tables(sql: str) -> set[str]:
    names = set()
    for match in re.finditer(r"\b(?:from|join)\s+((?:\w+\.)?\w+)", sql, flags=re.I):
        ref = match.group(1)
        if "." in ref:
            schema, table = ref.split(".", 1)
            if schema.lower() != "marts":
                names.add(f"INVALID_SCHEMA:{schema}.{table}")
            else:
                names.add(table)
        else:
            names.add(ref)
    return names


def validate_query(sql: str) -> tuple[bool, str | None]:
    if not sql or not sql.strip():
        return False, "SQL is empty"
    parsed = sqlparse.parse(sql)
    if not parsed:
        return False, "Could not parse SQL"
    first = parsed[0]
    if first.get_type() != "SELECT":
        return False, "Only SELECT statements are allowed"
    if FORBIDDEN.search(sql):
        return False, "SQL contains a forbidden statement or keyword"
    tables = _extract_tables(sql)
    if not tables:
        return False, "No table reference found"
    bad_schema = [t for t in tables if t.startswith("INVALID_SCHEMA:")]
    if bad_schema:
        return False, f"Only marts schema is allowed: {bad_schema}"
    unknown = tables - ALLOWED_TABLES
    if unknown:
        return False, f"Unknown or disallowed table(s): {sorted(unknown)}"
    # Conservative validation: table-level access is enforced. Column validation is intentionally permissive
    # for expressions, aliases, functions, and aggregates that sqlparse cannot safely resolve without a full parser.
    return True, None
