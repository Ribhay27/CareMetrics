import os

import streamlit as st
from dotenv import load_dotenv


def run():
    load_dotenv()

    author = os.getenv("AUTHOR_NAME", "Ribhay Singh")
    github = os.getenv("GITHUB_URL", "https://github.com/Ribhay27/CareMetrics")
    linkedin = os.getenv("LINKEDIN_URL", "")

    st.title("About Care Metrics")
    st.caption("Hospital Quality & Readmission Risk Intelligence Platform")

    st.markdown(
        """
        **Care Metrics** turns raw CMS and CDC public healthcare datasets into an analytics platform
        for evaluating hospital quality, readmission risk, patient experience, timely-care performance,
        community-health burden, and regional provider benchmarks.
        """
    )

    st.subheader("What this project does")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            """
            **Hospital performance**
            - Composite quality scores
            - Provider-level rankings
            - State and regional benchmarks
            """
        )

    with c2:
        st.markdown(
            """
            **Readmission intelligence**
            - Low / medium / high risk labels
            - High-risk hospital identification
            - Risk and quality comparisons
            """
        )

    with c3:
        st.markdown(
            """
            **Explainable ML**
            - XGBoost risk classification
            - LightGBM quality prediction
            - SHAP feature explanations
            """
        )

    st.subheader("How to use the dashboard")

    st.markdown(
        """
        - Use **National Overview** for executive KPIs and national performance summaries.
        - Use **Hospital Search** to inspect specific providers.
        - Use **Quality Scorecard** to compare top and bottom hospitals.
        - Use **Community Health** to connect CDC public-health indicators with hospital outcomes.
        - Use **Risk Explainability** to understand model-driven risk factors.
        - Use **Performance Metrics** to compare rankings, distributions, and quality-risk relationships.
        """
    )

    st.subheader("Technical architecture")

    st.code(
        """CMS/CDC public datasets
→ Python ingestion pipeline
→ Dockerized PostgreSQL database
→ dbt staging, intermediate, and mart models
→ XGBoost / LightGBM / SHAP machine learning layer
→ FastAPI backend
→ Streamlit analytics dashboard""",
        language="text",
    )

    st.subheader("Built by")
    st.write(f"**{author}**")

    col1, col2 = st.columns(2)

    with col1:
        if github:
            st.link_button("GitHub Repository", github, width="stretch")

    with col2:
        if linkedin and "PASTE_YOUR" not in linkedin:
            st.link_button("LinkedIn", linkedin, width="stretch")
        else:
            st.info("Add your real LinkedIn URL in `.env` as `LINKEDIN_URL=...`.")
