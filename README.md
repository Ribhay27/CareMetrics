# Clinical Performance & Readmission Risk Analytics Pipeline

An end-to-end hospital analytics platform using PostgreSQL, Airflow, dbt, XGBoost, LightGBM, SHAP, FastAPI, and Streamlit.

## What this project includes

- CMS hospital quality ingestion: Hospital General Information, HRRP readmissions, HCAHPS patient experience, Timely & Effective Care.
- Historical CMS snapshots for 2021 and 2022 trend views.
- CDC PLACES county-level community health data.
- PostgreSQL schemas: `raw`, `staging`, `intermediate`, `marts`.
- dbt staging, intermediate, and mart models.
- Airflow weekly pipeline DAG.
- ML feature engineering, readmission risk classifier, quality score regressor, and SHAP explainability artifacts.
- FastAPI backend with hospital, regional, trends, prediction, and natural language query endpoints.
- Streamlit dashboard with 8 analytical views.

## Local quickstart on Mac

### 1. Create the env file

```bash
cp .env.example .env
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Paste the generated key into `AIRFLOW_FERNET_KEY` in `.env`. Add your real `ANTHROPIC_API_KEY` only if you want the Claude Text-to-SQL page to work.

### 2. Start PostgreSQL first

```bash
docker compose up -d postgres
until docker exec hospital_postgres pg_isready -U hospital_user -d hospital_db; do sleep 2; done
docker exec -i hospital_postgres psql -U hospital_user -d hospital_db < init.sql
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python verify_setup.py
```

Expected final line: `ALL CHECKS PASSED`.

### 3. Download and load data

```bash
python download_data.py
python load_raw.py
```

The downloader prints a summary table. Every file should be `DOWNLOADED` or `SKIPPED` with more than 1,000 rows.

### 4. Build dbt models

```bash
cd dbt_project
export DBT_PROFILES_DIR=$PWD
dbt deps
dbt seed
dbt run
dbt test
cd ..
```

Expected dbt result: all models created and tests pass.

### 5. Train models and generate SHAP artifacts

```bash
python ml/feature_engineering.py
python ml/train_classifier.py
python ml/train_regressor.py
python ml/shap_analysis.py
```

Expected outputs:

- `data/processed/features.parquet`
- `data/processed/feature_metadata.json`
- `ml/models/readmission_classifier.pkl`
- `ml/models/quality_regressor.pkl`
- `data/processed/classifier_metrics.json`
- `data/processed/regressor_metrics.json`
- `data/processed/shap_classifier.parquet`
- `data/processed/shap_regressor.parquet`
- `data/processed/shap_classifier_summary.png`
- `data/processed/shap_regressor_summary.png`

### 6. Start API

```bash
uvicorn api.main:app --reload --port 8000
```

Open Swagger docs at `http://localhost:8000/docs`.

Useful endpoint tests:

```bash
curl http://localhost:8000/health
curl 'http://localhost:8000/hospitals?state=AZ&limit=5'
curl 'http://localhost:8000/hospitals/risk?state=AZ&risk_level=High&limit=5'
curl http://localhost:8000/regional/summary
curl http://localhost:8000/trends/030001
curl -X POST http://localhost:8000/hospitals/score \
  -H 'Content-Type: application/json' \
  -d '{"composite_quality_score":70,"readmission_risk_score":35,"patient_experience_score":75,"community_health_burden_score":45,"hospital_type_encoded":1,"ownership_encoded":1,"urban_rural_encoded":1,"state_avg_quality_score":65,"state_readmission_percentile":40}'
curl -X POST http://localhost:8000/nlq/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"What are the top 10 hospitals by quality score?"}'
```

### 7. Start dashboard

In another terminal:

```bash
streamlit run dashboard/app.py
```

Open `http://localhost:8501`. Use the sidebar to check all 8 pages.

### 8. Run Airflow pipeline

```bash
docker compose up -d --build airflow-webserver airflow-scheduler
```

Open `http://localhost:8080`, login with `admin` / `admin`, then trigger `hospital_pipeline_dag` manually. If a task fails, click the task square in the DAG graph, then choose **Logs**.

## Full Docker option

After your `.env` is set:

```bash
docker compose up -d --build
```

Services:

- PostgreSQL: `localhost:5432`
- Airflow: `http://localhost:8080`
- FastAPI: `http://localhost:8000`
- Streamlit: `http://localhost:8501`

## SQL validation query

```sql
select schemaname, tablename
from pg_tables
where schemaname in ('raw','staging','intermediate','marts')
order by schemaname, tablename;
```

## Streamlit Community Cloud deployment

1. Push this repo to GitHub.
2. In Streamlit Community Cloud, create a new app pointing to `dashboard/app.py`.
3. Add secrets/environment variables equivalent to `.env`: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST`, `POSTGRES_PORT`, `ANTHROPIC_API_KEY`, and `API_BASE_URL`.
4. Use a hosted PostgreSQL database. Streamlit Cloud cannot run this local Docker PostgreSQL instance.
5. Deploy the FastAPI backend separately, then set `API_BASE_URL` to that deployed API URL.

## Notes

Raw data and model artifacts are intentionally ignored by git. Rebuild them with the commands above.
