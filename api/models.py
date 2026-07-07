from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any


class HospitalProfile(BaseModel):
    provider_id: str
    hospital_name: str | None = None
    city: str | None = None
    state: str | None = None
    hospital_type: str | None = None
    hospital_ownership: str | None = None
    composite_quality_score: float | None = None
    readmission_risk_score: float | None = None
    patient_experience_score: float | None = None
    community_health_burden_score: float | None = None
    readmission_risk_label: str | None = None
    quality_tier: str | None = None
    shap_classifier: dict[str, float] | None = None
    shap_regressor: dict[str, float] | None = None
    raw: dict[str, Any] | None = None


class HospitalScoreRequest(BaseModel):
    composite_quality_score: float = Field(..., ge=0, le=100)
    readmission_risk_score: float = Field(..., ge=0, le=100)
    patient_experience_score: float = Field(..., ge=0, le=100)
    community_health_burden_score: float = Field(..., ge=0, le=100)
    hospital_type_encoded: int = 1
    ownership_encoded: int = 1
    urban_rural_encoded: int = 1
    state_avg_quality_score: float = Field(50, ge=0, le=100)
    state_readmission_percentile: float = Field(50, ge=0, le=100)


class HospitalScoreResponse(BaseModel):
    predicted_risk_label: str
    predicted_quality_score: float
    top_shap_drivers: list[dict[str, float | str]]


class RegionalSummary(BaseModel):
    state: str
    hospital_count: int
    avg_quality_score: float | None = None
    avg_readmission_risk: float | None = None
    pct_high_risk: float | None = None
    pct_low_risk: float | None = None
    avg_community_burden: float | None = None
    top_performing_hospital: str | None = None
    most_at_risk_hospital: str | None = None


class TrendData(BaseModel):
    provider_id: str
    hospital_name: str | None = None
    year: int
    quality_score: float | None = None
    readmission_risk_score: float | None = None
    national_avg_quality_score: float | None = None
    national_avg_readmission_risk_score: float | None = None


class NLQRequest(BaseModel):
    question: str = Field(..., min_length=3)


class NLQResponse(BaseModel):
    question: str
    generated_sql: str
    results: list[dict[str, Any]]
    plain_english_summary: str
