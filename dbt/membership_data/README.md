# membership_data (dbt project)

See the [repo root README](../../README.md) for the full picture — data model, pipeline, and how to run everything end to end. This file covers just the dbt-specific commands.

```bash
dbt build           # run models + tests
dbt docs generate    # build the browsable docs site into target/
mf list metrics      # list semantic layer metrics (needs DBT_PROFILES_DIR set, see root README)
```

`dbt docs serve` hangs serving `catalog.json` on this dbt-core beta (`1.12.0b3`) - confirmed with a direct `curl`, indefinite timeout. Serve `target/` with a plain HTTP server instead:

```bash
cd target && python -m http.server 8181
# open http://localhost:8181 - Sources, Metrics, and Semantic Models all show up in the sidebar
```

## Layout

- `models/staging/` — one view per raw source, renamed/cast columns only.
- `models/marts/{core,membership,events,finance}/` — tables, organized by business domain. Semantic model definitions (`semantic_model:`, `entity:`, `dimension:`, `metrics:`) are colocated in each mart's `.yml`, alongside its `data_tests`.
