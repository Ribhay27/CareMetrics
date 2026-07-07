import streamlit as st
from dashboard.utils.db import run_query


def style_quality(v):
    if v >= 70: return 'background-color: #dcfce7'
    if v >= 50: return 'background-color: #fef3c7'
    return 'background-color: #fee2e2'


def run():
    st.header("4. Quality Scorecard")
    df = run_query("select * from marts.mart_hospital_performance")
    if df.empty: st.warning("No data"); return
    with st.sidebar:
        states = st.multiselect("State", sorted(df.state.dropna().unique()))
        types = st.multiselect("Hospital Type", sorted(df.hospital_type.dropna().unique()))
        risks = st.multiselect("Risk Level", sorted(df.readmission_risk_label.dropna().unique()))
        owners = st.multiselect("Ownership", sorted(df.hospital_ownership.dropna().unique()))
        min_q, max_q = float(df.composite_quality_score.min()), float(df.composite_quality_score.max())
        qr = st.slider("Quality Score", min_q, max_q, (min_q, max_q))
    f = df.copy()
    if states: f = f[f.state.isin(states)]
    if types: f = f[f.hospital_type.isin(types)]
    if risks: f = f[f.readmission_risk_label.isin(risks)]
    if owners: f = f[f.hospital_ownership.isin(owners)]
    f = f[(f.composite_quality_score >= qr[0]) & (f.composite_quality_score <= qr[1])]
    cols = ["hospital_name","state","composite_quality_score","readmission_risk_score","overall_patient_experience_score","community_health_burden_score","readmission_risk_label","quality_tier"]
    st.write(f"Filtered results: {len(f):,}")
    st.dataframe(f[cols].style.applymap(style_quality, subset=["composite_quality_score"]), use_container_width=True, hide_index=True)
    st.download_button("Download CSV", f[cols].to_csv(index=False), "quality_scorecard.csv", "text/csv")
