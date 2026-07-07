with source as (
    select * from {{ source('raw', 'hospitals_patient_experience') }}
), normalized as (
    select
        nullif(trim(provider_id::text), '') as provider_id,
        lower(coalesce(measure_id::text, measure_name::text, '')) as measure_key,
        case
            when lower(coalesce(score::text, '')) in ('not available','not applicable','n/a','','nan') then null
            else nullif(regexp_replace(score::text, '[^0-9\.-]', '', 'g'), '')::numeric
        end as score
    from source
    where nullif(trim(provider_id::text), '') is not null
), scaled as (
    select
        provider_id,
        measure_key,
        case when score <= 5 then score * 20 else score end as score_0_100
    from normalized
)
select
    provider_id,
    avg(score_0_100) as overall_patient_experience_score,
    avg(score_0_100) filter (where measure_key like '%nurse%') as nurse_communication_score,
    avg(score_0_100) filter (where measure_key like '%doctor%') as doctor_communication_score,
    avg(score_0_100) filter (where measure_key like '%recommend%') as recommendation_score,
    avg(score_0_100) filter (where measure_key like '%clean%') as cleanliness_score
from scaled
group by provider_id
