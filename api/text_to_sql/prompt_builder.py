from __future__ import annotations

from api.text_to_sql.schema_injector import get_schema_context

FEW_SHOTS = [
    ("Which states have the highest average readmission risk?", "SELECT state, AVG(readmission_risk_score) AS avg_readmission_risk FROM marts.mart_hospital_performance GROUP BY state ORDER BY avg_readmission_risk DESC LIMIT 10;"),
    ("Show me hospitals in Arizona with high readmission risk", "SELECT provider_id, hospital_name, city, state, readmission_risk_score, readmission_risk_label FROM marts.mart_hospital_performance WHERE state = 'AZ' AND readmission_risk_label = 'High' ORDER BY readmission_risk_score DESC LIMIT 50;"),
    ("What are the top 10 hospitals by quality score?", "SELECT provider_id, hospital_name, city, state, composite_quality_score FROM marts.mart_hospital_performance ORDER BY composite_quality_score DESC NULLS LAST LIMIT 10;"),
    ("Which hospital types have the best average quality scores?", "SELECT hospital_type, AVG(composite_quality_score) AS avg_quality_score, COUNT(*) AS hospital_count FROM marts.mart_hospital_performance GROUP BY hospital_type ORDER BY avg_quality_score DESC NULLS LAST;"),
    ("Show hospitals where community health burden is high but quality score is above 70", "SELECT provider_id, hospital_name, city, state, composite_quality_score, community_health_burden_score, risk_context_label FROM marts.mart_hospital_performance WHERE risk_context_label = 'High Burden' AND composite_quality_score > 70 ORDER BY composite_quality_score DESC LIMIT 50;"),
]


def build_prompt(question: str) -> list[dict]:
    schema = get_schema_context()
    system = (
        "You are a PostgreSQL Text-to-SQL assistant for hospital quality analytics. "
        "Return only valid SQL. Do not include explanation, markdown, comments, or backticks. "
        "Only SELECT statements are allowed. Use only tables in the marts schema. "
        "Always add a LIMIT 50 unless the query is an aggregation returning fewer rows.\n\n"
        f"{schema}"
    )
    examples = "\n\n".join([f"Question: {q}\nSQL: {sql}" for q, sql in FEW_SHOTS])
    user = f"{examples}\n\nQuestion: {question}\nSQL:"
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]
