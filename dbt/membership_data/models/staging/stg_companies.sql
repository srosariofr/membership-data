{{ config(
    materialized='view'
)}}

select
    company_id,
    company_name,
    industry,
    city,
    country,
    phone_number,
    website,
    email,
    cast(created_at as timestamp) as created_at
from {{source('raw', 'companies')}}