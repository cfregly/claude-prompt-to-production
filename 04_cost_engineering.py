"""
ACT 4 — Cost engineering (minutes 10-15 of the live demo)
=========================================================
Same workload, three ways:

  1. naive    — Sonnet answers everything, full context resent every call
  2. cached   — Sonnet + prompt caching on the shared context block
  3. routed   — Haiku for lookup questions, Sonnet for synthesis, both cached

Cost-per-token is a DESIGN DECISION, not a bill you discover later. Caching
and routing are each ~10 lines of code; together they routinely cut serving
cost 50-80% on context-heavy workloads. This script measures, it doesn't
assert — run it live and quote YOUR numbers.

Run:   python 04_cost_engineering.py            # dry run: renders SAMPLE data, no key needed
       python 04_cost_engineering.py --live     # real run: makes ~36 API calls, writes data/last_run.*
"""

import argparse
import json
import os
import statistics
import time
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

load_dotenv()
console = Console()

ROOT = Path(__file__).parent
PRICING = json.loads((ROOT / "pricing.json").read_text())
FAQ = (ROOT / "data" / "founder_faq.md").read_text()

SONNET = "claude-sonnet-4-6"
HAIKU = "claude-haiku-4-5"

SYSTEM_TEXT = (
    "Answer questions using ONLY the company FAQ below. Be concise. If the answer is not "
    "in the FAQ, say you don't have that information.\n\n" + FAQ
)

# 12 questions over the same shared context. 'hard' marks synthesis questions that
# earn Sonnet; the rest are lookups Haiku handles fine. In production you'd route
# with a Haiku classifier or a confidence score — a flag keeps the demo deterministic.
QUESTIONS = [
    {"q": "What does the Pilot plan include?", "hard": False},
    {"q": "What does the Growth plan cost per robot per month?", "hard": False},
    {"q": "Which regions are supported for data residency?", "hard": False},
    {"q": "What is the Enterprise uptime SLA?", "hard": False},
    {"q": "How fast is first response for Growth-plan support tickets?", "hard": False},
    {"q": "Is customer imagery used to train shared models?", "hard": False},
    {"q": "How long does Growth onboarding take?", "hard": False},
    {"q": "What ERP connectors are prebuilt?", "hard": False},
    {"q": "A 40-person plant with 6 lines wants SSO and a tight SLA. Compare Growth vs Enterprise and recommend one, with reasoning.", "hard": True},
    {"q": "Draft a 3-sentence answer to a security questionnaire asking about encryption, data residency, and deletion.", "hard": True},
    {"q": "A buyer worries about false-positive fatigue. Write a short, honest reassurance grounded in the FAQ.", "hard": True},
    {"q": "Summarize Foglight's pricing philosophy in two sentences for an investor memo.", "hard": True},
]

def cost_usd(model: str, usage: dict) -> float:
    p = PRICING["models"][model]
    c = PRICING["cache"]
    inp = p["input_per_mtok"]
    return (
        usage["input_tokens"] * inp
        + usage["cache_creation_input_tokens"] * inp * c["write_multiplier"]
        + usage["cache_read_input_tokens"] * inp * c["read_multiplier"]
        + usage["output_tokens"] * p["output_per_mtok"]
    ) / 1_000_000

def run_arm(client, name: str, cached: bool, routed: bool) -> dict:
    totals = {"input_tokens": 0, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0, "output_tokens": 0}
    latencies, per_model_cost, models_used = [], 0.0, set()

    if cached:
        system = [{"type": "text", "text": SYSTEM_TEXT, "cache_control": {"type": "ephemeral"}}]
    else:
        system = SYSTEM_TEXT

    for item in QUESTIONS:
        model = (SONNET if item["hard"] else HAIKU) if routed else SONNET
        models_used.add(model)
        t0 = time.perf_counter()
        resp = client.messages.create(
            model=model, max_tokens=400, system=system,
            messages=[{"role": "user", "content": item["q"]}],
        )
        latencies.append(time.perf_counter() - t0)
        u = resp.usage
        usage = {
            "input_tokens": u.input_tokens or 0,
            "cache_creation_input_tokens": getattr(u, "cache_creation_input_tokens", 0) or 0,
            "cache_read_input_tokens": getattr(u, "cache_read_input_tokens", 0) or 0,
            "output_tokens": u.output_tokens or 0,
        }
        for k in totals:
            totals[k] += usage[k]
        per_model_cost += cost_usd(model, usage)

    return {
        "name": name,
        "model": "mixed" if len(models_used) > 1 else models_used.pop(),
        "calls": len(QUESTIONS),
        **totals,
        "p50_latency_s": round(statistics.median(latencies), 2),
        "cost_usd": round(per_model_cost, 4),
    }

def render(arms: list[dict], sample: bool) -> None:
    if sample:
        console.print(Panel(
            "[bold red]SAMPLE DATA[/bold red] — illustrative numbers so the table renders without an "
            "API key. Run with [bold]--live[/bold] and quote your own measurements, never these.",
            border_style="red",
        ))
    baseline = arms[0]["cost_usd"]
    table = Table(title="claude-prompt-to-production · same workload, three ways")
    for col in ("strategy", "model", "calls", "fresh in", "cache write", "cache read", "out", "p50 lat", "cost", "vs naive"):
        table.add_column(col, justify="right" if col not in ("strategy", "model") else "left")
    md = ["| strategy | model | cost | p50 latency | vs naive |", "|---|---|---|---|---|"]
    for a in arms:
        delta = (a["cost_usd"] - baseline) / baseline
        table.add_row(
            a["name"], a["model"], str(a["calls"]), f'{a["input_tokens"]:,}',
            f'{a["cache_creation_input_tokens"]:,}', f'{a["cache_read_input_tokens"]:,}',
            f'{a["output_tokens"]:,}', f'{a["p50_latency_s"]}s', f'${a["cost_usd"]:.4f}',
            "baseline" if a is arms[0] else f"[green]{delta:+.0%}[/green]",
        )
        md.append(f'| {a["name"]} | {a["model"]} | ${a["cost_usd"]:.4f} | {a["p50_latency_s"]}s | '
                  + ("baseline" if a is arms[0] else f"{delta:+.0%}") + " |")
    console.print(table)
    for a in arms:
        # A "cached" arm with zero cache reads means the prefix never hit the cache
        # (e.g. shrunk below the model's minimum cacheable prefix) — the comparison
        # would silently measure nothing. Fail loudly instead.
        if "cached" in a["name"] and a["cache_read_input_tokens"] == 0 and not sample:
            console.print(f"[bold red]WARNING:[/bold red] arm '{a['name']}' recorded ZERO cache reads — "
                          "prompt caching never engaged. Check that the system prefix exceeds the model's "
                          "minimum cacheable length before quoting these numbers.")
    if not sample:
        (ROOT / "data" / "last_run.json").write_text(json.dumps({"generated": time.strftime("%Y-%m-%d %H:%M:%S"), "arms": arms}, indent=2))
        (ROOT / "data" / "last_run.md").write_text("\n".join(md) + "\n")
        console.print("\nWrote data/last_run.json and data/last_run.md — paste the markdown table into the README.")
    console.print(f"[dim]Pricing from pricing.json — {PRICING['_verify']}[/dim]\n")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="make real API calls (~36 requests)")
    args = parser.parse_args()

    if not args.live or not os.environ.get("ANTHROPIC_API_KEY"):
        if args.live:
            console.print("[red]--live requested but ANTHROPIC_API_KEY is not set; falling back to sample.[/red]")
        sample = json.loads((ROOT / "data" / "sample_run.json").read_text())
        render(sample["arms"], sample=True)
        return

    from anthropic import Anthropic  # imported here so the dry run needs no key at all
    client = Anthropic()
    console.print("Running 3 arms x 12 questions (~36 calls). The cached arms reuse a ~5K-token prefix — sized above every model's minimum cacheable prefix.\n")
    arms = [
        run_arm(client, "naive (Sonnet, no cache)", cached=False, routed=False),
        run_arm(client, "cached (Sonnet + prompt caching)", cached=True, routed=False),
        run_arm(client, "routed + cached (Haiku easy / Sonnet hard)", cached=True, routed=True),
    ]
    render(arms, sample=False)

if __name__ == "__main__":
    main()
