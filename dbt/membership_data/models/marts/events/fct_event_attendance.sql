with event_attendance as (
    select * from {{ ref('stg_event_attendance') }}
),

final as (
    select
        event_attendance_id,
        event_id,
        member_id,
        attendance_status,
        registered_at,
        attended_at,
        attendance_status = 'Attended' as is_attended
    from event_attendance
)

select * from final
