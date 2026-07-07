import pandas as pd
import streamlit as st
import plotly.express as px

from dashboard.utils.db import run_query
from dashboard.utils.charts import quality_score_histogram, risk_distribution_bar, state_choropleth, polish


def metric_card(label: str, value: str, delta: str = ""):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="label">{label}</div>
            <div class="value">{value}</div>
            <div class="delta">{delta}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def run():
    perf = run_query("select * from marts.mart_hospital_performance")
    regional = run_query("select * from marts.mart_regional_summary")
    if perf.empty:
        st.warning("No mart data found. Run dbt first.")
        return

    st.markdown(
        '<div class="page-title"><div><h2>National Overview</h2><p>Executive summary across hospitals, quality, patient experience, and readmission risk.</p></div></div>',
        unsafe_allow_html=True,
    )

    with st.expander("Filters", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        states = c1.multiselect("States", sorted(perf.state.dropna().unique()))
        risks = c2.multiselect("Risk level", sorted(perf.readmission_risk_label.dropna().unique()))
        types = c3.multiselect("Hospital type", sorted(perf.hospital_type.dropna().unique()))
        tiers = c4.multiselect("Quality tier", sorted(perf.quality_tier.dropna().unique()) if "quality_tier" in perf else [])

    f = perf.copy()
    if states:
        f = f[f.state.isin(states)]
    if risks:
        f = f[f.readmission_risk_label.isin(risks)]
    if types:
        f = f[f.hospital_type.isin(types)]
    if tiers and "quality_tier" in f:
        f = f[f.quality_tier.isin(tiers)]

    avg_quality = f["composite_quality_score"].mean()
    avg_risk = f["readmission_risk_score"].mean()
    avg_px = f["overall_patient_experience_score"].mean()
    high_share = (f["readmission_risk_label"].eq("High").mean() * 100) if "readmission_risk_label" in f else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        metric_card("Hospitals analyzed", f"{len(f):,}", "Filtered provider count")
    with k2:
        metric_card("Avg quality score", f"{avg_quality:.1f}", "Composite quality index")
    with k3:
        metric_card("Avg readmission risk", f"{avg_risk:.1f}", f"High-risk share {high_share:.1f}%")
    with k4:
        metric_card("Avg patient experience", f"{avg_px:.1f}", "HCAHPS-derived score")

    st.write("")
    tab1, tab2, tab3 = st.tabs(["📊 Distribution", "🗺️ State intelligence", "🏆 Provider leaderboard"])

    with tab1:
        left, right = st.columns([1.45, 1])
        with left:
            st.plotly_chart(quality_score_histogram(f), use_container_width=True)
        with right:
            st.plotly_chart(risk_distribution_bar(f), use_container_width=True)

        by_type = f.groupby("hospital_type", dropna=False, as_index=False).agg(
            hospitals=("provider_id", "count"),
            avg_quality=("composite_quality_score", "mean"),
            avg_risk=("readmission_risk_score", "mean"),
        ).sort_values("hospitals", ascending=False).head(15)

        fig = px.bar(
            by_type,
            x="hospitals",
            y="hospital_type",
            orientation="h",
            color="avg_quality",
            title="Hospital mix by type",
            color_continuous_scale="Blues",
        )
        fig.update_layout(yaxis={"autorange": "reversed"})
        st.plotly_chart(polish(fig, height=460), use_container_width=True)

    with tab2:
        if regional.empty:
            st.info("Regional summary table is empty. Run dbt models first.")
        else:
            map_metric = st.radio("Map metric", ["avg_quality_score", "avg_readmission_risk", "hospital_count"], horizontal=True)
            st.plotly_chart(state_choropleth(regional, map_metric, map_metric.replace("_", " ").title()), use_container_width=True)

            c1, c2 = st.columns(2)
            c1.markdown("### Best quality states")
            c1.dataframe(regional.sort_values("avg_quality_score", ascending=False).head(10), use_container_width=True, hide_index=True)

            c2.markdown("### Highest readmission-risk states")
            c2.dataframe(regional.sort_values("avg_readmission_risk", ascending=False).head(10), use_container_width=True, hide_index=True)

    with tab3:
        search = st.text_input("Search hospitals", placeholder="Type a hospital, city, or state...")
        table = f.copy()

        if search:
            q = search.lower()
            mask = (
                table["hospital_name"].fillna("").str.lower().str.contains(q)
                | table["city"].fillna("").str.lower().str.contains(q)
                | table["state"].fillna("").str.lower().str.contains(q)
            )
            table = table[mask]

        cols = [
            "hospital_name",
            "city",
            "state",
            "composite_quality_score",
            "readmission_risk_score",
            "readmission_risk_label",
            "overall_patient_experience_score",
            "quality_tier",
        ]
        cols = [c for c in cols if c in table.columns]

        st.dataframe(
            table.sort_values("composite_quality_score", ascending=False)[cols].head(300),
            use_container_width=True,
            hide_index=True,
            column_config={
                "composite_quality_score": st.column_config.ProgressColumn("Quality", min_value=0, max_value=100, format="%.1f"),
                "readmission_risk_score": st.column_config.ProgressColumn("Risk", min_value=0, max_value=100, format="%.1f"),
                "overall_patient_experience_score": st.column_config.ProgressColumn("Patient Exp.", min_value=0, max_value=100, format="%.1f"),
            },
        )
