# CareMetrics

# Clinical Performance & Readmission Risk Analytics Pipeline

> An end-to-end healthcare analytics platform that ingests CMS hospital quality and CDC community health datasets, models hospital readmission and quality risk using XGBoost and LightGBM, and serves insights through a FastAPI backend, LLM-powered natural language query interface, and an 8-view public Streamlit dashboard.

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![Airflow](https://img.shields.io/badge/Apache%20Airflow-2.8-017CEE)](https://airflow.apache.org)
[![dbt](https://img.shields.io/badge/dbt-core-FF694B)](https://getdbt.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791)](https://postgresql.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.33-FF4B4B)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## Overview

Hospital readmission rates and quality scores vary significantly across the United States — yet raw performance metrics rarely tell the full story. A hospital serving a high-burden community with elevated rates of diabetes, obesity, and smoking faces a fundamentally different operating environment than one in a healthier region.

This platform addresses that gap by combining **CMS hospital performance data** with **CDC county-level community health indicators** to produce risk-adjusted hospital quality intelligence. The system ingests 5,000+ hospitals across multiple CMS release years, models readmission and quality risk, explains predictions with SHAP values, and exposes everything through a production-grade API and interactive dashboard — including a natural language query interface that converts plain-English questions into SQL using a Claude-powered Text-to-SQL pipeline.

**Live Dashboard:** [View on Streamlit Community Cloud](#) *(link added after deployment)*  
**API Docs:** [FastAPI Swagger UI](http://localhost:8000/docs) *(local)*

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                         │
│  CMS Hospital Quality  │  CMS Readmissions  │  CDC PLACES   │
│  (General Info, HCAHPS,│  Reduction Program │  County-Level │
│   Timely/Effective Care│  2021 / 2022 / 2023│  Health Data  │
└────────────┬───────────┴────────┬───────────┴───────┬───────┘
             │                   │                   │
             ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                  APACHE AIRFLOW (Docker)                     │
│  DAG: download → load_raw → dbt_staging → dbt_intermediate  │
│       → dbt_marts → feature_engineering → train_models      │
│       → validate_data_quality                               │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              POSTGRESQL 15 (Docker)                          │
│  Schema: raw → staging → intermediate → marts               │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    DBT MODELS                        │   │
│  │  Staging: stg_hospitals, stg_readmissions,          │   │
│  │           stg_patient_experience, stg_timely_care,  │   │
│  │           stg_community_health                      │   │
│  │  Intermediate: int_hospital_scores,                 │   │
│  │                int_community_risk                   │   │
│  │  Marts: mart_hospital_performance,                  │   │
│  │         mart_readmission_risk, mart_regional_summary│   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    ML LAYER                                  │
│  Model 1: XGBoost Classifier → Readmission Risk (Low/Med/Hi)│
│  Model 2: LightGBM Regressor → Quality Score (0-100)        │
│  Explainability: SHAP values for both models                 │
│  Trend Analysis: Year-over-year performance (2021-2023)      │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  FASTAPI BACKEND                             │
│  /hospitals          /hospitals/{id}    /hospitals/risk      │
│  /hospitals/score    /regional/summary  /trends/{id}         │
│  /nlq/query (Text-to-SQL via Claude API)  /health           │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              STREAMLIT DASHBOARD (8 Views)                   │
│  1. National Overview      5. Community Health Context       │
│  2. Hospital Search        6. Risk Explainability (SHAP)     │
│  3. Readmission Risk Map   7. Performance Trends             │
│  4. Quality Scorecard      8. Natural Language Query         │
└─────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Orchestration | Apache Airflow 2.8 | Pipeline scheduling and task dependency management |
| Transformation | dbt-core | SQL-based data modeling across 8 models in 3 layers |
| Storage | PostgreSQL 15 | Raw, staging, intermediate, and mart schema layers |
| Infrastructure | Docker Compose | Containerized Airflow and PostgreSQL instances |
| ML — Classification | XGBoost | Hospital readmission risk categorization (Low/Med/High) |
| ML — Regression | LightGBM | Composite hospital quality score prediction (0–100) |
| Explainability | SHAP | Feature importance and per-hospital prediction explanations |
| Forecasting | Prophet | Year-over-year performance trend analysis |
| API | FastAPI | Prediction serving and natural language query endpoint |
| AI / NLQ | Claude API (claude-sonnet-4-6) | Text-to-SQL pipeline with schema injection and result summarization |
| Dashboard | Streamlit | 8-view interactive public analytics dashboard |
| Mapping | Plotly Express + Folium | Choropleth and scatter map visualizations |
| Data Processing | pandas, NumPy | Data cleaning and feature engineering |
| Language | Python 3.11 | Primary language across all pipeline components |

---

## Data Sources

All datasets are publicly available at no cost and require no API key.

| Dataset | Source | Records | Description |
|---|---|---|---|
| Hospital General Information | CMS Provider Data | 5,000+ hospitals | Facility type, ownership, location, overall rating |
| Hospital Readmissions Reduction Program | CMS Provider Data | 5,000+ hospitals | Readmission rates by condition and measure |
| Patient Experience (HCAHPS) | CMS Provider Data | 5,000+ hospitals | Patient-reported experience scores |
| Timely and Effective Care | CMS Provider Data | 5,000+ hospitals | Emergency care and process-of-care measures |
| CMS Historical Releases | CMS Provider Data | 2021, 2022, 2023 | Multi-year snapshots for trend analysis |
| CDC PLACES | CDC Open Data | 3,000+ counties | County-level chronic disease and health behavior prevalence |

---

## Project Structure

```
clinical-performance-readmission-risk-pipeline/
├── docker-compose.yml          # Airflow + PostgreSQL containers
├── .env.example                # Environment variable template
├── requirements.txt            # All Python dependencies
├── README.md
├── data/
│   ├── raw/                    # Landing zone for downloaded CSVs
│   └── processed/              # Feature matrices, SHAP values, model metrics
├── airflow/
│   ├── Dockerfile
│   └── dags/
│       └── hospital_pipeline_dag.py   # Full orchestration DAG
├── dbt_project/
│   ├── dbt_project.yml
│   ├── profiles.yml
│   └── models/
│       ├── staging/            # stg_hospitals, stg_readmissions, stg_patient_experience,
│       │                       # stg_timely_care, stg_community_health
│       ├── intermediate/       # int_hospital_scores, int_community_risk
│       └── marts/              # mart_hospital_performance, mart_readmission_risk,
│                               # mart_regional_summary
├── ml/
│   ├── feature_engineering.py  # Feature extraction from mart tables
│   ├── train_classifier.py     # XGBoost readmission risk classifier
│   ├── train_regressor.py      # LightGBM quality score regressor
│   ├── shap_analysis.py        # SHAP value computation for both models
│   └── models/                 # Serialized model artifacts (.pkl)
├── api/
│   ├── main.py                 # FastAPI application entry point
│   ├── models.py               # Pydantic request/response schemas
│   ├── routes/
│   │   ├── predictions.py      # /hospitals/score endpoint
│   │   ├── hospitals.py        # Hospital query endpoints
│   │   └── nlq.py              # Natural language query endpoint
│   └── text_to_sql/
│       ├── prompt_builder.py   # Few-shot prompt construction
│       ├── schema_injector.py  # Dynamic schema context injection
│       ├── query_validator.py  # SQL parsing and column validation
│       └── result_summarizer.py # LLM-powered plain-English result summaries
└── dashboard/
    ├── app.py                  # Streamlit multi-page entry point
    ├── pages/                  # 8 individual dashboard pages
    └── utils/
        ├── db.py               # PostgreSQL connection utilities
        ├── api_client.py       # FastAPI client wrapper
        └── charts.py           # Reusable Plotly chart components
```

---

## Key Features

**Dual ML Models**
XGBoost classifier predicting readmission risk category (Low / Medium / High) and LightGBM regressor predicting a composite quality score (0–100), both trained on hospital performance metrics and community health context with cross-validation and hyperparameter tuning.

**Community Health Context**
Connects hospital-level performance to CDC county-level health burden indicators — diabetes prevalence, obesity rates, smoking rates, poor health percentage — providing risk-adjusted context that raw readmission scores alone cannot capture.

**SHAP Explainability**
Per-hospital SHAP waterfall charts explain exactly which features drove each prediction. Global summary plots surface the most influential features across all 5,000+ hospitals.

**LLM-Powered Natural Language Query**
A production-grade Text-to-SQL pipeline using the Claude API with dynamic schema injection, SQL syntax validation, automatic error recovery with retry logic, and plain-English result summarization. Users type questions in natural language and receive both the generated SQL and a human-readable answer.

**Multi-Year Trend Analysis**
Three years of CMS data (2021–2023) enable year-over-year hospital performance tracking, identifying improving and declining facilities nationally.

**Production-Grade Pipeline**
Apache Airflow DAG orchestrates the full pipeline from data ingestion through model training on a weekly schedule, with data quality validation checks and failure logging at each stage.

---

## Dashboard Pages

| Page | Description |
|---|---|
| National Overview | Summary metrics, quality score distribution, readmission risk distribution, state-level choropleth map |
| Hospital Search | Search by name, city, or state — full hospital profile with risk badge, SHAP waterfall, and comparison tool |
| Readmission Risk Map | Interactive US map with hospitals colored by risk level and state-level choropleth overlay |
| Quality Scorecard | Sortable, filterable table of all hospitals with export to CSV |
| Community Health Context | Scatter plots connecting readmission risk to diabetes, obesity, and smoking prevalence by county |
| Risk Explainability | Per-hospital and global SHAP visualizations for both ML models |
| Performance Trends | Year-over-year quality score and readmission rate trends with national comparison |
| Natural Language Query | Plain-English question interface powered by Claude Text-to-SQL pipeline |

---

## Setup & Installation

### Prerequisites

- Docker Desktop (running)
- Python 3.11
- Claude API key from [console.anthropic.com](https://console.anthropic.com)

### 1. Clone the Repository

```bash
git clone https://github.com/Ribhay27/clinical-performance-readmission-risk-pipeline.git
cd clinical-performance-readmission-risk-pipeline
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` and fill in:

```
POSTGRES_USER=hospital_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=hospital_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
ANTHROPIC_API_KEY=your_claude_api_key
AIRFLOW_FERNET_KEY=your_fernet_key
```

### 3. Start Docker Services

```bash
docker-compose up -d
```

This starts PostgreSQL 15 on port 5432 and Airflow 2.8 on port 8080. Wait 60 seconds for Airflow to initialize.

Verify both are running:

```bash
docker-compose ps
```

### 4. Install Python Dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. Initialize PostgreSQL Schema

```bash
psql -h localhost -U hospital_user -d hospital_db -f init.sql
```

### 6. Run dbt Models

```bash
cd dbt_project
dbt deps
dbt run
dbt test
```

### 7. Trigger the Airflow DAG

Open [http://localhost:8080](http://localhost:8080) in your browser (user: `airflow`, password: `airflow`).

Enable and trigger the `hospital_pipeline_dag` DAG. This will:
- Download all CMS and CDC datasets
- Load raw data into PostgreSQL
- Run all dbt models
- Engineer features and train both ML models
- Validate data quality

Estimated runtime: 15–25 minutes on first run.

### 8. Start the FastAPI Backend

```bash
cd api
uvicorn main:app --reload --port 8000
```

API documentation available at [http://localhost:8000/docs](http://localhost:8000/docs)

### 9. Launch the Streamlit Dashboard

```bash
cd dashboard
streamlit run app.py
```

Dashboard available at [http://localhost:8501](http://localhost:8501)

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/hospitals` | List hospitals with optional filters (state, risk_level, quality_min) |
| GET | `/hospitals/{provider_id}` | Full hospital profile with scores and SHAP explanation |
| GET | `/hospitals/risk?state=AZ` | Hospitals filtered by state and risk level |
| POST | `/hospitals/score` | Input hospital metrics, receive predicted risk + quality score |
| GET | `/regional/summary` | State-level aggregations for map visualization |
| GET | `/trends/{provider_id}` | Year-over-year performance history for one hospital |
| POST | `/nlq/query` | Natural language question → SQL → results → plain-English summary |
| GET | `/health` | Service health check |

---

## Key Findings

*(Updated after full dataset ingestion)*

- Southern states consistently show higher readmission risk scores when controlling for hospital type and ownership
- County-level diabetes prevalence shows the strongest correlation with hospital readmission rates among all community health indicators analyzed
- Critical Access Hospitals in rural counties face a compounding risk — lower quality scores combined with higher community health burden — suggesting raw quality rankings systematically underrate rural facility performance
- Non-profit hospitals outperform for-profit facilities on patient experience scores across all hospital size categories

---

## Deployment

To deploy the Streamlit dashboard publicly on Streamlit Community Cloud:

1. Push repository to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Select this repository and set main file to `dashboard/app.py`
5. Add environment variables in the Streamlit Cloud secrets manager
6. Deploy — public URL generated automatically

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Author

**Ribhay Singh**  
[LinkedIn](https://www.linkedin.com/in/ribhaysingh/) · [GitHub](https://github.com/Ribhay27) · [Portfolio](https://ribhaysingh.vercel.app)
