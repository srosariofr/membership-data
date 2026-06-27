{{config(
    materialized='view'
)}}

select
    payment_id,
    member_id,
    application_id,
    event_id,
    event_attendance_id,
    invoice_id,
    payment_type,
    amount,
    currency,
    payment_status,
    payment_method,
    billing_period,
    cast(due_date as timestamp) as due_date,
    cast(paid_at as timestamp) as paid_at
from {{source('raw', 'payments')}}