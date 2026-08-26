with source as (
    select * from {{ ref('stg_companies') }}
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
        created_at
    from source
)

select * from renamed
