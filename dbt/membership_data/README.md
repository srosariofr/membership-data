# membership_data (dbt project)

See the [repo root README](../../README.md) for the full picture — data model, pipeline, and how to run everything end to end. This file covers just the dbt-specific commands.

```bash
dbt build           # run models + tests
dbt docs generate && dbt docs serve   # browsable model/column docs
mf list metrics      # list semantic layer metrics (needs DBT_PROFILES_DIR set, see root README)
```

## Layout

- `models/staging/` — one view per raw source, renamed/cast columns only.
- `models/marts/{core,membership,events,finance}/` — tables, organized by business domain. Semantic model definitions (`semantic_model:`, `entity:`, `dimension:`, `metrics:`) are colocated in each mart's `.yml`, alongside its `data_tests`.
