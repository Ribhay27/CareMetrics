from __future__ import annotations

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from common.config import db_url


@st.cache_resource
def get_connection():
    return create_engine(db_url(), pool_pre_ping=True)


@st.cache_data(ttl=300)
def run_query(sql: str, params: dict | None = None) -> pd.DataFrame:
    return pd.read_sql(text(sql), get_connection(), params=params or {})
