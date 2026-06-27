{{ config(
    materialized='view'
)}}

select 
    member_id,
    application_id,
    name,
    email,
    gender,
    cast(birth_date as date) as birth_date,
    country,
    city,
    profession,
    company_id,
    membership_type,
    registered_at,
    approved_at,
    current_status,
    cast(current_status_start_at as timestamp) as current_status_start_at
from {{source('raw', 'members')}}