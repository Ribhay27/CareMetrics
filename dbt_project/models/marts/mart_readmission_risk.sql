with scores as (
    select * from {{ ref('int_hospital_scores') }}
), risk as (
    select * from {{ ref('stg_readmissions') }}
)
select
    s.provider_id,
    s.hospital_name,
    s.city,
    s.state,
    s.hospital_type,
    s.hospital_ownership,
    s.readmission_risk_score,
    s.readmission_performance_score,
    r.readm_heart_failure,
    r.readm_pneumonia,
    r.readm_hip_knee,
    r.readm_copd,
    r.readm_stroke,
    r.readm_heart_attack,
    r.avg_readmission_score,
    r.hf_compared_to_national,
    r.pn_compared_to_national,
    r.copd_compared_to_national,
    r.ami_compared_to_national,
    rank() over (partition by s.state order by s.readmission_risk_score desc nulls last) as state_readmission_rank
from scores s
left join risk r using (provider_id)
