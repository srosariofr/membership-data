{{ config(
    materialized='view'
) }}

select
    member_status_history_id,
    member_id,
    status,
    cast(status_start_at as timestamp) as status_start_at,
    cast(status_end_at as timestamp) as status_end_at,
    changed_by,
    change_reason
from {{source('raw', 'member_status_history')}}