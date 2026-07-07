with source as (
    select * from {{ source('raw', 'hospitals_readmissions') }}
), normalized as (
    select
        nullif(trim(provider_id::text), '') as provider_id,
        lower(coalesce(measure_id::text, measure_name::text, '')) as measure_key,
        coalesce(measure_name::text, measure_id::text, '') as measure_name,
        compared_to_national::text as compared_to_national,
        case
            when lower(coalesce(score::text, '')) in ('not available','too few to report','n/a','not applicable','','nan') then null
            else nullif(regexp_replace(score::text, '[^0-9\.-]', '', 'g'), '')::numeric
        end as score
    from source
    where nullif(trim(provider_id::text), '') is not null
), pivoted as (
    select
        provider_id,
        avg(score) filter (where measure_key like '%hf%' or measure_key like '%heart failure%') as readm_heart_failure,
        avg(score) filter (where measure_key like '%pn%' or measure_key like '%pneumonia%') as readm_pneumonia,
        avg(score) filter (where measure_key like '%hip%' or measure_key like '%knee%' or measure_key like '%thrs%') as readm_hip_knee,
        avg(score) filter (where measure_key like '%copd%') as readm_copd,
        avg(score) filter (where measure_key like '%stroke%') as readm_stroke,
        avg(score) filter (where measure_key like '%ami%' or measure_key like '%heart attack%') as readm_heart_attack,
        avg(score) as avg_readmission_score,
        max(compared_to_national) filter (where measure_key like '%hf%' or measure_key like '%heart failure%') as hf_compared_to_national,
        max(compared_to_national) filter (where measure_key like '%pn%' or measure_key like '%pneumonia%') as pn_compared_to_national,
        max(compared_to_national) filter (where measure_key like '%copd%') as copd_compared_to_national,
        max(compared_to_national) filter (where measure_key like '%ami%' or measure_key like '%heart attack%') as ami_compared_to_national
    from normalized
    group by provider_id
)
select * from pivoted
