# CareMetrics — Hospital Quality & Readmission Risk Intelligence Platform

CareMetrics is an end-to-end healthcare analytics platform that turns public CMS hospital-quality data and CDC community-health data into hospital-level insights, readmission-risk analysis, quality rankings, model explainability, and an interactive Streamlit dashboard.

The project was built to understand how a complete data product works from raw data ingestion to database modeling, analytics engineering, machine learning, API serving, and dashboard delivery.



## What This Project Solves

Hospital performance data is public, but it is spread across multiple datasets and is difficult to compare directly.

CareMetrics brings together hospital information, readmission measures, patient experience data, timely-care performance, and CDC community-health indicators into one structured analytics platform.

The project helps answer questions like:

- Which hospitals are performing best overall?
- Which hospitals have higher readmission risk?
- How do hospitals compare across states and regions?
- How do patient experience and timely-care metrics relate to quality?
- How does community-health burden affect hospital performance?
- Which factors influence machine-learning model outputs?

Instead of only building a standalone machine-learning model, this project focuses on the full data lifecycle: ingestion, storage, transformation, validation, modeling, explainability, API development, and dashboarding.

---

## Datasets Used

CareMetrics uses public healthcare datasets from CMS and CDC.

### CMS Hospital Data

- Hospital General Information
- Hospital Readmissions / HRRP measures
- HCAHPS Patient Experience
- Timely and Effective Care

### CDC Community Health Data

- CDC PLACES county-level community-health indicators

These datasets are loaded into PostgreSQL, transformed with dbt, and combined into final analytics marts used by the dashboard and modeling workflows.

---

## Technical Architecture

```text
CMS / CDC public datasets
        ↓
Python ingestion scripts
        ↓
PostgreSQL raw tables
        ↓
dbt staging models
        ↓
dbt intermediate models
        ↓
dbt analytics marts
        ↓
Feature engineering
        ↓
XGBoost + LightGBM models
        ↓
SHAP explainability
        ↓
FastAPI backend
        ↓
Streamlit dashboard
```

---

## Core Features

### National Overview

Provides an executive-level summary of hospital performance, including:

- Hospital count
- Average quality score
- Average readmission-risk score
- Average patient-experience score
- Readmission-risk distribution
- Hospital mix by type
- State-level performance summaries

### Hospital Search

Allows users to search and compare hospitals by:

- Hospital name
- City
- State
- Hospital type
- Composite quality score
- Readmission-risk score
- Readmission-risk label
- Quality tier

### Readmission Risk Analysis

Classifies hospitals into readmission-risk groups:

- Low risk
- Medium risk
- High risk

This helps identify hospitals that may need closer review around patient readmissions and care outcomes.

### Quality Scorecard

Ranks hospitals using a composite quality score and compares providers across quality tiers.

This helps surface:

- Top-performing hospitals
- Lower-performing hospitals
- State and regional quality differences
- Provider-level performance patterns

### Community Health Analysis

Incorporates CDC community-health indicators to give hospital performance additional regional context.

This helps analyze how community health burden may relate to hospital outcomes and readmission risk.

### Risk Explainability

Uses SHAP analysis to interpret machine-learning model outputs.

Instead of only showing a prediction, the explainability layer helps identify which features influenced risk or quality estimates.

### Performance Metrics

Provides additional hospital-level and regional performance comparisons, including quality distributions, risk patterns, and provider-level summaries.

### Natural Language Query

Includes an optional natural-language query feature for asking plain-English questions against the analytics layer.

This feature is designed as an experimental Text-to-SQL style interface.

---

## Data Engineering

The project uses a layered warehouse structure in PostgreSQL:

```text
raw
staging
intermediate
marts
```

### Raw Layer

Stores source data loaded from CMS and CDC files.

Example raw tables:

```text
raw.hospitals_general
raw.hospitals_readmissions
raw.hospitals_patient_experience
raw.hospitals_timely_care
raw.cdc_places_county
```

### Staging Layer

Standardizes raw tables by cleaning column names, casting data types, and preparing source data for transformation.

### Intermediate Layer

Combines and prepares hospital-level metrics, scoring logic, and supporting transformations.

### Marts Layer

Final dashboard-ready analytics tables.

Main marts:

```text
marts.mart_hospital_performance
marts.mart_readmission_risk
marts.mart_regional_summary
```

These marts power the Streamlit dashboard, API endpoints, and public demo database snapshot.

---

## Machine Learning

CareMetrics includes machine-learning workflows for hospital performance analysis.

### Models

- **XGBoost** for readmission-risk classification
- **LightGBM** for hospital quality-score estimation
- **SHAP** for model explainability

### ML Workflow

```text
dbt marts
   ↓
feature engineering
   ↓
model training
   ↓
metrics evaluation
   ↓
SHAP explainability
   ↓
dashboard/API outputs
```

The quality-score regression model achieved approximately **0.84 R²** during experimentation.

---

## Backend API

The project includes a FastAPI backend for serving hospital analytics and model-related outputs.

The API supports functionality such as:

- Health checks
- Hospital search
- High-risk hospital filtering
- Regional summaries
- Hospital scoring
- Natural-language query endpoint

Local Swagger docs are available at:

```text
http://localhost:8000/docs
```

---

## Dashboard

The Streamlit dashboard includes 8 analytical views:

```text
About Project
National Overview
Hospital Search
Readmission Map
Quality Scorecard
Community Health
Risk Explainability
Performance Metrics
Natural Language Query
```

The dashboard is designed to make the analytics layer accessible through search, filters, rankings, charts, maps, and explainability views.

---

## Tech Stack

### Languages and Libraries

- Python
- SQL
- pandas
- NumPy
- scikit-learn
- XGBoost
- LightGBM
- SHAP

### Data Engineering

- PostgreSQL
- dbt
- Docker
- SQLAlchemy
- Airflow

### Backend and Dashboard

- FastAPI
- Streamlit
- Plotly

### Deployment

- GitHub
- Streamlit Community Cloud
- SQLite public demo fallback
