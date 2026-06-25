import streamlit as st
import plotly.express as px
from dashboard.utils.db import run_query
from dashboard.utils.charts import state_choropleth


def run():
    st.header("3. Readmission Map")
    df = run_query("select * from marts.mart_hospital_performance")
    if df.empty: st.warning("No data"); return
    with st.sidebar:
        states = st.multiselect("State", sorted(df.state.dropna().unique()))
        types = st.multiselect("Hospital Type", sorted(df.hospital_type.dropna().unique()))
        risks = st.multiselect("Risk Level", sorted(df.readmission_risk_label.dropna().unique()))
        owners = st.multiselect("Ownership", sorted(df.hospital_ownership.dropna().unique()))
    f = df.copy()
    if states: f = f[f.state.isin(states)]
    if types: f = f[f.hospital_type.isin(types)]
    if risks: f = f[f.readmission_risk_label.isin(risks)]
    if owners: f = f[f.hospital_ownership.isin(owners)]
    state_df = f.groupby("state", as_index=False).agg(avg_readmission_risk_score=("readmission_risk_score", "mean"), hospital_count=("provider_id", "count"))
    st.plotly_chart(state_choropleth(state_df, "avg_readmission_risk_score", "Average Readmission Risk Score by State"), use_container_width=True)
    if {'latitude','longitude'}.issubset(f.columns):
        st.plotly_chart(px.scatter_geo(f, lat="latitude", lon="longitude", color="readmission_risk_label", hover_name="hospital_name", hover_data=["city", "quality_score"], scope="usa"), use_container_width=True)
    else:
        st.caption("Individual dot layer needs latitude/longitude columns; CMS general file may not include them.")
    c1,c2,c3 = st.columns(3)
    c1.metric("Filtered Hospitals", f"{len(f):,}")
    c2.metric("Average Risk", f"{f.readmission_risk_score.mean():.1f}")
    c3.metric("High Risk Share", f"{(f.readmission_risk_label=='High').mean()*100:.1f}%")
