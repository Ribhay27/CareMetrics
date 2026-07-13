import os

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine


def get_engine():
    load_dotenv()
    user = os.getenv("POSTGRES_USER", "hospital_user")
    password = os.getenv("POSTGRES_PASSWORD", "hospital_password")
    host = os.getenv("POSTGRES_HOST", "127.0.0.1")
    port = os.getenv("POSTGRES_PORT", "55432")
    db = os.getenv("POSTGRES_DB", "hospital_db")

    url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    return create_engine(url)


@st.cache_data(ttl=300)
def load_performance_data():
    engine = get_engine()

    query = """
        SELECT *
        FROM marts.mart_hospital_performance
    """

    return pd.read_sql(query, engine)


def ensure_columns(df):
    defaults = {
        "hospital_name": "Unknown hospital",
        "city": "N/A",
        "state": "N/A",
        "hospital_type": "N/A",
        "composite_quality_score": pd.NA,
        "readmission_risk_score": pd.NA,
        "patient_experience_score": pd.NA,
        "readmission_risk_label": "Unknown",
        "quality_tier": "Unknown",
    }

    for col, default in defaults.items():
        if col not in df.columns:
            df[col] = default

    numeric_cols = [
        "composite_quality_score",
        "readmission_risk_score",
        "patient_experience_score",
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def run():
    st.title("Performance Metrics")
    st.caption("Compare hospital quality rankings, readmission-risk patterns, and provider-level performance metrics.")
    try:
        df = load_performance_data()
    except Exception as e:
        st.error("Could not load hospital performance data from PostgreSQL.")
        st.code(str(e))
        return

    if df.empty:
        st.error("No hospital performance data found.")
        return

    df = ensure_columns(df)

    df = df[df["hospital_name"].notna()].copy()

    states = ["All"] + sorted(df["state"].dropna().astype(str).unique().tolist())
    selected_state = st.selectbox("Filter by state", states)

    filtered = df.copy()

    if selected_state != "All":
        filtered = filtered[filtered["state"].astype(str) == selected_state]

    st.subheader("Current Performance Summary")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Hospitals", f"{len(filtered):,}")

    c2.metric(
        "Avg Quality Score",
        f"{filtered['composite_quality_score'].mean():.2f}"
        if filtered["composite_quality_score"].notna().any()
        else "N/A",
    )

    c3.metric(
        "Avg Readmission Risk",
        f"{filtered['readmission_risk_score'].mean():.2f}"
        if filtered["readmission_risk_score"].notna().any()
        else "N/A",
    )

    high_risk_count = (
        filtered["readmission_risk_label"]
        .fillna("")
        .astype(str)
        .str.lower()
        .eq("high")
        .sum()
    )

    c4.metric("High-Risk Hospitals", f"{high_risk_count:,}")

    st.subheader("Quality Score Distribution")

    quality_df = filtered.dropna(subset=["composite_quality_score"])

    if not quality_df.empty:
        fig = px.histogram(
            quality_df,
            x="composite_quality_score",
            nbins=35,
            title="Distribution of Composite Quality Scores",
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title="Composite Quality Score",
            yaxis_title="Hospital Count",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No quality score data available.")

    left, right = st.columns(2)

    with left:
        st.subheader("Top Performing Hospitals")
        top = (
            filtered.dropna(subset=["composite_quality_score"])
            .sort_values("composite_quality_score", ascending=False)
            .head(15)
        )

        st.dataframe(
            top[
                [
                    "hospital_name",
                    "city",
                    "state",
                    "composite_quality_score",
                    "readmission_risk_label",
                    "quality_tier",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

    with right:
        st.subheader("Highest Readmission Risk")
        risky = (
            filtered.dropna(subset=["readmission_risk_score"])
            .sort_values("readmission_risk_score", ascending=False)
            .head(15)
        )

        st.dataframe(
            risky[
                [
                    "hospital_name",
                    "city",
                    "state",
                    "readmission_risk_score",
                    "readmission_risk_label",
                    "composite_quality_score",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("Quality vs Readmission Risk")

    scatter_df = filtered.dropna(
        subset=["composite_quality_score", "readmission_risk_score"]
    )

    if not scatter_df.empty:
        fig = px.scatter(
            scatter_df,
            x="readmission_risk_score",
            y="composite_quality_score",
            color="readmission_risk_label",
            hover_data=["hospital_name", "city", "state"],
            title="Hospital Quality Score vs Readmission Risk",
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title="Readmission Risk Score",
            yaxis_title="Composite Quality Score",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough data for scatter plot.")

    st.subheader("Full Performance Table")

    table_cols = [
        "hospital_name",
        "city",
        "state",
        "hospital_type",
        "composite_quality_score",
        "readmission_risk_score",
        "patient_experience_score",
        "readmission_risk_label",
        "quality_tier",
    ]

    st.dataframe(
        filtered[table_cols].sort_values(
            "composite_quality_score",
            ascending=False,
            na_position="last",
        ),
        use_container_width=True,
        hide_index=True,
    )


if __name__ == "__main__":
    run()
