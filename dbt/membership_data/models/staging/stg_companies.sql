with source as (
    select * from {{source('raw', 'stg_companies')}}
),

renamed as (
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
    from source
)

select * from renamed