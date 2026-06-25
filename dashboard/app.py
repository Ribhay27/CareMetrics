from __future__ import annotations

import importlib.util
from pathlib import Path
import streamlit as st

st.set_page_config(page_title="Clinical Performance & Readmission Risk Analytics", layout="wide", page_icon="🏥")

st.markdown("""
<style>
.main-header {padding: 1rem; background: #111827; color: white; border-radius: 12px; margin-bottom: 1rem;}
.metric-card {padding: 1rem; border-radius: 12px; border: 1px solid #e5e7eb; background: #f9fafb;}
.risk-high {background:#fee2e2; padding:.35rem .65rem; border-radius:999px; color:#991b1b; font-weight:700;}
.risk-medium {background:#fef3c7; padding:.35rem .65rem; border-radius:999px; color:#92400e; font-weight:700;}
.risk-low {background:#dcfce7; padding:.35rem .65rem; border-radius:999px; color:#166534; font-weight:700;}
.callout {padding:1rem; background:#eef2ff; border-left:5px solid #4f46e5; border-radius:8px;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>Clinical Performance & Readmission Risk Analytics</h1><p>CMS hospital quality + CDC PLACES community health + ML explainability.</p></div>', unsafe_allow_html=True)

PAGES = {
    "National Overview": "pages/01_national_overview.py",
    "Hospital Search": "pages/02_hospital_search.py",
    "Readmission Map": "pages/03_readmission_map.py",
    "Quality Scorecard": "pages/04_quality_scorecard.py",
    "Community Health": "pages/05_community_health.py",
    "Risk Explainability": "pages/06_risk_explainability.py",
    "Performance Trends": "pages/07_performance_trends.py",
    "Natural Language Query": "pages/08_natural_language_query.py",
}

with st.sidebar:
    st.header("Navigation")
    page_name = st.radio("Choose a view", list(PAGES.keys()))
    st.markdown("---")
    st.caption("Real data only: mart tables, API endpoints, trained models, and SHAP artifacts.")

page_path = Path(__file__).resolve().parent / PAGES[page_name]
spec = importlib.util.spec_from_file_location("dashboard_page", page_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)  # type: ignore[union-attr]
module.run()
