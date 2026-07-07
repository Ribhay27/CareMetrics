with source as (
    select * from {{ source('raw', 'cdc_places_county') }}
), normalized as (
    select
        nullif(trim(county_fips::text), '') as county_fips,
        upper(trim(state::text)) as state,
        lower(coalesce(measure_id::text, measure::text, '')) as measure_key,
        case
            when lower(coalesce(data_value::text, '')) in ('not available','not applicable','n/a','','nan') then null
            else nullif(regexp_replace(data_value::text, '[^0-9\.-]', '', 'g'), '')::numeric
        end as value
    from source
    where nullif(trim(state::text), '') is not null
), county_pivot as (
    select
        county_fips,
        state,
        avg(value) filter (where measure_key in ('diabetes','diabetes_crudeprev','diabetes_adjprev') or measure_key like '%diabetes%') as diabetes_prevalence,
        avg(value) filter (where measure_key in ('obesity','obesity_crudeprev','obesity_adjprev') or measure_key like '%obesity%') as obesity_prevalence,
        avg(value) filter (where measure_key in ('csmoking','csmoking_crudeprev','csmoking_adjprev') or measure_key like '%smok%') as smoking_prevalence,
        avg(value) filter (where measure_key in ('mhlth','mhlth_crudeprev','mhlth_adjprev') or measure_key like '%mental%') as poor_mental_health_days,
        avg(value) filter (where measure_key in ('access2','access2_crudeprev','access2_adjprev') or measure_key like '%insurance%') as no_health_insurance_rate,
        avg(value) filter (where measure_key in ('lpa','lpa_crudeprev','lpa_adjprev') or measure_key like '%physical inactivity%') as physical_inactivity_rate
    from normalized
    group by county_fips, state
), scored as (
    select
        *,
        (
            coalesce(diabetes_prevalence, 0) * 0.30 +
            coalesce(obesity_prevalence, 0) * 0.25 +
            coalesce(smoking_prevalence, 0) * 0.20 +
            coalesce(poor_mental_health_days, 0) * 0.15 +
            coalesce(no_health_insurance_rate, 0) * 0.10
        ) as community_health_burden_score
    from county_pivot
)
select * from scored
