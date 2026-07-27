with source as (
    select * from {{source('raw', 'event_attendance')}}
),

renamed as (
    select
        event_attendance_id,
        event_id,
        member_id,
        attendance_status,
        cast(registered_at as timestamp) as registered_at,
        cast(attended_at as timestamp) as attended_at
    from source
)

select * from renamed
