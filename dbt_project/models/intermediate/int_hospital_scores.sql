with h as (select * from {{ ref('stg_hospitals') }}),
r as (select * from {{ ref('stg_readmissions') }}),
p as (select * from {{ ref('stg_patient_experience') }}),
t as (select * from {{ ref('stg_timely_care') }}),
joined as (
    select
        h.*,
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
        p.overall_patient_experience_score,
        p.nurse_communication_score,
        p.doctor_communication_score,
        p.recommendation_score,
        p.cleanliness_score,
        t.ed_throughput_score,
        t.door_to_ct_score,
        t.sepsis_care_score,
        t.avg_timely_care_score,
        2023 as year
    from h
    left join r using (provider_id)
    left join p using (provider_id)
    left join t using (provider_id)
), normalized as (
    select
        *,
        case
            when avg_readmission_score is null then null
            when max(avg_readmission_score) over () = min(avg_readmission_score) over () then 50
            else 100 - ((avg_readmission_score - min(avg_readmission_score) over ()) / nullif(max(avg_readmission_score) over () - min(avg_readmission_score) over (), 0) * 100)
        end as readmission_performance_score,
        case
            when avg_timely_care_score is null then null
            when avg_timely_care_score <= 5 then avg_timely_care_score * 20
            when avg_timely_care_score > 100 then 100 - least(100, avg_timely_care_score / nullif(max(avg_timely_care_score) over (), 0) * 100)
            else avg_timely_care_score
        end as timely_care_score_0_100
    from joined
), scored as (
    select
        *,
        (
            coalesce(overall_patient_experience_score, 50) * 0.35 +
            coalesce(timely_care_score_0_100, 50) * 0.30 +
            coalesce(readmission_performance_score, 50) * 0.35
        ) as composite_quality_score,
        (100 - coalesce(readmission_performance_score, 50)) as readmission_risk_score
    from normalized
)
select * from scored
