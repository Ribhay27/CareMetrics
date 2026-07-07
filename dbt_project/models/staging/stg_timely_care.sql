with source as (
    select * from {{ source('raw', 'hospitals_timely_care') }}
), normalized as (
    select
        nullif(trim(provider_id::text), '') as provider_id,
        lower(coalesce(measure_id::text, measure_name::text, '')) as measure_key,
        case
            when lower(coalesce(score::text, '')) in ('not available','not applicable','n/a','too few to report','','nan') then null
            else nullif(regexp_replace(score::text, '[^0-9\.-]', '', 'g'), '')::numeric
        end as score
    from source
    where nullif(trim(provider_id::text), '') is not null
), pivoted as (
    select
        provider_id,
        avg(score) filter (where measure_key like '%ed%' or measure_key like '%emergency%') as ed_throughput_score,
        avg(score) filter (where measure_key like '%ct%' or measure_key like '%stroke%') as door_to_ct_score,
        avg(score) filter (where measure_key like '%sepsis%' or measure_key like '%sep%') as sepsis_care_score,
        avg(score) as avg_timely_care_score
    from normalized
    group by provider_id
)
select * from pivoted
