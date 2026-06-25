from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def quality_score_histogram(df: pd.DataFrame):
    return px.histogram(df, x="composite_quality_score", nbins=30, title="Quality Score Distribution")


def risk_distribution_bar(df: pd.DataFrame):
    counts = df["readmission_risk_label"].value_counts().reset_index()
    counts.columns = ["risk", "count"]
    return px.bar(counts, x="risk", y="count", title="Readmission Risk Distribution", text="count")


def state_choropleth(df: pd.DataFrame, color_column: str, title: str):
    return px.choropleth(df, locations="state", locationmode="USA-states", color=color_column, scope="usa", title=title)


def shap_waterfall(shap_values, feature_names, hospital_name):
    values = np.array(shap_values, dtype=float)
    order = np.argsort(np.abs(values))[::-1][:12]
    fig = go.Figure(go.Bar(x=values[order], y=np.array(feature_names)[order], orientation="h"))
    fig.update_layout(title=f"Top SHAP Drivers — {hospital_name}", yaxis={"autorange": "reversed"})
    return fig


def trend_line(df: pd.DataFrame, y_column: str, title: str):
    return px.line(df, x="year", y=y_column, markers=True, title=title)


def scatter_with_regression(df: pd.DataFrame, x_col: str, y_col: str, title: str):
    return px.scatter(df, x=x_col, y=y_col, trendline="ols", title=title, hover_data=["hospital_name", "state"])
