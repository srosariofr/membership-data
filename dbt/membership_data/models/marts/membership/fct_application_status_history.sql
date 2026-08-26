with application_status_history as (
    select * from {{ ref('stg_application_status_history') }}
),

final as (
    select
        application_status_history_id,
        application_id,
        status,
        status_start_at,
        status_end_at,
        changed_by,
        (status_end_at::date - status_start_at::date) as duration_days,
        status_end_at is null as is_current
    from application_status_history
)

select * from final
