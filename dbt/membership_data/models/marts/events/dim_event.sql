with source as (
    select * from {{ ref('stg_events') }}
),

renamed as (
    select
        event_id,
        event_name,
        event_type,
        event_date,
        city,
        capacity
    from source
)

select * from renamed
