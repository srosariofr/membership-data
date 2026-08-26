{{ config(materialized='table') }}

with days as (
    {{ dbt.date_spine(
        'day',
        "to_date('2021-01-01', 'yyyy-mm-dd')",
        "to_date('2027-01-01', 'yyyy-mm-dd')"
    ) }}
),

final as (
    select cast(date_day as date) as date_day
    from days
)

select * from final
