with perf as (
    select * from {{ ref('mart_hospital_performance') }}
), ranked as (
    select
        *,
        row_number() over (partition by state order by composite_quality_score desc nulls last) as best_rank,
        row_number() over (partition by state order by readmission_risk_score desc nulls last) as risk_rank
    from perf
)
select
    state,
    count(*) as hospital_count,
    avg(composite_quality_score) as avg_quality_score,
    avg(readmission_risk_score) as avg_readmission_risk,
    avg(case when readmission_risk_label = 'High' then 1.0 else 0.0 end) * 100 as pct_high_risk,
    avg(case when readmission_risk_label = 'Low' then 1.0 else 0.0 end) * 100 as pct_low_risk,
    avg(community_health_burden_score) as avg_community_burden,
    max(case when best_rank = 1 then hospital_name end) as top_performing_hospital,
    max(case when risk_rank = 1 then hospital_name end) as most_at_risk_hospital
from ranked
group by state
