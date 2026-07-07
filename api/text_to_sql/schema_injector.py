from __future__ import annotations

from sqlalchemy import text
from api.db import get_engine

MART_TABLES = ["mart_hospital_performance", "mart_readmission_risk", "mart_regional_summary"]


def get_schema_context() -> str:
    engine = get_engine()
    lines = ["Schema: marts", "provider_id is the primary hospital identifier across hospital-level mart tables."]
    with engine.connect() as conn:
        for table in MART_TABLES:
            cols = conn.execute(text("""
                select column_name, data_type
                from information_schema.columns
                where table_schema='marts' and table_name=:table
                order by ordinal_position
            """), {"table": table}).mappings().all()
            lines.append(f"\nTable marts.{table}")
            for c in cols:
                lines.append(f"- {c['column_name']}: {c['data_type']}")
        sample_queries = {
            "readmission_risk_label": "select distinct readmission_risk_label from marts.mart_hospital_performance where readmission_risk_label is not null limit 10",
            "hospital_type": "select distinct hospital_type from marts.mart_hospital_performance where hospital_type is not null limit 10",
            "state": "select distinct state from marts.mart_hospital_performance where state is not null order by state limit 60",
            "hospital_ownership": "select distinct hospital_ownership from marts.mart_hospital_performance where hospital_ownership is not null limit 10",
        }
        lines.append("\nCategorical sample values:")
        for name, sql in sample_queries.items():
            try:
                vals = [list(r)[0] for r in conn.execute(text(sql)).fetchall()]
            except Exception:
                vals = []
            lines.append(f"- {name}: {vals}")
    lines.append("\nRelationships:")
    lines.append("- marts.mart_hospital_performance.provider_id = marts.mart_readmission_risk.provider_id")
    lines.append("- marts.mart_hospital_performance.state = marts.mart_regional_summary.state")
    lines.append("Only query tables inside the marts schema.")
    return "\n".join(lines)
