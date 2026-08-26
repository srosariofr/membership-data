with payments as (
    select * from {{ ref('stg_payments') }}
),

final as (
    select
        payment_id,
        member_id,
        application_id,
        event_id,
        event_attendance_id,
        invoice_id,
        payment_type,
        payment_status,
        payment_method,
        billing_period,
        currency,
        amount,
        due_date,
        paid_at,
        (paid_at::date - due_date::date) as days_to_pay,
        paid_at > due_date as is_late
    from payments
)

select * from final
