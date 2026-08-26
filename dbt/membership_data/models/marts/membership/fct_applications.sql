with applications as (
    select * from {{ ref('stg_membership_applications') }}
),

terminal_status as (
    select
        application_id,
        status as final_status,
        status_start_at as decided_at
    from {{ ref('stg_application_status_history') }}
    where status_end_at is null
      and status in ('Approved', 'Rejected', 'Withdrawn')
),

members as (
    select
        application_id,
        member_id
    from {{ ref('stg_members') }}
),

final as (
    select
        applications.application_id,
        applications.applicant_name,
        applications.email,
        applications.birth_date,
        applications.profession,
        applications.company_id,
        applications.country,
        applications.city,
        applications.application_type,
        applications.source_channel,
        applications.status,
        applications.submitted_at,
        terminal_status.decided_at,
        (terminal_status.decided_at::date - applications.submitted_at::date) as days_to_decision,
        applications.status = 'Approved' as is_approved,
        members.member_id
    from applications
    left join terminal_status
        on applications.application_id = terminal_status.application_id
    left join members
        on applications.application_id = members.application_id
)

select * from final
