from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

COLORWAY = ["#38bdf8", "#a78bfa", "#34d399", "#fbbf24", "#fb7185", "#22d3ee", "#c084fc"]
RISK_COLORS = {"High": "#fb7185", "Medium": "#fbbf24", "Low": "#34d399"}


def polish(fig, title: str | None = None, height: int = 430):
    fig.update_layout(
        template="plotly_dark",
        title={"text": title or fig.layout.title.text or "", "x": 0.02, "xanchor": "left"},
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.45)",
        font={"color": "#e5e7eb", "family": "Inter, ui-sans-serif, system-ui"},
        colorway=COLORWAY,
        margin={"l": 28, "r": 24, "t": 70, "b": 34},
        legend={"orientation": "h", "y": 1.08, "x": 0.02},
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(148,163,184,.16)", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(148,163,184,.16)", zeroline=False)
    return fig


def quality_score_histogram(df: pd.DataFrame):
    fig = px.histogram(
        df,
        x="composite_quality_score",
        nbins=34,
        title="Quality Score Distribution",
        color_discrete_sequence=["#38bdf8"],
        marginal="box",
    )
    fig.update_traces(marker_line_width=0, opacity=0.88, hovertemplate="Score bin=%{x}<br>Hospitals=%{y}<extra></extra>")
    return polish(fig)


def risk_distribution_bar(df: pd.DataFrame):
    order = ["Low", "Medium", "High"]
    counts = df["readmission_risk_label"].value_counts().reindex(order).dropna().reset_index()
    counts.columns = ["risk", "count"]
    fig = px.bar(
        counts,
        x="risk",
        y="count",
        color="risk",
        color_discrete_map=RISK_COLORS,
        title="Readmission Risk Distribution",
        text="count",
    )
    fig.update_traces(textposition="outside", marker_line_width=0, hovertemplate="Risk=%{x}<br>Hospitals=%{y}<extra></extra>")
    return polish(fig, height=390)


def state_choropleth(df: pd.DataFrame, color_column: str, title: str):
    fig = px.choropleth(
        df,
        locations="state",
        locationmode="USA-states",
        color=color_column,
        scope="usa",
        title=title,
        color_continuous_scale="Blues",
        hover_data=[c for c in ["hospital_count", "avg_quality_score", "avg_readmission_risk"] if c in df.columns],
    )
    fig.update_geos(bgcolor="rgba(0,0,0,0)", lakecolor="rgba(15,23,42,.4)")
    return polish(fig, height=520)


def shap_waterfall(shap_values, feature_names, hospital_name):
    values = np.array(shap_values, dtype=float)
    names = np.array(feature_names)
    order = np.argsort(np.abs(values))[::-1][:12]
    colors = ["#fb7185" if v > 0 else "#34d399" for v in values[order]]
    fig = go.Figure(go.Bar(x=values[order], y=names[order], orientation="h", marker_color=colors))
    fig.update_layout(yaxis={"autorange": "reversed"})
    return polish(fig, f"Top SHAP Drivers — {hospital_name}", height=470)


def trend_line(df: pd.DataFrame, y_column: str, title: str):
    fig = px.line(df, x="year", y=y_column, markers=True, title=title, color_discrete_sequence=["#38bdf8"])
    fig.update_traces(line_width=4, marker_size=10)
    return polish(fig)


def scatter_with_regression(df: pd.DataFrame, x_col: str, y_col: str, title: str):
    fig = px.scatter(
        df,
        x=x_col,
        y=y_col,
        trendline="ols",
        title=title,
        hover_data=[c for c in ["hospital_name", "city", "state", "readmission_risk_label"] if c in df.columns],
        color="readmission_risk_label" if "readmission_risk_label" in df.columns else None,
        color_discrete_map=RISK_COLORS,
        opacity=0.72,
    )
    return polish(fig, height=500)
