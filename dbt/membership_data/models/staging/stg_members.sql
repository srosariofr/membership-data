with source as (
    select * from {{source('raw', 'members')}}
),

renamed as (
    select 
        member_id,
        application_id,
        company_id,
        name,
        email,
        gender,
        country,
        city,
        profession,
        membership_type,
        cast(birth_date as date) as birth_date,
        registered_at,
        approved_at
    from source
)

select * from renamed