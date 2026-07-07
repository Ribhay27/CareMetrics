from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from common.config import db_url

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(db_url(), pool_pre_ping=True)
    return _engine


def fetch_all(sql: str, params: dict | None = None) -> list[dict]:
    with get_engine().connect() as conn:
        rows = conn.execute(text(sql), params or {}).mappings().all()
        return [dict(r) for r in rows]
