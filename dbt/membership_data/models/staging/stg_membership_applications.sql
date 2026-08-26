with source as (
    select * from {{source('raw', 'membership_applications')}}
),

renamed as (
    select
        application_id,
        applicant_name,
        email,
        cast(birth_date as date) as birth_date,
        profession,
        company_id,
        country,
        city,
        application_type,
        status,
        cast(submitted_at as timestamp) as submitted_at,
        source_channel
    from source
)

select * from renamed