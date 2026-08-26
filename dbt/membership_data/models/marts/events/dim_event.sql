with events as (
    select * from {{ ref('stg_events') }}
),

final as (
    select
        event_id,
        event_name,
        event_type,
        event_date,
        city,
        capacity
    from events
)

select * from final
