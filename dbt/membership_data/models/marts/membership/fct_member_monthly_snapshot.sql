with months as (
    select distinct
        date_trunc('month', date_day)::date as snapshot_month
    from {{ ref('metricflow_time_spine') }}
),

month_ends as (
    select
        snapshot_month,
        (snapshot_month + interval '1 month' - interval '1 day')::date as snapshot_date
    from months
),

members as (
    select member_id, approved_at from {{ ref('dim_member') }}
),

status_history as (
    select * from {{ ref('fct_member_status_history') }}
),

bounds as (
    select max(status_start_at)::date as max_known_date
    from status_history
),

member_months as (
    select
        members.member_id,
        month_ends.snapshot_month,
        month_ends.snapshot_date
    from members
    cross join month_ends
    cross join bounds
    where month_ends.snapshot_date >= members.approved_at::date
      and month_ends.snapshot_date <= bounds.max_known_date
),

final as (
    select
        member_months.snapshot_month::text || '-' || member_months.member_id::text as member_month_id,
        member_months.member_id,
        member_months.snapshot_month,
        member_months.snapshot_date,
        status_history.status,
        (member_months.snapshot_date - status_history.status_start_at::date) as days_in_current_status
    from member_months
    left join status_history
        on member_months.member_id = status_history.member_id
        and status_history.status_start_at::date <= member_months.snapshot_date
        and (
            status_history.status_end_at is null
            or status_history.status_end_at::date > member_months.snapshot_date
        )
)

select * from final
