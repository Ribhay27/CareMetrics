from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from airflow import DAG
from airflow.exceptions import AirflowException
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", "/opt/airflow/project"))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _run_python_script(script: str, *args: str) -> None:
    cmd = [sys.executable, str(PROJECT_ROOT / script), *args]
    result = subprocess.run(cmd, cwd=PROJECT_ROOT, text=True, capture_output=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if result.returncode != 0:
        raise AirflowException(f"Command failed: {' '.join(cmd)}")


def download_cms_data() -> None:
    for name in [
        "hospitals_general.csv",
        "hospitals_readmissions.csv",
        "hospitals_patient_experience.csv",
        "hospitals_timely_care.csv",
        "hospitals_general_2022.csv",
        "hospitals_readmissions_2022.csv",
        "hospitals_general_2021.csv",
        "hospitals_readmissions_2021.csv",
    ]:
        _run_python_script("download_data.py", "--only", name)


def download_cdc_data() -> None:
    _run_python_script("download_data.py", "--only", "cdc_places_county.csv")


def load_raw_to_postgres(**context) -> None:
    _run_python_script("load_raw.py")
    from sqlalchemy import create_engine, text
    from common.config import db_url
    engine = create_engine(db_url(host_override=os.getenv("POSTGRES_HOST", "postgres")))
    with engine.connect() as conn:
        rows = conn.execute(text("""
            select table_name,
                   (xpath('/row/c/text()', query_to_xml(format('select count(*) c from raw.%I', table_name), false, true, '')))[1]::text::int as row_count
            from information_schema.tables
            where table_schema='raw' and table_type='BASE TABLE'
            order by table_name
        """)).mappings().all()
    context["ti"].xcom_push(key="raw_row_counts", value=[dict(r) for r in rows])
    print(json.dumps([dict(r) for r in rows], indent=2))


def run_feature_engineering() -> None:
    _run_python_script("ml/feature_engineering.py")


def train_models() -> None:
    _run_python_script("ml/train_classifier.py")
    _run_python_script("ml/train_regressor.py")
    _run_python_script("ml/shap_analysis.py")


def validate_data_quality() -> None:
    from sqlalchemy import create_engine, text
    from common.config import db_url
    engine = create_engine(db_url(host_override=os.getenv("POSTGRES_HOST", "postgres")))
    checks = []
    with engine.connect() as conn:
        row_count = conn.execute(text("select count(*) from marts.mart_hospital_performance")).scalar_one()
        null_rate = conn.execute(text("""
            select avg(case when composite_quality_score is null then 1.0 else 0.0 end)
            from marts.mart_hospital_performance
        """)).scalar_one()
        max_label_share = conn.execute(text("""
            with counts as (
                select readmission_risk_label, count(*)::numeric c
                from marts.mart_hospital_performance
                group by 1
            ), total as (select sum(c) t from counts)
            select coalesce(max(c / nullif(t,0)), 0) from counts cross join total
        """)).scalar_one()
    checks.append(("mart_hospital_performance row count > 4000", row_count > 4000, row_count))
    checks.append(("composite_quality_score null rate < 20%", float(null_rate or 0) < 0.20, float(null_rate or 0)))
    checks.append(("risk label max category share <= 80%", float(max_label_share or 0) <= 0.80, float(max_label_share or 0)))
    model_dir = PROJECT_ROOT / "ml" / "models"
    checks.append(("classifier model exists", (model_dir / "readmission_classifier.pkl").exists(), str(model_dir)))
    checks.append(("regressor model exists", (model_dir / "quality_regressor.pkl").exists(), str(model_dir)))
    failed = []
    for name, ok, value in checks:
        print(f"{'PASS' if ok else 'FAIL'} {name}: {value}")
        if not ok:
            failed.append(name)
    if failed:
        raise AirflowException(f"Critical data quality checks failed: {failed}")


with DAG(
    dag_id="hospital_pipeline_dag",
    schedule="@weekly",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["healthcare", "pipeline", "dbt"],
) as dag:
    t_download_cms = PythonOperator(task_id="download_cms_data", python_callable=download_cms_data)
    t_download_cdc = PythonOperator(task_id="download_cdc_data", python_callable=download_cdc_data)
    t_load = PythonOperator(task_id="load_raw_to_postgres", python_callable=load_raw_to_postgres)
    dbt_env = {
        "DBT_PROFILES_DIR": str(PROJECT_ROOT / "dbt_project"),
        "POSTGRES_HOST": os.getenv("POSTGRES_HOST", "postgres"),
        "POSTGRES_PORT": os.getenv("POSTGRES_PORT", "5432"),
        "POSTGRES_USER": os.getenv("POSTGRES_USER", "hospital_user"),
        "POSTGRES_PASSWORD": os.getenv("POSTGRES_PASSWORD", "hospital_password"),
        "POSTGRES_DB": os.getenv("POSTGRES_DB", "hospital_db"),
    }
    t_dbt_staging = BashOperator(
        task_id="run_dbt_staging",
        bash_command="cd $PROJECT_ROOT/dbt_project && dbt run --select staging && dbt test --select staging",
        env=dbt_env,
    )
    t_dbt_intermediate = BashOperator(
        task_id="run_dbt_intermediate",
        bash_command="cd $PROJECT_ROOT/dbt_project && dbt run --select intermediate && dbt test --select intermediate",
        env=dbt_env,
    )
    t_dbt_marts = BashOperator(
        task_id="run_dbt_marts",
        bash_command="cd $PROJECT_ROOT/dbt_project && dbt run --select marts && dbt test --select marts",
        env=dbt_env,
    )
    t_features = PythonOperator(task_id="run_feature_engineering", python_callable=run_feature_engineering)
    t_train = PythonOperator(task_id="train_models", python_callable=train_models)
    t_validate = PythonOperator(task_id="validate_data_quality", python_callable=validate_data_quality)

    [t_download_cms, t_download_cdc] >> t_load >> t_dbt_staging >> t_dbt_intermediate >> t_dbt_marts >> t_features >> t_train >> t_validate
