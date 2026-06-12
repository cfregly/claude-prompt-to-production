"""
ACT 2 — Give the model hands (minutes 2-6 of the live demo)
===========================================================
A minimal agent loop with two tools over a tiny "startup metrics store."

The deliberately-boring lesson that saves startups months:
  *** Tool descriptions are API contracts. ***
Most agent bugs in the wild are not model failures — they are vague tool
descriptions, undocumented edge cases, and silent failure modes. Write the
description like you'd write the docstring for a paid public API, including
what happens on bad input.

Run:  python 02_agent_with_tools.py "Given our burn and MRR trend, how many months of runway do we have?"
"""

import json
import sys
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

load_dotenv()
console = Console()

MODEL = "claude-sonnet-4-6"
DATA = json.loads((Path(__file__).parent / "data" / "metrics.json").read_text())

SYSTEM = (
    "You are a CFO co-pilot for a startup founder. Use the tools for every number; "
    "never estimate a stored metric from memory. If a metric or month doesn't exist, "
    "say so plainly. Keep final answers under 120 words. Write plain prose: no "
    "em-dashes, no buzzwords, no 'it's not X, it's Y' framing."
)

# --- Tool definitions: read these descriptions like contracts -----------------
TOOLS = [
    {
        "name": "get_metric",
        "description": (
            "Return a stored company metric as JSON. Supported names: 'mrr' (monthly recurring "
            "revenue in USD, keyed by 'YYYY-MM'), 'customers' (count, keyed by 'YYYY-MM'), "
            "'cash_on_hand' (USD, scalar), 'monthly_burn' (USD, scalar), 'churn_rate_monthly' "
            "(fraction, scalar). For time-series metrics, pass month='YYYY-MM' for one value or "
            "omit month for the full series. Returns {'error': ...} if the metric or month does "
            "not exist — report that honestly instead of guessing."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Metric name, e.g. 'mrr'."},
                "month": {"type": "string", "description": "Optional 'YYYY-MM' for time-series metrics."},
            },
            "required": ["name"],
        },
    },
    {
        "name": "calculate_runway",
        "description": (
            "Compute runway in months as cash_on_hand / monthly_burn using the latest stored "
            "values, returned as JSON with the inputs included for auditability. Use this "
            "instead of doing the division yourself so the math is exact and traceable."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]

def run_tool(name: str, args: dict) -> dict:
    if name == "get_metric":
        metric = DATA.get(args.get("name", ""))
        if metric is None:
            return {"error": f"unknown metric '{args.get('name')}'", "available": [k for k in DATA if not k.startswith('_') and k not in ('company','currency')]}
        month = args.get("month")
        if month is None:
            return {args["name"]: metric}
        if isinstance(metric, dict):
            if month in metric:
                return {args["name"]: {month: metric[month]}}
            return {"error": f"no data for {month}", "available_months": sorted(metric)}
        # Error-only: don't hand the model the value alongside the contract violation.
        return {"error": f"'{args['name']}' is a scalar metric; omit 'month' and call again"}
    if name == "calculate_runway":
        cash, burn = DATA["cash_on_hand"], DATA["monthly_burn"]
        return {"cash_on_hand": cash, "monthly_burn": burn, "runway_months": round(cash / burn, 1)}
    return {"error": f"unknown tool '{name}'"}

def main() -> None:
    question = " ".join(sys.argv[1:]) or (
        "Given our current burn and the MRR trend over the last few months, how many months "
        "of runway do we have, and what would you tell our investors in two sentences?"
    )
    client = Anthropic()
    messages = [{"role": "user", "content": question}]
    console.print(Panel(question, title="founder asks", border_style="cyan"))

    for _turn in range(6):  # hard stop so a demo can never loop forever
        response = client.messages.create(
            model=MODEL, max_tokens=1024, system=SYSTEM, tools=TOOLS, messages=messages
        )
        if response.stop_reason != "tool_use":
            final = "".join(b.text for b in response.content if b.type == "text")
            console.print(Panel(final, title="agent answers", border_style="green"))
            u = response.usage
            console.print(f"[dim]final turn usage: {u.input_tokens} in / {u.output_tokens} out[/dim]")
            return

        messages.append({"role": "assistant", "content": response.content})
        results = []
        for block in response.content:
            if block.type == "tool_use":
                out = run_tool(block.name, dict(block.input))
                console.print(f"[yellow]tool[/yellow] {block.name}({json.dumps(dict(block.input))}) -> {json.dumps(out)[:160]}")
                results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(out)}
                )
        messages.append({"role": "user", "content": results})

    console.print("[red]Stopped after 6 turns — check your tool contracts.[/red]")

if __name__ == "__main__":
    main()
