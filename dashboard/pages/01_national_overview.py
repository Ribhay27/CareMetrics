import pandas as pd
import streamlit as st
from dashboard.utils.api_client import get_regional_summary
from dashboard.utils.db import run_query
from dashboard.utils.charts import quality_score_histogram, risk_distribution_bar, state_choropleth


def run():
    st.header("1. National Overview")
    regional = pd.DataFrame(get_regional_summary())
    perf = run_query("select * from marts.mart_hospital_performance")
    if perf.empty:
        st.warning("No mart data found. Run dbt first."); return
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total Hospitals Analyzed", f"{len(perf):,}")
    c2.metric("Average Quality Score", f"{perf['composite_quality_score'].mean():.1f}")
    c3.metric("Hospitals Above National Readmission Average", f"{(perf['readmission_risk_score'] > perf['readmission_risk_score'].mean()).mean()*100:.1f}%")
    c4.metric("Average Patient Experience", f"{perf['overall_patient_experience_score'].mean():.1f}")
    st.plotly_chart(quality_score_histogram(perf), use_container_width=True)
    st.plotly_chart(risk_distribution_bar(perf), use_container_width=True)
    if not regional.empty:
        st.plotly_chart(state_choropleth(regional, "avg_quality_score", "Average Quality Score by State"), use_container_width=True)
        left, right = st.columns(2)
        left.subheader("Top 10 Best Performing States")
        left.dataframe(regional.sort_values("avg_quality_score", ascending=False).head(10), use_container_width=True)
        right.subheader("Top 10 Highest Risk States")
        right.dataframe(regional.sort_values("avg_readmission_risk", ascending=False).head(10), use_container_width=True)
