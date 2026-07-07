import pandas as pd
import streamlit as st
from dashboard.utils.db import run_query
from dashboard.utils.charts import scatter_with_regression
import plotly.express as px


def run():
    st.header("5. Community Health")
    df = run_query("select * from marts.mart_hospital_performance")
    if df.empty: st.warning("No data"); return
    state = st.selectbox("State filter", ["All"] + sorted(df.state.dropna().unique().tolist()))
    f = df if state == "All" else df[df.state == state]
    pairs = [
        ("diabetes_prevalence", "readmission_risk_score", "Readmission Risk vs Diabetes Prevalence"),
        ("obesity_prevalence", "composite_quality_score", "Quality Score vs Obesity Prevalence"),
        ("smoking_prevalence", "readmission_risk_score", "Readmission Risk vs Smoking Rate"),
        ("community_health_burden_score", "composite_quality_score", "Quality Score vs Community Burden"),
    ]
    corrs = []
    for x,y,title in pairs:
        if x in f and y in f:
            st.plotly_chart(scatter_with_regression(f.dropna(subset=[x,y]), x, y, title), use_container_width=True)
            corrs.append((title, f[x].corr(f[y])))
    if corrs:
        best = max(corrs, key=lambda p: abs(p[1]) if pd.notna(p[1]) else -1)
        st.markdown(f'<div class="callout">The strongest correlation found is between {best[0]} (r = {best[1]:.2f}).</div>', unsafe_allow_html=True)
    state_burden = df.groupby("state", as_index=False).community_health_burden_score.mean().sort_values("community_health_burden_score", ascending=False)
    st.plotly_chart(px.bar(state_burden.head(25), x="state", y="community_health_burden_score", title="States Ranked by Community Health Burden"), use_container_width=True)
