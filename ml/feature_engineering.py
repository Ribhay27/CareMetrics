from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sklearn.preprocessing import LabelEncoder

from common.config import PROJECT_ROOT, db_url

PROCESSED = PROJECT_ROOT / "data" / "processed"
PROCESSED.mkdir(parents=True, exist_ok=True)


def normalize_0_100(series: pd.Series, invert: bool = False) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    mn, mx = s.min(), s.max()
    if pd.isna(mn) or pd.isna(mx) or mx == mn:
        out = pd.Series(np.full(len(s), 50.0), index=s.index)
    else:
        out = (s - mn) / (mx - mn) * 100
    return 100 - out if invert else out


def ownership_bucket(value: object) -> str:
    v = str(value or "").lower()
    if "government" in v: return "Government"
    if "proprietary" in v or "physician" in v or "for profit" in v: return "For-profit"
    if "voluntary" in v or "non" in v: return "Non-profit"
    return "Other"


def hospital_type_bucket(value: object) -> str:
    v = str(value or "").lower()
    if "critical access" in v: return "Critical Access"
    if "psychiatric" in v: return "Psychiatric"
    if "children" in v: return "Childrens"
    if "acute" in v: return "General Acute"
    return "Other"


def main() -> int:
    engine = create_engine(db_url(), pool_pre_ping=True)
    df = pd.read_sql("select * from marts.mart_hospital_performance", engine)
    if df.empty:
        raise RuntimeError("marts.mart_hospital_performance is empty. Run dbt first.")

    features = pd.DataFrame()
    id_cols = ["provider_id", "hospital_name", "city", "state", "readmission_risk_label", "quality_tier"]
    for col in id_cols:
        features[col] = df[col] if col in df else None

    features["composite_quality_score"] = pd.to_numeric(df.get("composite_quality_score"), errors="coerce")
    raw_risk = df.get("readmission_risk_score", df.get("avg_readmission_score"))
    features["readmission_risk_score"] = normalize_0_100(raw_risk, invert=False)
    features["patient_experience_score"] = pd.to_numeric(df.get("overall_patient_experience_score"), errors="coerce")
    features["community_health_burden_score"] = pd.to_numeric(df.get("community_health_burden_score"), errors="coerce")
    features["urban_rural_encoded"] = df.get("urban_rural", "Urban").astype(str).str.lower().map({"urban": 1, "rural": 0}).fillna(1).astype(int)

    type_map = {"Critical Access": 0, "General Acute": 1, "Psychiatric": 2, "Childrens": 3, "Other": 4}
    owner_map = {"Government": 0, "Non-profit": 1, "For-profit": 2, "Other": 3}
    type_bucketed = df.get("hospital_type", "Other").map(hospital_type_bucket)
    owner_bucketed = df.get("hospital_ownership", "Other").map(ownership_bucket)
    features["hospital_type_encoded"] = type_bucketed.map(type_map).fillna(type_map["Other"]).astype(int)
    features["ownership_encoded"] = owner_bucketed.map(owner_map).fillna(owner_map["Other"]).astype(int)

    features["state_avg_quality_score"] = df.groupby("state")["composite_quality_score"].transform("mean")
    features["state_readmission_percentile"] = df.groupby("state")["readmission_risk_score"].rank(pct=True) * 100

    optional_numeric = [
        "diabetes_prevalence", "obesity_prevalence", "smoking_prevalence", "poor_mental_health_days",
        "no_health_insurance_rate", "physical_inactivity_rate", "overall_rating", "ed_throughput_score",
        "door_to_ct_score", "sepsis_care_score", "readm_heart_failure", "readm_pneumonia", "readm_copd",
        "readm_heart_attack", "readm_stroke", "readm_hip_knee"
    ]
    for col in optional_numeric:
        if col in df.columns:
            features[col] = pd.to_numeric(df[col], errors="coerce")

    numeric_cols = features.select_dtypes(include=[np.number]).columns.tolist()
    medians = {col: float(features[col].median()) if not pd.isna(features[col].median()) else 0.0 for col in numeric_cols}
    for col in numeric_cols:
        features[col] = features[col].fillna(medians[col])

    print(f"Feature matrix shape: {features.shape}")
    print("Null counts after engineering:")
    print(features.isna().sum().to_string())

    features.to_parquet(PROCESSED / "features.parquet", index=False)
    metadata = {
        "feature_columns": [c for c in numeric_cols if c not in ["composite_quality_score"]],
        "numeric_columns": numeric_cols,
        "medians": medians,
        "encodings": {"hospital_type_encoded": type_map, "ownership_encoded": owner_map, "urban_rural_encoded": {"Rural": 0, "Urban": 1}},
        "rows": int(len(features)),
    }
    (PROCESSED / "feature_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Saved {PROCESSED / 'features.parquet'}")
    print(f"Saved {PROCESSED / 'feature_metadata.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
