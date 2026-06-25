FROM apache/airflow:2.8.0

ENV AIRFLOW_HOME=/opt/airflow
ENV PROJECT_ROOT=/opt/airflow/project

USER root
RUN apt-get update && apt-get install -y --no-install-recommends build-essential git curl && rm -rf /var/lib/apt/lists/*
USER airflow

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY dbt_project/ /opt/airflow/project/dbt_project/
COPY download_data.py load_raw.py /opt/airflow/project/
COPY ml/ /opt/airflow/project/ml/
