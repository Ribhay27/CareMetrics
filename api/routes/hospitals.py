from __future__ import annotations

from pathlib import Path
import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text

from api.db import fetch_all, get_engine
from api.models import HospitalProfile
from common.config import PROJECT_ROOT

router = APIRouter()


@router.get("")
def list_hospitals(state: str | None = None, risk_level: str | None = None, quality_min: float | None = None, limit: int = Query(100, ge=1, le=1000)):
    clauses = []
    params = {"limit": limit}
    if state:
        clauses.append("state = :state")
        params["state"] = state.upper()
    if risk_level:
        clauses.append("readmission_risk_label = :risk")
        params["risk"] = risk_level.title()
    if quality_min is not None:
        clauses.append("composite_quality_score >= :quality_min")
        params["quality_min"] = quality_min
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    sql = f"""
        SELECT provider_id, hospital_name, city, state, hospital_type, hospital_ownership,
               composite_quality_score, readmission_risk_score, overall_patient_experience_score,
               community_health_burden_score, readmission_risk_label, quality_tier
        FROM marts.mart_hospital_performance
        {where}
        ORDER BY composite_quality_score DESC NULLS LAST
        LIMIT :limit
    """
    return fetch_all(sql, params)


@router.get("/risk")
def hospitals_by_risk(state: str | None = None, risk_level: str = Query("High", pattern="^(Low|Medium|High)$"), limit: int = Query(100, ge=1, le=1000)):
    return list_hospitals(state=state, risk_level=risk_level, quality_min=None, limit=limit)


def _shap_for(provider_id: str, filename: str) -> dict[str, float] | None:
    path = PROJECT_ROOT / "data" / "processed" / filename
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    row = df[df["provider_id"].astype(str) == str(provider_id)]
    if row.empty:
        return None
    return {k: float(v) for k, v in row.iloc[0].drop(labels=["provider_id"]).to_dict().items()}


@router.get("/{provider_id}", response_model=HospitalProfile)
def hospital_profile(provider_id: str):
    rows = fetch_all("SELECT * FROM marts.mart_hospital_performance WHERE provider_id = :provider_id", {"provider_id": provider_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Hospital not found")
    row = rows[0]
    return HospitalProfile(
        provider_id=str(row.get("provider_id")),
        hospital_name=row.get("hospital_name"),
        city=row.get("city"),
        state=row.get("state"),
        hospital_type=row.get("hospital_type"),
        hospital_ownership=row.get("hospital_ownership"),
        composite_quality_score=row.get("composite_quality_score"),
        readmission_risk_score=row.get("readmission_risk_score"),
        patient_experience_score=row.get("overall_patient_experience_score"),
        community_health_burden_score=row.get("community_health_burden_score"),
        readmission_risk_label=row.get("readmission_risk_label"),
        quality_tier=row.get("quality_tier"),
        shap_classifier=_shap_for(provider_id, "shap_classifier.parquet"),
        shap_regressor=_shap_for(provider_id, "shap_regressor.parquet"),
        raw=row,
    )
