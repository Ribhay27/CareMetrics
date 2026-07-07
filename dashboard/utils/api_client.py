from __future__ import annotations

import os
import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")


def _get(path: str, params: dict | None = None):
    try:
        r = requests.get(f"{API_BASE_URL}{path}", params={k:v for k,v in (params or {}).items() if v not in (None, "")}, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        st.error(f"API request failed: {exc}")
        return [] if path != "/health" else {"status": "error"}


def _post(path: str, payload: dict):
    try:
        r = requests.post(f"{API_BASE_URL}{path}", json=payload, timeout=90)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        st.error(f"API request failed: {exc}")
        return {}


def get_hospitals(state=None, risk_level=None, quality_min=None, limit=100):
    return _get("/hospitals", {"state": state, "risk_level": risk_level, "quality_min": quality_min, "limit": limit})

def get_hospital_profile(provider_id: str):
    return _get(f"/hospitals/{provider_id}")

def score_hospital(metrics: dict):
    return _post("/hospitals/score", metrics)

def get_regional_summary():
    return _get("/regional/summary")

def get_hospital_trends(provider_id: str):
    return _get(f"/trends/{provider_id}")

def query_nlq(question: str):
    return _post("/nlq/query", {"question": question})
