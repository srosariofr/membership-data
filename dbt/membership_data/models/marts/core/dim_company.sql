with companies as (
    select * from {{ ref('stg_companies') }}
),

final as (
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
    from companies
)

select * from final
