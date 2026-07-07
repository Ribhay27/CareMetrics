from __future__ import annotations

import compileall
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REQUIRED = [
    'docker-compose.yml', '.env.example', 'init.sql', 'requirements.txt', 'download_data.py', 'load_raw.py',
    'dbt_project/dbt_project.yml', 'dbt_project/profiles.yml',
    'airflow/dags/hospital_pipeline_dag.py', 'ml/feature_engineering.py', 'api/main.py', 'dashboard/app.py'
]

missing = [f for f in REQUIRED if not (ROOT / f).exists()]
if missing:
    raise SystemExit(f'Missing files: {missing}')
print('PASS required files exist')

ok = compileall.compile_dir(str(ROOT), quiet=1)
if not ok:
    raise SystemExit('FAIL Python compile check')
print('PASS Python files compile')
print('Smoke test complete. Full integration test requires Docker/PostgreSQL and downloaded data.')
