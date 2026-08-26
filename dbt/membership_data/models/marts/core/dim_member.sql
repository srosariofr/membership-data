select
    member.member_id,
    member.application_id,
    member.name,
    member.email,
    member.gender,
    member.birth_date,
    member.country,
    member.city,
    member.profession,
    member.company_id,
    company.company_name,
    member.membership_type,
    member.registered_at,
    member.approved_at,
    status.status as current_status,
    status.status_start_at as current_status_start_at
from {{ ref('stg_members') }} as member
left join {{ ref('stg_companies') }} as company
    on member.company_id = company.company_id
left join {{ ref('stg_member_status_history') }} as status
    on member.member_id = status.member_id 
    and status.status_end_at is null