with source as (
    select * from {{ ref('int_community_risk') }}
), ranked as (
    select
        *,
        percent_rank() over (order by readmission_risk_score) as readmission_pct_rank,
        percent_rank() over (order by composite_quality_score) as quality_pct_rank
    from source
)
select
    *,
    case
        when readmission_pct_rank >= 0.67 then 'High'
        when readmission_pct_rank <= 0.33 then 'Low'
        else 'Medium'
    end as readmission_risk_label,
    case
        when quality_pct_rank >= 0.90 then 'Top 10%'
        when quality_pct_rank >= 0.67 then 'Above Average'
        when quality_pct_rank <= 0.10 then 'Bottom 10%'
        when quality_pct_rank <= 0.33 then 'Below Average'
        else 'Average'
    end as quality_tier
from ranked
