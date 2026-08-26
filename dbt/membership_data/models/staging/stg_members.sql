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
        current_status,
        cast(birth_date as date) as birth_date,
        registered_at,
        approved_at,
        cast(current_status_start_at as timestamp) as current_status_start_at
    from source
)

select * from renamed