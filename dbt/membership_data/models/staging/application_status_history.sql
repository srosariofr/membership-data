{{ config(
    materialized='view'
)}}

select
    application_status_history_id,
    application_id,
    status,
    cast(status_start_at as timestamp) as status_start_at,
    cast(status_end_at as timestamp) as status_end_at,
    changed_by
from {{source('raw', 'application_status_history')}}