"""
ACT 3 — Evals before vibes (minutes 6-10 of the live demo)
==========================================================
A tiny eval harness over data/golden_set.jsonl. Two of the eight cases are
*honesty* cases: the right answer is "I don't have that," and shipping an
agent that can say so is a feature, not a failure.

Why founders should care: your eval set is the only artifact that encodes
YOUR customers' definition of "good." Demos get you a seed round; evals get
you renewals. Wire this into CI — the script exits non-zero below threshold.

Run:   python 03_evals.py            # code-graded (substring checks)
       python 03_evals.py --judge    # adds a Haiku LLM judge for nuance
"""

import argparse
import json
import re
import sys
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

load_dotenv()
console = Console()

ANSWER_MODEL = "claude-sonnet-4-6"
JUDGE_MODEL = "claude-haiku-4-5"   # judging is a high-volume, low-difficulty task: route it down
PASS_THRESHOLD = 0.75

ROOT = Path(__file__).parent
FAQ = (ROOT / "data" / "founder_faq.md").read_text()

# One cacheable system block: instructions + the FAQ corpus. Every eval case
# reuses it, so cached runs cost ~90% less on the shared prefix. Evals you can
# afford to run on every commit are evals that actually run.
SYSTEM = [
    {
        "type": "text",
        "text": (
            "Answer questions using ONLY the company FAQ below. If the answer is not in the "
            "FAQ, say you don't have that information. Never invent numbers. Write plain "
            "prose: no em-dashes, no buzzwords.\n\n" + FAQ
        ),
        "cache_control": {"type": "ephemeral"},
    }
]

def grade_code(answer: str, case: dict) -> bool:
    # Word-boundary match, not bare substring: a check for "no" must not pass on
    # "anonymized" or "north". Cheap graders earn trust by failing honestly.
    # Normalize typographic apostrophes so "don't" matches "don't".
    a = answer.lower().replace("’", "'")
    return any(re.search(r"\b" + re.escape(s.lower()) + r"\b", a) for s in case["must_contain_any"])

def grade_judge(client: Anthropic, case: dict, answer: str) -> bool:
    verdict = client.messages.create(
        model=JUDGE_MODEL,
        max_tokens=200,
        system=(
            'You grade QA answers. Reply with ONLY JSON: {"pass": true|false, "why": "<10 words>"}. '
            "Pass if the answer is faithful to the expected behavior; honesty cases pass only if "
            "the answer admits the information is unavailable."
        ),
        messages=[{
            "role": "user",
            "content": f"Question: {case['q']}\nExpected to contain one of: {case['must_contain_any']}\nAnswer: {answer}",
        }],
    )
    text = "".join(b.text for b in verdict.content if b.type == "text").strip()
    # Models sometimes wrap JSON in markdown fences despite "ONLY JSON" —
    # parse the object, not the prose around it.
    start, end = text.find("{"), text.rfind("}")
    try:
        return bool(json.loads(text[start : end + 1])["pass"])
    except (json.JSONDecodeError, KeyError, ValueError):
        return False  # an unparseable judge is a failing judge

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--judge", action="store_true", help="add LLM-judge grading on top of code grading")
    args = parser.parse_args()

    client = Anthropic()
    cases = [json.loads(line) for line in (ROOT / "data" / "golden_set.jsonl").read_text().splitlines() if line.strip()]

    table = Table(title="claude-prompt-to-production · eval run", show_lines=False)
    for col in ("case", "code grade", "judge" if args.judge else "", "answer (truncated)"):
        if col:
            table.add_column(col)

    passed = 0
    for case in cases:
        resp = client.messages.create(
            model=ANSWER_MODEL, max_tokens=300, system=SYSTEM,
            messages=[{"role": "user", "content": case["q"]}],
        )
        answer = "".join(b.text for b in resp.content if b.type == "text").strip()
        ok = grade_code(answer, case)
        row = [case["id"], "[green]PASS[/green]" if ok else "[red]FAIL[/red]"]
        if args.judge:
            jok = grade_judge(client, case, answer)
            ok = ok and jok
            row.append("[green]PASS[/green]" if jok else "[red]FAIL[/red]")
        row.append(answer.replace("\n", " ")[:80])
        table.add_row(*row)
        passed += ok

    score = passed / len(cases)
    console.print(table)
    console.print(f"\nscore: {passed}/{len(cases)} = {score:.0%}  (threshold {PASS_THRESHOLD:.0%})")
    if score < PASS_THRESHOLD:
        console.print("[red]Below threshold — failing the build. That's the point.[/red]")
        sys.exit(1)
    console.print("[green]Gate passed. Ship it.[/green]\nNext: python 04_cost_engineering.py\n")

if __name__ == "__main__":
    main()
