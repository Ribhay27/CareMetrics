import pandas as pd
import streamlit as st
import plotly.express as px
from dashboard.utils.db import run_query
from dashboard.utils.api_client import get_hospital_trends
from dashboard.utils.charts import trend_line


def run():
    st.header("7. Performance Trends")
    hospitals = run_query("select provider_id, hospital_name, state from marts.mart_hospital_performance order by hospital_name")
    if hospitals.empty: st.warning("No data"); return
    provider = st.selectbox("Hospital", hospitals.provider_id.astype(str), format_func=lambda x: hospitals.loc[hospitals.provider_id.astype(str)==x, 'hospital_name'].iloc[0])
    trends = pd.DataFrame(get_hospital_trends(provider))
    if not trends.empty:
        st.plotly_chart(trend_line(trends, "quality_score", "Quality Score Trend"), use_container_width=True)
        if "readmission_risk_score" in trends:
            st.plotly_chart(trend_line(trends, "readmission_risk_score", "Readmission Risk Trend"), use_container_width=True)
        trends["quality_delta"] = trends["quality_score"].diff()
        st.dataframe(trends, use_container_width=True, hide_index=True)
    improved = run_query("""
        with curr as (select provider_id, hospital_name, composite_quality_score from marts.mart_hospital_performance),
        old as (select provider_id, nullif(regexp_replace(overall_rating::text, '[^0-9]', '', 'g'),'')::numeric * 20 as old_quality from raw.hospitals_general_2021)
        select curr.hospital_name, curr.composite_quality_score - old.old_quality as improvement
        from curr join old using(provider_id) where old.old_quality is not null order by improvement desc nulls last limit 10
    """)
    declined = improved.sort_values("improvement").head(10) if not improved.empty else improved
    c1,c2 = st.columns(2)
    c1.subheader("Most Improved")
    c1.dataframe(improved, hide_index=True, use_container_width=True)
    c2.subheader("Most Declined")
    c2.dataframe(declined, hide_index=True, use_container_width=True)
