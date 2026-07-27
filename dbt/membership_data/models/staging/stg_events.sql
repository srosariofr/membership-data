with source as (
    select * from {{source('raw', 'stg_events')}}
),

renamed as (
    select
        event_id,
        event_name,
        event_type,
        city,
        capacity,
        cast(event_date as date) as event_date
    from source
)

select * from renamed