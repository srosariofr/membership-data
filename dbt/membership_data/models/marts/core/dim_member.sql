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
        current_status.status_start_at as current_status_start_at
    from members
    left join companies
        on members.company_id = companies.company_id
    left join current_status
        on members.member_id = current_status.member_id
)

select * from final
