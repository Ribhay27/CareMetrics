with hospital_scores as (
    select * from {{ ref('int_hospital_scores') }}
), state_community as (
    select
        state,
        avg(diabetes_prevalence) as diabetes_prevalence,
        avg(obesity_prevalence) as obesity_prevalence,
        avg(smoking_prevalence) as smoking_prevalence,
        avg(poor_mental_health_days) as poor_mental_health_days,
        avg(no_health_insurance_rate) as no_health_insurance_rate,
        avg(physical_inactivity_rate) as physical_inactivity_rate,
        avg(community_health_burden_score) as community_health_burden_score
    from {{ ref('stg_community_health') }}
    group by state
), joined as (
    select
        h.*,
        c.diabetes_prevalence,
        c.obesity_prevalence,
        c.smoking_prevalence,
        c.poor_mental_health_days,
        c.no_health_insurance_rate,
        c.physical_inactivity_rate,
        c.community_health_burden_score,
        ntile(3) over (order by c.community_health_burden_score) as burden_tertile
    from hospital_scores h
    left join state_community c using (state)
)
select
    *,
    case burden_tertile
        when 3 then 'High Burden'
        when 2 then 'Moderate Burden'
        else 'Low Burden'
    end as risk_context_label
from joined
