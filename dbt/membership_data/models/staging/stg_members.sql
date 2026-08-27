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
        cast(registered_at as timestamp) as registered_at,
        cast(approved_at as timestamp) as approved_at
    from source
)

select * from renamed