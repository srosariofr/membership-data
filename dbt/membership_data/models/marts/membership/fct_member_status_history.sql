with member_status_history as (
    select * from {{ ref('stg_member_status_history') }}
),

final as (
    select
        member_status_history_id,
        member_id,
        status,
        status_start_at,
        status_end_at,
        changed_by,
        change_reason,
        (status_end_at::date - status_start_at::date) as duration_days,
        status_end_at is null as is_current
    from member_status_history
)

select * from final
