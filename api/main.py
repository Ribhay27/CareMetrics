from __future__ import annotations

from datetime import datetime, timezone
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from api.db import fetch_all, get_engine
from api.routes.hospitals import router as hospitals_router
from api.routes.nlq import router as nlq_router
from api.routes.predictions import router as predictions_router
from common.config import PROJECT_ROOT

load_dotenv(PROJECT_ROOT / ".env")

app = FastAPI(title="Clinical Performance & Readmission Risk Analytics API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(hospitals_router, prefix="/hospitals", tags=["hospitals"])
app.include_router(predictions_router, prefix="/hospitals", tags=["predictions"])
app.include_router(nlq_router, prefix="/nlq", tags=["natural-language-query"])


@app.on_event("startup")
def startup_checks():
    with get_engine().connect() as conn:
        conn.execute(text("SELECT 1"))
    for path in [PROJECT_ROOT / "ml" / "models" / "readmission_classifier.pkl", PROJECT_ROOT / "ml" / "models" / "quality_regressor.pkl"]:
        if not path.exists():
            print(f"WARN model file not found yet: {path}")


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/regional/summary")
def regional_summary():
    return fetch_all("SELECT * FROM marts.mart_regional_summary ORDER BY avg_quality_score DESC NULLS LAST")


@app.get("/trends/{provider_id}")
def trends(provider_id: str):
    sql = """
    with current as (
        select provider_id, hospital_name, 2023 as year,
               composite_quality_score as quality_score,
               readmission_risk_score,
               avg(composite_quality_score) over () as national_avg_quality_score,
               avg(readmission_risk_score) over () as national_avg_readmission_risk_score
        from marts.mart_hospital_performance
        where provider_id = :provider_id
    ), hist as (
        select nullif(trim(g.provider_id::text),'') as provider_id,
               g.hospital_name::text as hospital_name,
               2022 as year,
               case when lower(coalesce(g.overall_rating::text,'')) in ('not available','n/a','') then null
                    else nullif(regexp_replace(g.overall_rating::text, '[^0-9]', '', 'g'),'')::numeric * 20 end as quality_score,
               null as readmission_risk_score,
               null as national_avg_quality_score,
               null as national_avg_readmission_risk_score
        from raw.hospitals_general_2022 g where nullif(trim(g.provider_id::text),'') = :provider_id
        union all
        select nullif(trim(g.provider_id::text),'') as provider_id,
               g.hospital_name::text as hospital_name,
               2021 as year,
               case when lower(coalesce(g.overall_rating::text,'')) in ('not available','n/a','') then null
                    else nullif(regexp_replace(g.overall_rating::text, '[^0-9]', '', 'g'),'')::numeric * 20 end as quality_score,
               null as readmission_risk_score,
               null as national_avg_quality_score,
               null as national_avg_readmission_risk_score
        from raw.hospitals_general_2021 g where nullif(trim(g.provider_id::text),'') = :provider_id
    )
    select * from hist
    union all
    select * from current
    order by year
    """
    rows = fetch_all(sql, {"provider_id": provider_id})
    if not rows:
        raise HTTPException(status_code=404, detail="No trend data found for provider_id")
    return rows
