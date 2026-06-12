"""
ENCORE — The same tools, made portable (MCP)
============================================
Act 2 wired tools into one script. This server exposes the SAME metrics store
over the Model Context Protocol, so Claude Code, Claude Desktop, or any MCP
client can use it — no app rewrite. Tools are the product; MCP is distribution.

Note the docstrings: FastMCP publishes them as the tool descriptions the model
reads. Write them like contracts — supported inputs, exact semantics, and what
happens on bad input. (Vague descriptions are the #1 agent bug in the wild.)

Try it with Claude Code:
    claude mcp add startup-metrics -- python mcp_server/startup_metrics_server.py
or add to claude_desktop_config.json (see README).
"""

import json
from pathlib import Path
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

DATA = json.loads((Path(__file__).resolve().parent.parent / "data" / "metrics.json").read_text())
SCALARS = ("cash_on_hand", "monthly_burn", "churn_rate_monthly")
SERIES = ("mrr", "customers")

mcp = FastMCP("startup-metrics")

@mcp.tool()
def list_metrics() -> str:
    """List every available metric with its type. Time-series metrics ('mrr',
    'customers') are keyed by 'YYYY-MM'; scalar metrics ('cash_on_hand',
    'monthly_burn', 'churn_rate_monthly') have a single current value. Returns
    JSON: {"time_series": [...], "scalars": [...]}. Takes no arguments and
    cannot fail. Call this first if you are unsure what exists — do not guess
    metric names."""
    return json.dumps({"time_series": list(SERIES), "scalars": list(SCALARS)})

@mcp.tool()
def get_metric(
    name: Annotated[str, Field(description=(
        "Metric to fetch: one of 'mrr', 'customers' (time-series) or "
        "'cash_on_hand', 'monthly_burn', 'churn_rate_monthly' (scalar). "
        "Unknown names return {\"error\": ...} with the valid list."
    ))],
    month: Annotated[str | None, Field(description=(
        "For time-series metrics only: one month as 'YYYY-MM' (e.g. '2026-03'). "
        "Omit for the full series, and always omit for scalar metrics."
    ))] = None,
) -> str:
    """Return a stored company metric as JSON. For time-series metrics, pass
    month='YYYY-MM' for one value or omit month for the full series; for scalar
    metrics, omit month. Returns {"error": ...} with the list of valid options
    if the metric or month does not exist — report that to the user honestly
    instead of inventing a value."""
    if name not in SCALARS + SERIES:
        return json.dumps({"error": f"unknown metric '{name}'", "valid": list(SCALARS + SERIES)})
    value = DATA[name]
    if name in SCALARS:
        if month:
            # Error-only: returning the value alongside the error would let the model
            # read past the contract violation and use it anyway.
            return json.dumps({"error": f"'{name}' is scalar; omit 'month' and call again"})
        return json.dumps({name: value})
    if month is None:
        return json.dumps({name: value})
    if month in value:
        return json.dumps({name: {month: value[month]}})
    return json.dumps({"error": f"no data for {month}", "available_months": sorted(value)})

@mcp.tool()
def calculate_runway() -> str:
    """Compute runway in months as cash_on_hand / monthly_burn from the latest
    stored values. Returns JSON including both inputs so the calculation is
    auditable, or {"error": ...} if monthly_burn is zero (runway is undefined).
    Prefer this over doing division on values you fetched separately."""
    cash, burn = DATA["cash_on_hand"], DATA["monthly_burn"]
    if not burn:
        return json.dumps({"error": "monthly_burn is zero; runway is undefined", "cash_on_hand": cash})
    return json.dumps({"cash_on_hand": cash, "monthly_burn": burn, "runway_months": round(cash / burn, 1)})

if __name__ == "__main__":
    mcp.run()
