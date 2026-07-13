import importlib.util
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv


load_dotenv()

AUTHOR_NAME = os.getenv("AUTHOR_NAME", "Ribhay Singh")
GITHUB_URL = os.getenv("GITHUB_URL", "https://github.com/Ribhay27/CareMetrics")
LINKEDIN_URL = os.getenv("LINKEDIN_URL", "")

BASE_DIR = Path(__file__).parent
VIEWS_DIR = BASE_DIR / "views"

st.set_page_config(
    page_title="Care Metrics",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.4rem;
            padding-bottom: 3rem;
            max-width: 1420px;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #07111f 0%, #0b1728 55%, #111827 100%);
            border-right: 1px solid rgba(148, 163, 184, 0.14);
        }

        .brand-card {
            padding: 1.2rem;
            border-radius: 20px;
            background: linear-gradient(135deg, rgba(30, 58, 138, 0.72), rgba(15, 23, 42, 0.94));
            border: 1px solid rgba(147, 197, 253, 0.18);
            margin-bottom: 1rem;
        }

        .brand-title {
            font-size: 1.35rem;
            font-weight: 850;
            color: #f8fafc;
            margin-bottom: 0.4rem;
        }

        .brand-subtitle {
            font-size: 0.88rem;
            color: #cbd5e1;
            line-height: 1.5;
        }

        .built-by {
            padding: 0.85rem 0.95rem;
            border-radius: 16px;
            background: rgba(15, 23, 42, 0.76);
            border: 1px solid rgba(148, 163, 184, 0.15);
            margin-top: 1rem;
            margin-bottom: 1rem;
            color: #e2e8f0;
        }

        .hero {
            padding: 2.2rem 2.35rem;
            border-radius: 28px;
            background:
                radial-gradient(circle at top right, rgba(14, 165, 233, 0.22), transparent 35%),
                linear-gradient(135deg, rgba(15, 23, 42, 0.98), rgba(30, 41, 59, 0.86));
            border: 1px solid rgba(96, 165, 250, 0.18);
            box-shadow: 0 20px 55px rgba(0, 0, 0, 0.28);
            margin-bottom: 2rem;
        }

        .hero-kicker {
            color: #93c5fd;
            font-size: 0.82rem;
            font-weight: 800;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            margin-bottom: 0.45rem;
        }

        .hero-title {
            color: #f8fafc;
            font-size: 3rem;
            line-height: 1.05;
            font-weight: 900;
            letter-spacing: -0.045em;
            margin-bottom: 0.8rem;
        }

        .hero-subtitle {
            color: #cbd5e1;
            font-size: 1.05rem;
            max-width: 980px;
            line-height: 1.6;
        }

        .pill-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.65rem;
            margin-top: 1.2rem;
        }

        .pill {
            padding: 0.45rem 0.75rem;
            border-radius: 999px;
            background: rgba(15, 23, 42, 0.72);
            border: 1px solid rgba(148, 163, 184, 0.18);
            color: #e2e8f0;
            font-size: 0.86rem;
        }

        div[data-testid="stMetric"] {
            background: rgba(15, 23, 42, 0.72);
            padding: 1rem;
            border-radius: 18px;
            border: 1px solid rgba(148, 163, 184, 0.16);
        }

        h1, h2, h3 {
            letter-spacing: -0.025em;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


PAGES = [
    ("About Project", "00_about_project.py", "🏥"),
    ("National Overview", "01_national_overview.py", "📊"),
    ("Hospital Search", "02_hospital_search.py", "🔎"),
    ("Readmission Map", "03_readmission_map.py", "🗺️"),
    ("Quality Scorecard", "04_quality_scorecard.py", "🏆"),
    ("Community Health", "05_community_health.py", "🌎"),
    ("Risk Explainability", "06_risk_explainability.py", "🧠"),
    ("Performance Metrics", "07_performance_trends.py", "📈"),
    ("Natural Language Query", "08_natural_language_query.py", "💬"),
]


def load_view(file_name: str):
    path = VIEWS_DIR / file_name

    if not path.exists():
        st.error(f"View file not found: {path}")
        return

    module_name = f"caremetrics_{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)

    try:
        spec.loader.exec_module(module)
        if hasattr(module, "run"):
            module.run()
        else:
            st.warning(f"{file_name} does not define a run() function.")
    except Exception as exc:
        st.error("This dashboard view failed to load.")
        st.code(str(exc))


with st.sidebar:
    st.markdown(
        """
        <div class="brand-card">
            <div class="brand-title">🏥 Care Metrics</div>
            <div class="brand-subtitle">
                Hospital quality, readmission risk, patient experience, timely care,
                and community-health intelligence.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    selected = st.radio(
        "Navigation",
        PAGES,
        format_func=lambda item: f"{item[2]} {item[0]}",
    )

    st.markdown(
        f"""
        <div class="built-by">
            <b>Built by</b><br>
            {AUTHOR_NAME}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if GITHUB_URL:
        st.link_button("GitHub Repository", GITHUB_URL, width="stretch")

    if LINKEDIN_URL and "PASTE_YOUR" not in LINKEDIN_URL:
        st.link_button("LinkedIn", LINKEDIN_URL, width="stretch")
    else:
        st.caption("Add your real LINKEDIN_URL in .env to show the LinkedIn button.")

    st.markdown("---")
    st.caption("Python • PostgreSQL • dbt • XGBoost • LightGBM • SHAP • FastAPI • Streamlit")


st.markdown(
    f"""
    <div class="hero">
        <div class="hero-kicker">Flagship healthcare analytics project</div>
        <div class="hero-title">Care Metrics</div>
        <div class="hero-subtitle">
            Hospital quality and readmission-risk intelligence platform built from public CMS quality data,
            CDC PLACES indicators, dbt analytics marts, and explainable machine learning models.
            <br><br>
            Built by <b>{AUTHOR_NAME}</b>.
        </div>
        <div class="pill-row">
            <div class="pill">✅ Real CMS + CDC public datasets</div>
            <div class="pill">⚙️ Batch analytics pipeline</div>
            <div class="pill">🧱 PostgreSQL + dbt warehouse</div>
            <div class="pill">🧠 XGBoost / LightGBM + SHAP</div>
            <div class="pill">🚀 FastAPI + Streamlit</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

page_name, page_file, _ = selected
load_view(page_file)
