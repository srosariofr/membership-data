# Membership Data

Fictional data engineering portfolio project: a professional association in the Dominican Republic, its 5+ years of membership history, and a full pipeline from raw data generation to a queryable semantic layer.

The data is synthetic but not random noise — it's generated with actual business logic behind it: an application funnel with rejections and withdrawals, an annual renewal cycle with grace periods and churn, event attendance, and payments tied to real member state. The goal of the project is to exercise a realistic stack end to end: **Python data generation → object storage → warehouse → dbt (staging + marts) → dbt Semantic Layer (MetricFlow)**.

## Stack

```
Faker/pandas  ──generate──▶  data/*.csv
                                  │
                            upload_to_minio.py
                                  ▼
                          MinIO (s3://membership-data/raw/*.csv)
                                  │
                          load_minio_to_postgres.py
                                  ▼
                          Postgres: raw schema
                                  │
                              dbt run
                                  ▼
                  staging (views)  ──▶  marts (tables, schema "mart")
                                              │
                                     dbt Semantic Layer
                                     (semantic models + metrics)
                                              │
                                        mf query / dbt build
```

- **Generation**: [scripts/generate_data_sources.py](scripts/generate_data_sources.py) — Faker (`es_ES` locale) + pandas, 8 CSVs with real referential and temporal logic between them (see [The data](#the-data) below).
- **Object storage**: MinIO (S3-compatible), landing zone for the raw CSVs.
- **Warehouse**: Postgres, loaded via pandas/SQLAlchemy into a `raw` schema.
- **Transformation**: dbt-core, `raw` → `staging` (views) → `mart` (tables), organized by business domain.
- **Semantic layer**: dbt's Semantic Layer (MetricFlow), colocated `semantic_model`/`entity`/`dimension`/`metrics` definitions on top of the mart models, queryable locally with the `mf` CLI.
- **Local infra**: `docker-compose.yaml` — MinIO, Postgres, pgAdmin.

## The data

8 raw entities, ~5 years of history (2021 to 2026), generated with real state-machine logic rather than independent random rows:

| Entity | Rows | What it captures |
|---|---|---|
| `companies` | 300 | Employers members/applicants can be affiliated with |
| `membership_applications` | 5,000 | One row per application, with its current status |
| `application_status_history` | 17,309 | Full path of each application through the funnel: `Submitted → Under Review → Pending Payment → Approved/Rejected/Withdrawn` |
| `members` | 3,317 | One row per **approved** application |
| `member_status_history` | 15,758 | Annual renewal cycle per member: `Active → Pending Renewal → (Active again, or → Inactive after 6mo unpaid → Cancelled after 1yr inactive)` |
| `events` | 100 | Conferences, workshops, networking, etc. |
| `event_attendance` | 15,303 | Registrations, with `Registered/Attended/No Show/Cancelled` outcomes |
| `payments` | 12,381 | Initial subscription, annual renewal, and event registration payments — only generated for members who were actually active at the relevant time, with due dates distributed ~75% on-time / ~25% late |

This history-with-a-state-machine design is what makes the dbt layer worth building: durations, funnel drop-off, churn, and month-over-month membership trends are all real, derivable signals — not decoration.

## Getting started

```bash
# 1. Start MinIO + Postgres + pgAdmin
docker compose up -d

# 2. Generate the fictional dataset (writes to data/*.csv)
python scripts/generate_data_sources.py

# 3. Land the CSVs in MinIO, then load them into Postgres's raw schema
python scripts/upload_to_minio.py
python scripts/load_minio_to_postgres.py

# 4. Build and test the dbt project
cd dbt/membership_data
dbt build
```

Requires a `~/.dbt/profiles.yml` with a `membership_data` profile pointing at the Postgres container (see `docker-compose.yaml` for credentials — `admin`/`password123`, db `membership_db`, port `5432`).

Dependencies are in [requirements.txt](requirements.txt) (Faker/pandas for generation, `dbt-core`/`dbt-postgres`/`dbt-metricflow` for the transformation and semantic layers).

## dbt project layout

```
dbt/membership_data/models/
├── staging/            one view per raw source, renamed/cast columns only
│   └── stg_*.sql
└── marts/               tables, organized by business domain
    ├── core/            dim_member, dim_company, metricflow_time_spine
    ├── membership/       fct_applications, fct_application_status_history,
    │                     fct_member_status_history, fct_member_monthly_snapshot
    ├── events/           dim_event, fct_event_attendance
    └── finance/          fct_payments
```

All `marts/*` subfolders land in the same physical Postgres schema (`mart`) — the folder split is for project organization, not warehouse fragmentation.

Each domain pairs an **accumulating-snapshot fact** (current outcome, 1 row per entity — `fct_applications`, `dim_member`) with a **transaction fact** of its status history (1 row per state transition — `fct_application_status_history`, `fct_member_status_history`), and members additionally get a **periodic snapshot fact** (`fct_member_monthly_snapshot`, 1 row per member × month) for clean time-series membership metrics without re-deriving point-in-time logic in every query.

## Semantic layer

9 semantic models (one per mart, using dbt-core 1.12's colocated spec — `semantic_model:`/`entity:`/`dimension:` live directly in each model's own `.yml` alongside its existing docs/tests) and 20 metrics:

| Metric | Type | Model |
|---|---|---|
| `members`, `companies`, `events_hosted` | simple count | dim_member, dim_company, dim_event |
| `applications_submitted`, `applications_approved`, `avg_days_to_decision` | simple | fct_applications |
| `application_status_periods`, `avg_application_status_duration_days` | simple | fct_application_status_history |
| `member_status_periods`, `avg_status_duration_days` | simple | fct_member_status_history |
| `member_month_snapshots`, `active_members` | simple | fct_member_monthly_snapshot |
| `revenue`, `payments_count`, `late_payments_count` | simple | fct_payments |
| `event_registrations`, `event_attendees` | simple | fct_event_attendance |
| `approval_rate` | ratio | applications_approved / applications_submitted |
| `late_payment_rate` | ratio | late_payments_count / payments_count |
| `event_attendance_rate` | ratio | event_attendees / event_registrations |

A daily `metricflow_time_spine` (2021-01-01 to 2027-01-01) backs all time-based queries.

Query it locally with `mf` (installed via `dbt-metricflow`):

```bash
mf list metrics
mf query --metrics revenue --group-by metric_time__month
mf query --metrics active_members --group-by metric_time__month
mf query --metrics approval_rate,late_payment_rate,event_attendance_rate
```

**On Windows**, `mf` needs `DBT_PROFILES_DIR` set explicitly (it doesn't resolve `~/.dbt` the way the `dbt` CLI does):

```bash
DBT_PROFILES_DIR="$HOME/.dbt" mf query --metrics revenue --group-by metric_time__month
```

## Dashboard

A small analytics dashboard ([dashboard/](dashboard/)) that reads exclusively through the semantic layer — no SQL is written for it. [dashboard/api.py](dashboard/api.py) is a Flask app that loads the MetricFlow Python engine once at startup (the same `MetricFlowEngine`/`CLIConfiguration` classes the `mf` CLI wraps) and exposes it as `GET /api/query?metrics=...&group_by=...&order_by=...`; [dashboard/static/index.html](dashboard/static/index.html) is a single self-contained page (vanilla JS, hand-rolled SVG charts, no build step, no CDN dependency) that calls that endpoint and renders KPIs plus revenue/membership/funnel charts.

```bash
python dashboard/api.py
# open http://localhost:5001
```

Loading the engine costs ~15s (importing dbt-core/metricflow and parsing the semantic manifest) — that happens once at process startup, printed to the console, not per request. Querying `mf` as a subprocess per request was the first approach and it worked, but every single call paid that ~15s cold-start again (confirmed with `time mf --version`: 14.8s doing nothing) since each invocation is a fresh process; loading the engine once in a long-running process instead brought each query down to ~0.5-1s.

## Known quirks

- `active_members` is defined **strictly** (`status = 'Active'`) — members in the `Pending Renewal` grace period are their own segment, not folded in. Filter for both explicitly if you want "members in good standing."
- The data generator's `random` module isn't seeded (only Faker is), so re-running `generate_data_sources.py` produces a slightly different dataset each time — row counts above are a snapshot, not guaranteed exact on regeneration.
- `mf`'s spinner output used emoji that crash on Windows' default `cp1252` console codepage. This repo doesn't patch third-party packages, so if you hit `UnicodeEncodeError`/`TypeError: cannot use a string pattern on a bytes-like object` running `mf`, set `PYTHONIOENCODING=utf-8` and `PYTHONUTF8=1` alongside `DBT_PROFILES_DIR`.
