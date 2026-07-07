from __future__ import annotations

import importlib.util
from pathlib import Path
import streamlit as st

st.set_page_config(
    page_title="Clinical Performance Analytics",
    layout="wide",
    page_icon="🏥",
    initial_sidebar_state="expanded",
)

APP_DIR = Path(__file__).resolve().parent

PAGES = {
    "National Overview": {"icon": "🏥", "path": "views/01_national_overview.py", "desc": "Executive KPIs, maps, and national trends"},
    "Hospital Search": {"icon": "🔎", "path": "views/02_hospital_search.py", "desc": "Find and compare providers"},
    "Readmission Map": {"icon": "🗺️", "path": "views/03_readmission_map.py", "desc": "Geographic risk exploration"},
    "Quality Scorecard": {"icon": "📊", "path": "views/04_quality_scorecard.py", "desc": "Ranked provider scorecard"},
    "Community Health": {"icon": "🌎", "path": "views/05_community_health.py", "desc": "CDC PLACES context"},
    "Risk Explainability": {"icon": "🧠", "path": "views/06_risk_explainability.py", "desc": "SHAP model drivers"},
    "Performance Trends": {"icon": "📈", "path": "views/07_performance_trends.py", "desc": "Historical snapshots"},
    "Natural Language Query": {"icon": "💬", "path": "views/08_natural_language_query.py", "desc": "Ask questions in plain English"},
}

st.markdown("""
<style>
:root {
  --bg: #020617;
  --panel: rgba(15, 23, 42, 0.78);
  --stroke: rgba(148, 163, 184, 0.18);
  --text: #e5eefb;
  --muted: #94a3b8;
  --accent: #38bdf8;
  --accent2: #a78bfa;
}

.stApp {
  background:
    radial-gradient(circle at 18% 10%, rgba(56, 189, 248, .14), transparent 32%),
    radial-gradient(circle at 85% 5%, rgba(167, 139, 250, .16), transparent 35%),
    linear-gradient(135deg, #020617 0%, #08111f 45%, #030712 100%);
}

.block-container {
  max-width: 1280px;
  padding-top: 2.2rem;
  padding-bottom: 4rem;
}

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, rgba(15,23,42,.98), rgba(2,6,23,.98));
  border-right: 1px solid var(--stroke);
}

.sidebar-brand {
  padding: 1rem;
  border: 1px solid var(--stroke);
  border-radius: 22px;
  background: linear-gradient(135deg, rgba(56,189,248,.14), rgba(167,139,250,.12));
  margin-bottom: 1rem;
}

.sidebar-brand h2 {
  font-size: 1.35rem;
  margin: 0;
  letter-spacing: -0.03em;
  color: white;
}

.sidebar-brand p {
  margin: .35rem 0 0;
  color: var(--muted);
  font-size: .86rem;
}

.hero {
  position: relative;
  overflow: hidden;
  padding: 2rem;
  border-radius: 28px;
  border: 1px solid rgba(56,189,248,.18);
  background: linear-gradient(135deg, rgba(15,23,42,.96), rgba(15,23,42,.72));
  box-shadow: 0 24px 80px rgba(0,0,0,.28);
  margin-bottom: 1.55rem;
}

.hero:after {
  content: "";
  position: absolute;
  right: -90px;
  top: -90px;
  width: 260px;
  height: 260px;
  border-radius: 999px;
  background: radial-gradient(circle, rgba(56,189,248,.28), transparent 62%);
}

.hero h1 {
  font-size: clamp(2rem, 4vw, 4rem);
  line-height: .98;
  margin: 0;
  letter-spacing: -0.065em;
  color: white;
  max-width: 980px;
}

.hero p {
  margin: 1rem 0 0;
  color: #cbd5e1;
  font-size: 1.05rem;
}

.chips {
  display: flex;
  gap: .55rem;
  flex-wrap: wrap;
  margin-top: 1.2rem;
}

.chip {
  display:inline-flex;
  align-items:center;
  gap:.4rem;
  padding:.48rem .72rem;
  border-radius: 999px;
  border:1px solid rgba(148,163,184,.22);
  background: rgba(2,6,23,.42);
  color:#dbeafe;
  font-size:.84rem;
}

.page-title {
  display:flex;
  align-items:end;
  justify-content:space-between;
  gap:1rem;
  margin: .8rem 0 1rem;
}

.page-title h2 {
  margin:0;
  font-size:2.1rem;
  letter-spacing:-.045em;
  color:white;
}

.page-title p {
  margin:.35rem 0 0;
  color:var(--muted);
}

.metric-card {
  height: 100%;
  padding: 1.15rem;
  border-radius: 22px;
  border: 1px solid var(--stroke);
  background: linear-gradient(180deg, rgba(15,23,42,.88), rgba(15,23,42,.55));
  box-shadow: 0 18px 50px rgba(0,0,0,.18);
}

.metric-card .label {
  color: var(--muted);
  font-size:.82rem;
  text-transform: uppercase;
  letter-spacing:.08em;
}

.metric-card .value {
  font-size: 2.1rem;
  font-weight: 800;
  color: white;
  letter-spacing:-.05em;
  margin-top:.35rem;
}

.metric-card .delta {
  font-size:.86rem;
  color:#cbd5e1;
  margin-top:.25rem;
}

.glass-card {
  padding: 1.1rem;
  border-radius: 24px;
  border: 1px solid var(--stroke);
  background: rgba(15,23,42,.62);
  box-shadow: 0 18px 70px rgba(0,0,0,.16);
}

.stTabs [data-baseweb="tab-list"] {
  gap: .5rem;
}

.stTabs [data-baseweb="tab"] {
  border-radius: 999px;
  padding: .5rem 1rem;
  background: rgba(15,23,42,.65);
  border:1px solid var(--stroke);
}

.stTabs [aria-selected="true"] {
  background: linear-gradient(135deg, rgba(56,189,248,.28), rgba(167,139,250,.22));
  color:white;
}

.risk-high, .risk-medium, .risk-low {
  padding:.36rem .7rem;
  border-radius:999px;
  font-weight:800;
  border:1px solid transparent;
}

.risk-high {background:rgba(251,113,133,.14); color:#fecdd3; border-color:rgba(251,113,133,.35);}
.risk-medium {background:rgba(251,191,36,.13); color:#fde68a; border-color:rgba(251,191,36,.35);}
.risk-low {background:rgba(52,211,153,.13); color:#bbf7d0; border-color:rgba(52,211,153,.35);}

.callout {
  padding:1rem;
  border-radius:18px;
  border:1px solid rgba(56,189,248,.22);
  background:rgba(56,189,248,.08);
  color:#dbeafe;
}

hr {border-color: rgba(148,163,184,.18);}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown(
        '<div class="sidebar-brand"><h2>PulseCare AI</h2><p>Hospital quality, readmission risk, and community-health intelligence.</p></div>',
        unsafe_allow_html=True,
    )
    page_name = st.radio(
        "Navigation",
        list(PAGES.keys()),
        format_func=lambda name: f"{PAGES[name]['icon']}  {name}",
    )
    st.markdown("---")
    st.caption(PAGES[page_name]["desc"])
    st.markdown("---")
    st.caption("Real CMS + CDC data • PostgreSQL • dbt marts • ML + SHAP")

st.markdown("""
<section class="hero">
  <h1>Clinical Performance & Readmission Risk Analytics</h1>
  <p>Executive-grade hospital intelligence built from public CMS quality data, CDC PLACES indicators, dbt marts, and explainable ML models.</p>
  <div class="chips">
    <span class="chip">✅ Real public datasets</span>
    <span class="chip">⚙️ Batch data pipeline</span>
    <span class="chip">🧱 PostgreSQL + dbt</span>
    <span class="chip">🧠 XGBoost / LightGBM + SHAP</span>
  </div>
</section>
""", unsafe_allow_html=True)

page_path = APP_DIR / PAGES[page_name]["path"]
spec = importlib.util.spec_from_file_location("dashboard_page", page_path)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)
module.run()
