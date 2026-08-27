# Progress log

Working notes to pick this project back up in a future session. For what the project *is*, see [README.md](README.md) — this file is about what's been done and what's left, not the architecture.

Last updated: 2026-08-27. Latest commit: `3a4ddfc` (not yet pushed — see [Immediate next step](#immediate-next-step)).

## Immediate next step

`3a4ddfc apply BICentric brand theme to the dashboard` is committed locally but **not pushed**. Run:
```bash
git push origin master
```

## What's done, in order

1. **Staging layer fixed and documented** — 7 of 8 `stg_*.sql` models had `source()` calls pointing at the wrong names (a leftover from an earlier rename). Fixed, and added `data_tests`/`description` to every staging model (none but one had any before).
2. **`dim_member` cleaned up** — dropped `current_status`/`current_status_start_at` columns from `stg_members`: they were unreliable (the generator hardcodes `current_status = "Active"` at creation time and never updates it — the real status only lives in `member_status_history`). `dim_member` already derived the correct status via a join, so nothing downstream broke. Also removed a no-op `config()` block and added tests/docs.
3. **Payment due dates fixed** — `fct_payments.is_late` was tautologically always `true` (due_date was always constructed to fall before paid_at). Changed the generator (`scripts/generate_data_sources.py`) so `due_date` is derived from `paid_at` with a ~75%-on-time/~25%-late split, for all three payment types. Regenerated `data/*.csv`.
4. **Marts reorganized by domain** — `models/mart/` (flat) → `models/marts/{core,membership,events,finance}/`. Added `fct_applications`, `fct_payments`, `fct_event_attendance`. Unified all mart SQL on one CTE style (entity-named CTEs → `final`), replacing a mix of staging's `source`/`renamed` pattern and ad-hoc styles.
5. **dbt Semantic Layer built** — this was the actual point of the project. Uses dbt-core 1.12's new **colocated** spec (`semantic_model:`/`entity:`/`dimension:`/`metrics:` live inside each mart's own `.yml`, not a separate top-level file). Added a daily `metricflow_time_spine` (2021-01-01 to 2027-01-01).
6. **Two more history facts added** (the accumulating-snapshot + transaction-fact pairing pattern, mirrored from members onto applications):
   - `fct_member_status_history`, `fct_member_monthly_snapshot` (periodic snapshot, member × month, unlocks clean "active members over time" queries)
   - `fct_application_status_history`
7. **`dbt-metricflow` installed** — gives the `mf` query CLI locally (previously only had the `metricflow` engine library, no CLI). All semantic layer metrics validated by cross-checking `mf query` output against direct SQL — exact matches throughout.
8. **Metric descriptions filled in** — the 17 colocated `simple` metrics had no `description:` (only the 3 `ratio` metrics did); spotted via the dbt docs site and fixed.
9. **Project documented** — root `README.md` (was empty) and `dbt/membership_data/README.md` (was the `dbt init` boilerplate) now cover the full stack, data model, setup steps, mart layout, and semantic layer.
10. **Analytics dashboard built** (`dashboard/`) — Flask API (`dashboard/api.py`) + a single self-contained HTML page (`dashboard/static/index.html`, vanilla JS, hand-rolled SVG charts, no build step, no CDN except Google Fonts). Reads *exclusively* through the semantic layer.
    - First cut shelled out to the `mf` CLI per request — worked, but every request paid a ~15-25s cold start (importing dbt-core/metricflow fresh each time). Rewrote to load the `MetricFlowEngine` **once** at Flask startup using the same Python classes `mf` wraps internally (`dbt_metricflow.cli.cli_configuration.CLIConfiguration`, `metricflow.engine.metricflow_engine.MetricFlowQueryRequest`) — brought per-query time down to ~0.5-1s.
11. **BICentric brand theme applied to the dashboard** — colors and logo icon sourced from the user directly (the Google Drive connector couldn't reliably browse the `BICentric_Marca` folder — see [Known issues](#known-issues)). Palette: navy `#001f67`, green `#00823b`, lime `#9dd522` (primary, verified against the actual logo SVG), navy-deep `#061238`, green-soft `#75b148`, teal `#2b595b` (secondary), gray `#f4f4f4` (background). Font switched to **Inter** (Google Fonts). The actual logo's icon mark (3 diagonal bars) is embedded as inline SVG in the header using the real path data, not redrawn. Structure/layout/chart logic untouched — this pass was theme-only, deliberately.

## Current state

- **9 semantic models, 20 metrics** (17 simple + 3 ratio). Full list is in the README's [Semantic layer](README.md#semantic-layer) section.
- **10 mart models**: `dim_member`, `dim_company`, `dim_event`, `metricflow_time_spine` (core); `fct_applications`, `fct_application_status_history`, `fct_member_status_history`, `fct_member_monthly_snapshot` (membership); `fct_event_attendance` (events); `fct_payments` (finance).
- `dbt build`: 163/163 passing as of the last dbt-touching commit.
- Dashboard runs with `python dashboard/api.py` → `http://localhost:5001`. Needs `DBT_PROFILES_DIR` set (see README) and the local stack up (`docker compose up -d` + data loaded).
- Local dev stack (MinIO/Postgres/pgAdmin) and the dashboard's Flask server may or may not still be running depending on whether the machine was restarted since the last session — check with `docker ps` and `netstat -an | grep 5001` before assuming either is up.

## Known issues

- **Google Drive connector is unreliable in this environment.** `search_files` only reliably returns results for one specific query it seems to have cached (`title contains 'Bicentric' or title contains 'BICentric'`); any other query — different keywords, `parentId` filtering, pagination (`pageToken`), or `pageSize` — fails with "Operation is not implemented, or supported, or enabled." Could not browse the `BICentric_Marca` folder directly; the user ended up pasting the color palette and the logo SVG into the chat instead. If Drive access is needed again, expect this same failure mode and don't sink time into query-string guessing — ask the user to paste/upload instead.
- **`mf` CLI needs `DBT_PROFILES_DIR` set explicitly on Windows** (documented in README) — it doesn't resolve `~/.dbt` the way the `dbt` CLI does.
- **`mf`'s emoji crash was patched directly in `.venv/Lib/site-packages/dbt_metricflow/`** (stripped emoji/non-cp1252 characters from `main.py`, `tutorial.py`, `utils.py` — Windows' default console codepage can't encode them, causing a `TypeError` inside `halo`/`colorama`). This is **not part of the repo** (site-packages isn't tracked) and **will be lost if `dbt-metricflow` is reinstalled or upgraded**. The README documents the `PYTHONIOENCODING=utf-8 PYTHONUTF8=1` workaround as the fallback if that happens.
- The data generator's `random` module isn't seeded (only Faker is) — regenerating `data/*.csv` produces a different dataset each time. Documented in the README; not considered a bug worth fixing unless reproducibility becomes important.

## Backlog / ideas not yet started

Roughly in the order they came up in conversation, not necessarily priority order:

- **Saved queries** — name the dashboard's repeated query shapes as `saved_queries` in the semantic layer YAML instead of hardcoding metric/group-by lists in `dashboard/static/index.html`.
- **Derived/cumulative metrics** — everything so far is `simple` or `ratio`. Nothing uses MetricFlow's `derived` (e.g. month-over-month revenue growth using `offset_window`) or `cumulative` (running-total revenue) metric types yet. Churn rate (cancellations this month ÷ active members last month) would be a good first derived metric to try, since it needs a period-over-period comparison.
- **CI** — no GitHub Actions workflow exists. Would want `dbt build` + `mf validate-configs` running on every push.
- **`dbt docs serve` is broken on this dbt-core beta** (hangs serving `catalog.json` — confirmed with a direct `curl`, documented in the README with a `python -m http.server` workaround). Worth revisiting once dbt-core ships a stable (non-`b3`) 1.12 release, and possibly hosting the generated static docs site on GitHub Pages instead of requiring anyone to run it locally.
- **Dashboard**: only the theme changed in the last pass, deliberately ("quiero que nos enfoquemos primero en el tema" — the user's words). Structure/layout/charts are all still the original design from before the brand theme. Worth checking in on whether further visual refinement is wanted (the user may have more brand assets in `BICentric_Marca` — logo lockups, secondary marks, spacing rules — that weren't part of what got pasted into chat).
