"""Thin JSON API in front of the dbt Semantic Layer.

Uses the MetricFlow Python API (the same one the `mf` CLI wraps)
directly, loading the engine once at process startup, instead of
shelling out to `mf` per request - importing dbt-core/metricflow and
parsing the semantic manifest costs ~15s, and `mf` pays that on every
single invocation since it's a fresh process each time. Loading it
once here means each query after startup only pays its own execution
time (roughly 1-3s). No SQL and no metric logic lives here - this
process is a transparent proxy, so every number the dashboard shows
is defined exactly once, in the semantic layer YAML.
"""

import datetime
import decimal
import os
import re
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

REPO_ROOT = Path(__file__).resolve().parent.parent
DBT_PROJECT_DIR = REPO_ROOT / "dbt" / "membership_data"
PROFILES_DIR = Path.home() / ".dbt"

os.environ.setdefault("DBT_PROFILES_DIR", str(PROFILES_DIR))
os.environ.setdefault("DBT_PROJECT_DIR", str(DBT_PROJECT_DIR))

from dbt_metricflow.cli.cli_configuration import CLIConfiguration  # noqa: E402
from metricflow.engine.metricflow_engine import MetricFlowQueryRequest  # noqa: E402

IDENTIFIER_RE = re.compile(r"^-?[A-Za-z0-9_]+$")

app = Flask(__name__, static_folder="static", static_url_path="")

print("Loading MetricFlow engine (parses the semantic manifest, connects to the warehouse)...")
_cfg = CLIConfiguration()
_cfg.setup(dbt_profiles_path=PROFILES_DIR, dbt_project_path=DBT_PROJECT_DIR, configure_file_logging=False)
_engine = _cfg.mf  # building this property triggers the one-time manifest parse + sql client setup
print("MetricFlow engine ready.")


def _parse_identifier_list(raw: str) -> list[str]:
    items = [item.strip() for item in raw.split(",") if item.strip()]
    for item in items:
        if not IDENTIFIER_RE.match(item):
            raise ValueError(f"invalid identifier: {item!r}")
    return items


def _parse_filters(raw: str) -> list[str]:
    """Turns 'dim1:value1|dim2:value2' into MetricFlow where_constraints strings.

    Dimension names are validated against IDENTIFIER_RE (same allowlist as
    metrics/group_by); values are only ever compared for equality inside a
    quoted SQL literal, so the sole injection surface is an embedded quote,
    which is escaped by doubling it.
    """
    constraints = []
    for pair in (p for p in raw.split("|") if p.strip()):
        if ":" not in pair:
            raise ValueError(f"invalid filter (expected dim:value): {pair!r}")
        dim, value = pair.split(":", 1)
        dim = dim.strip()
        if not IDENTIFIER_RE.match(dim):
            raise ValueError(f"invalid filter dimension: {dim!r}")
        escaped_value = value.replace("'", "''")
        constraints.append(f"{{{{ Dimension('{dim}') }}}} = '{escaped_value}'")
    return constraints


def _jsonable(value):
    if isinstance(value, decimal.Decimal):
        return float(value)
    if isinstance(value, (datetime.datetime, datetime.date)):
        return value.isoformat()
    return value


@app.get("/api/query")
def api_query():
    metrics_raw = request.args.get("metrics", "")
    group_by_raw = request.args.get("group_by", "")
    order_by_raw = request.args.get("order_by", "")
    limit = request.args.get("limit", "").strip()
    start_date_raw = request.args.get("start_date", "").strip()
    end_date_raw = request.args.get("end_date", "").strip()
    filters_raw = request.args.get("filters", "").strip()

    if not metrics_raw.strip():
        return jsonify({"error": "metrics query param is required"}), 400
    if limit and not limit.isdigit():
        return jsonify({"error": "limit must be a positive integer"}), 400

    try:
        metrics = _parse_identifier_list(metrics_raw)
        group_by = _parse_identifier_list(group_by_raw)
        order_by = _parse_identifier_list(order_by_raw)
        where_constraints = _parse_filters(filters_raw)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    try:
        time_constraint_start = (
            datetime.datetime.combine(datetime.date.fromisoformat(start_date_raw), datetime.time.min)
            if start_date_raw
            else None
        )
        time_constraint_end = (
            datetime.datetime.combine(datetime.date.fromisoformat(end_date_raw), datetime.time.max)
            if end_date_raw
            else None
        )
    except ValueError:
        return jsonify({"error": "start_date/end_date must be YYYY-MM-DD"}), 400

    mf_request = MetricFlowQueryRequest.create(
        metric_names=metrics,
        group_by_names=group_by or None,
        order_by_names=order_by or None,
        limit=int(limit) if limit else None,
        time_constraint_start=time_constraint_start,
        time_constraint_end=time_constraint_end,
        where_constraints=where_constraints or None,
    )

    try:
        result = _engine.query(mf_request=mf_request)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 502

    if result.result_df is None:
        return jsonify({"error": "query returned no data"}), 502

    df = result.result_df
    columns = list(df.column_names)
    rows = [{col: _jsonable(val) for col, val in zip(columns, row)} for row in df.rows]
    return jsonify({"rows": rows})


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    app.run(port=5001, debug=False, use_reloader=False)
