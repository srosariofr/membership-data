with members as (
    select * from {{ ref('stg_members') }}
),

companies as (
    select * from {{ ref('stg_companies') }}
),

current_status as (
    select * from {{ ref('stg_member_status_history') }}
    where status_end_at is null
),

final as (
    select
        members.member_id,
        members.application_id,
        members.name,
        members.email,
        members.gender,
        members.birth_date,
        members.country,
        members.city,
        members.profession,
        members.company_id,
        companies.company_name,
        members.membership_type,
        members.registered_at,
        members.approved_at,
        current_status.status as current_status,
        current_status.status_start_at as current_status_start_at,
        case
            when members.birth_date is null then null
            when date_part('year', age(current_date, members.birth_date)) < 25 then 'Under 25'
            when date_part('year', age(current_date, members.birth_date)) < 35 then '25-34'
            when date_part('year', age(current_date, members.birth_date)) < 45 then '35-44'
            when date_part('year', age(current_date, members.birth_date)) < 55 then '45-54'
            when date_part('year', age(current_date, members.birth_date)) < 65 then '55-64'
            else '65+'
        end as age_range,
        case
            when members.approved_at is null then null
            when date_part('year', age(current_date, members.approved_at)) < 1 then 'Under 1 year'
            when date_part('year', age(current_date, members.approved_at)) < 3 then '1-3 years'
            when date_part('year', age(current_date, members.approved_at)) < 5 then '3-5 years'
            else '5+ years'
        end as tenure_range
    from members
    left join companies
        on members.company_id = companies.company_id
    left join current_status
        on members.member_id = current_status.member_id
)

select * from final
