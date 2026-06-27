{{ config(
    materialized='view'
) }}

select
    event_id,
    event_name,
    event_type,
    cast(event_date as date) as event_date,
    city,
    capacity
from {{source('raw', 'events')}}