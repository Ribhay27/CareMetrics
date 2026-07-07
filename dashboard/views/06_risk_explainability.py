import json
import pandas as pd
import streamlit as st
from pathlib import Path
from dashboard.utils.db import run_query
from dashboard.utils.charts import shap_waterfall
from common.config import PROJECT_ROOT


def _load(path):
    return pd.read_parquet(path) if path.exists() else pd.DataFrame()


def run():
    st.header("6. Risk Explainability")
    hospitals = run_query("select provider_id, hospital_name, state, readmission_risk_label from marts.mart_hospital_performance order by hospital_name")
    if hospitals.empty: st.warning("No data"); return
    provider = st.selectbox("Hospital", hospitals.provider_id.astype(str), format_func=lambda x: hospitals.loc[hospitals.provider_id.astype(str)==x, 'hospital_name'].iloc[0])
    row = hospitals[hospitals.provider_id.astype(str)==provider].iloc[0]
    clf = _load(PROJECT_ROOT / "data" / "processed" / "shap_classifier.parquet")
    reg = _load(PROJECT_ROOT / "data" / "processed" / "shap_regressor.parquet")
    for name, data in [("Readmission Risk Classifier", clf), ("Quality Score Regressor", reg)]:
        srow = data[data.provider_id.astype(str)==provider] if not data.empty else pd.DataFrame()
        if not srow.empty:
            vals = srow.drop(columns=["provider_id"]).iloc[0]
            st.plotly_chart(shap_waterfall(vals.values, vals.index.values, row.hospital_name), use_container_width=True)
            top = vals.abs().sort_values(ascending=False).head(3).index.tolist()
            st.write(f"This hospital was flagged {row.readmission_risk_label} primarily because of {', '.join(top)}.")
        else:
            st.info(f"{name} SHAP values not available yet. Run ml/shap_analysis.py.")
    for filename in ["classifier_metrics.json", "regressor_metrics.json"]:
        path = PROJECT_ROOT / "data" / "processed" / filename
        with st.expander(filename):
            st.json(json.loads(path.read_text()) if path.exists() else {"status": "missing"})
