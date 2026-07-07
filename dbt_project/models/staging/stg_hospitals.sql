with source as (
    select * from {{ source('raw', 'hospitals_general') }}
), cleaned as (
    select
        nullif(trim(provider_id::text), '') as provider_id,
        trim(initcap(hospital_name::text)) as hospital_name,
        trim(address::text) as address,
        upper(trim(city::text)) as city,
        upper(trim(state::text)) as state,
        lpad(regexp_replace(coalesce(zip_code::text, ''), '[^0-9]', '', 'g'), 5, '0') as zip_code,
        initcap(trim(hospital_type::text)) as hospital_type,
        initcap(trim(hospital_ownership::text)) as hospital_ownership,
        case
            when lower(coalesce(overall_rating::text, '')) in ('not available', 'n/a', 'nan', '') then null
            else nullif(regexp_replace(overall_rating::text, '[^0-9]', '', 'g'), '')::integer
        end as overall_rating,
        case
            when lower(coalesce(hospital_type::text, '')) like '%critical access%' then 'Rural'
            when lower(coalesce(hospital_type::text, '')) like '%rural%' then 'Rural'
            else 'Urban'
        end as urban_rural
    from source
)
select *
from cleaned
where provider_id is not null
