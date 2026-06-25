import pandas as pd
import streamlit as st
from dashboard.utils.db import run_query
from dashboard.utils.api_client import get_hospital_profile
from dashboard.utils.charts import shap_waterfall


def run():
    st.header("2. Hospital Search")
    term = st.text_input("Search hospital name, city, or state", "")
    sql = """
        select provider_id, hospital_name, city, state, composite_quality_score, readmission_risk_label,
               quality_tier, hospital_type, hospital_ownership, community_health_burden_score
        from marts.mart_hospital_performance
        where (:term = '' or hospital_name ilike :like or city ilike :like or state ilike :like)
        order by composite_quality_score desc nulls last limit 500
    """
    df = run_query(sql, {"term": term, "like": f"%{term}%"})
    st.dataframe(df, use_container_width=True, hide_index=True)
    if df.empty: return
    provider_id = st.selectbox("Select a hospital to inspect", df["provider_id"].astype(str), format_func=lambda x: df.loc[df.provider_id.astype(str)==x, 'hospital_name'].iloc[0])
    profile = get_hospital_profile(provider_id)
    if not profile: return
    st.subheader(profile.get("hospital_name"))
    risk = profile.get("readmission_risk_label", "Medium")
    css = {"High":"risk-high", "Medium":"risk-medium", "Low":"risk-low"}.get(risk, "risk-medium")
    st.markdown(f'<span class="{css}">{risk} Risk</span>', unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Quality", f"{profile.get('composite_quality_score') or 0:.1f}")
    c2.metric("Readmission Risk", f"{profile.get('readmission_risk_score') or 0:.1f}")
    c3.metric("Patient Experience", f"{profile.get('patient_experience_score') or 0:.1f}")
    c4.metric("Community Burden", f"{profile.get('community_health_burden_score') or 0:.1f}")
    shap = profile.get("shap_classifier") or {}
    if shap:
        st.plotly_chart(shap_waterfall(list(shap.values()), list(shap.keys()), profile.get("hospital_name")), use_container_width=True)
    st.info(f"Community health context for {profile.get('state')}: burden score {profile.get('community_health_burden_score') or 0:.1f}")
    if "compare" not in st.session_state: st.session_state.compare = []
    if st.button("Add to Compare") and provider_id not in st.session_state.compare and len(st.session_state.compare) < 3:
        st.session_state.compare.append(provider_id)
    if st.session_state.compare:
        st.subheader("Comparison")
        comp = df[df.provider_id.astype(str).isin(st.session_state.compare)]
        st.dataframe(comp, use_container_width=True, hide_index=True)
