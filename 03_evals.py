"""
ACT 3 — Evals before vibes, and proof every tier is safe (minutes 6-10)
=======================================================================
A tiny eval harness over data/golden_set.jsonl. Two of the eight cases are
*honesty* cases: the right answer is "I don't have that," and shipping an
agent that can say so is a feature, not a failure.

This act routes each case across the model ladder by consequence (junior Haiku
for lookups, senior Sonnet for the workhorse questions, principal Opus for
high-consequence honesty, distinguished Fable for the adversarial edge) and gates
each tier on its own. That order is the point. A router without an eval gate is
not a cost optimization, it is a quality regression you have not measured yet.
Aggregate quality can stay green while the cheap junior tier quietly tanks,
hidden behind the stronger tiers in the average. So every tier is proven here, in
Act 3, before Act 4 claims the 86 percent its two-tier cost routing saves. A tier
the key cannot reach (for example access-gated Fable) is reported as unavailable,
never faked. Every run writes a receipt to data/last_eval.md, the same way Act 4
writes data/last_run.md.

The code grader is a cheap substring check, and it has false negatives: a valid
"I don't have that" phrased a new way ("the FAQ does not include...") fails the
literal match. That is the lesson. With --judge, an LLM judge adjudicates when
the two disagree, recovering the valid answer the substring check missed, the
reason you layer a judge on top of cheap checks instead of trusting either alone.

Why founders should care: your eval set is the only artifact that encodes YOUR
customers' definition of "good." Demos get you a seed round, evals get you the
renewal. Wire this into CI. The script exits non-zero below threshold, on the
whole set or on any single tier.

Run:   python 03_evals.py            # code-graded, routed, gated per tier
       python 03_evals.py --judge    # adds a Haiku LLM judge for nuance
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

from anthropic import Anthropic, APIStatusError
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

load_dotenv()
console = Console()

HAIKU = "claude-haiku-4-5"
SONNET = "claude-sonnet-4-6"
OPUS = "claude-opus-4-8"
FABLE = "claude-fable-5"
JUDGE_MODEL = HAIKU   # judging is a high-volume, low-difficulty task: route it down
PASS_THRESHOLD = 0.75

# The routing ladder, by consequence: the cost of being wrong rises with the
# tier, so the more capable, more expensive model earns the higher-stakes work.
# The 'tier' is set per case in golden_set.jsonl to keep the eval deterministic.
# In production a classifier or a confidence score picks the tier, and you route
# DOWN only where it is cheap to be wrong.
TIER_MODEL = {"junior": HAIKU, "senior": SONNET, "principal": OPUS, "distinguished": FABLE}
MODEL_TIER = {m: t for t, m in TIER_MODEL.items()}
MODEL_NAME = {HAIKU: "Haiku", SONNET: "Sonnet", OPUS: "Opus", FABLE: "Fable"}
TIER_ORDER = list(TIER_MODEL)   # junior -> distinguished, the display and gate order

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


def route(case: dict) -> str:
    # Map a case to its model by tier. Unlabeled cases ride the cheap junior
    # model, the safe default for a low-stakes lookup.
    return TIER_MODEL.get(case.get("tier"), HAIKU)


def tier_rank(model: str) -> int:
    # Sort key so tiers print junior -> distinguished, not by model-id string.
    return TIER_ORDER.index(MODEL_TIER.get(model, "junior"))


def bucket_label(model: str) -> str:
    return f"{MODEL_NAME.get(model, model)} ({MODEL_TIER.get(model, 'unknown')})"


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
    # Models sometimes wrap JSON in markdown fences despite the ONLY JSON
    # instruction. Parse the object, not the prose around it.
    start, end = text.find("{"), text.rfind("}")
    try:
        return bool(json.loads(text[start : end + 1])["pass"])
    except (json.JSONDecodeError, KeyError, ValueError):
        return False  # an unparseable judge is a failing judge


def write_receipt(buckets: dict, unavailable: dict, passed: int, ran: int, graded_by: str) -> None:
    # Write the per-tier result the way 04 writes data/last_run.md: a committed
    # receipt, so each pass rate is a real number you can quote, not an assertion.
    # An access-gated tier is recorded as unavailable, not as a pass.
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    md = ["| tier | model | passed | total | pass rate | gate |",
          "|---|---|---|---|---|---|"]
    for model in sorted(set(buckets) | set(unavailable), key=tier_rank):
        if model in buckets:
            bp, bt = buckets[model]
            gate = "ok" if bp / bt >= PASS_THRESHOLD else "below bar"
            md.append(f"| {bucket_label(model)} | {model} | {bp} | {bt} | {bp / bt:.0%} | {gate} |")
        else:
            md.append(f"| {bucket_label(model)} | {model} | - | {unavailable[model]} | - | no access |")
    overall_gate = "ok" if ran and passed / ran >= PASS_THRESHOLD else "below bar"
    md.append(f"| overall (ran) | mixed | {passed} | {ran} | {(passed / ran if ran else 0):.0%} | {overall_gate} |")
    md.append("")
    suffix = f" {sum(unavailable.values())} case(s) skipped: tier not available with this key." if unavailable else ""
    md.append(f"Threshold {PASS_THRESHOLD:.0%}. Grading: {graded_by}. Generated {stamp}.{suffix}")
    (ROOT / "data" / "last_eval.md").write_text("\n".join(md) + "\n")
    tiers = {bucket_label(m): {"model": m, "passed": bp, "total": bt, "pass_rate": round(bp / bt, 4)}
             for m, (bp, bt) in buckets.items()}
    for m, n in unavailable.items():
        tiers[bucket_label(m)] = {"model": m, "available": False, "skipped": n}
    (ROOT / "data" / "last_eval.json").write_text(json.dumps({
        "generated": stamp,
        "threshold": PASS_THRESHOLD,
        "graded_by": graded_by,
        "tiers": tiers,
        "overall_ran": {"passed": passed, "total": ran, "pass_rate": round(passed / ran, 4) if ran else None},
    }, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--judge", action="store_true", help="add LLM-judge grading on top of code grading")
    args = parser.parse_args()

    client = Anthropic()
    cases = [json.loads(line) for line in (ROOT / "data" / "golden_set.jsonl").read_text().splitlines() if line.strip()]

    table = Table(title="claude-prompt-to-production · eval run (routed, gated per tier)", show_lines=False)
    for col in ("case", "tier", "code grade", "judge" if args.judge else "", "answer (truncated)"):
        if col:
            table.add_column(col)

    passed = 0
    recovered = 0   # code grader missed it; the judge caught the valid answer
    overruled = 0   # code grader passed it; the judge caught a false pass
    # Per tier: {model: [passed, ran]} for tiers that ran; {model: count} for
    # tiers the key cannot reach. Each tier is gated on its own, so a router
    # cannot trade quality for cost on a cheap tier under cover of the average.
    buckets = {}
    unavailable = {}
    for case in cases:
        model = route(case)
        label = bucket_label(model)
        try:
            resp = client.messages.create(
                model=model, max_tokens=300, system=SYSTEM,
                messages=[{"role": "user", "content": case["q"]}],
            )
        except APIStatusError as e:
            # A model the key cannot reach (a 403/404, e.g. access-gated Fable) is
            # an access gap, not a quality failure. Surface it, never fake a pass.
            if e.status_code in (403, 404):
                unavailable[model] = unavailable.get(model, 0) + 1
                na = "[yellow]N/A[/yellow]"
                cells = [case["id"], label, na] + ([na] if args.judge else []) + ["tier not available with this key"]
                table.add_row(*cells)
                continue
            raise
        answer = "".join(b.text for b in resp.content if b.type == "text").strip()
        ok_code = grade_code(answer, case)
        row = [case["id"], label, "[green]PASS[/green]" if ok_code else "[red]FAIL[/red]"]
        final = ok_code
        if args.judge:
            jok = grade_judge(client, case, answer)
            row.append("[green]PASS[/green]" if jok else "[red]FAIL[/red]")
            # The judge adjudicates: it is the authority when the two disagree, so
            # it can RECOVER a valid answer the substring grader missed -- not only
            # catch a false pass. That recovery is the whole reason to add a judge.
            final = jok
            recovered += int(jok and not ok_code)
            overruled += int(ok_code and not jok)
        row.append(answer.replace("\n", " ")[:80])
        table.add_row(*row)
        tally = buckets.setdefault(model, [0, 0])
        tally[1] += 1
        tally[0] += int(final)
        passed += int(final)

    ran = sum(bt for _, bt in buckets.values())
    score = passed / ran if ran else 0.0
    console.print(table)
    console.print(f"\noverall (ran): {passed}/{ran} = {score:.0%}  (threshold {PASS_THRESHOLD:.0%})")

    # Per tier, junior -> distinguished. Aggregate quality can stay green while a
    # cheap tier quietly fails, hidden behind the stronger tiers in the average.
    # Only a per-tier check catches a router that bought savings by degrading a
    # cheaper tier. An access-gated tier shows as unavailable, not as a failure.
    failed_buckets = []
    for model in sorted(set(buckets) | set(unavailable), key=tier_rank):
        if model in buckets:
            bp, bt = buckets[model]
            brate = bp / bt
            ok = brate >= PASS_THRESHOLD
            console.print(f"  {bucket_label(model)}: {bp}/{bt} = {brate:.0%}  "
                          + ("[green]ok[/green]" if ok else "[red]BELOW BAR[/red]"))
            if not ok:
                failed_buckets.append(bucket_label(model))
        else:
            console.print(f"  {bucket_label(model)}: {unavailable[model]} case(s) "
                          "[yellow]unavailable (no access on this key)[/yellow]")

    graded_by = "code + Haiku judge" if args.judge else "code (substring)"
    write_receipt(buckets, unavailable, passed, ran, graded_by)
    console.print("[dim]wrote data/last_eval.md and data/last_eval.json[/dim]")

    if args.judge and (recovered or overruled):
        console.print(
            f"[dim]judge adjudicated: recovered {recovered} valid answer(s) the "
            f"substring grader failed, overruled {overruled} false pass(es).[/dim]")
    if unavailable:
        miss = ", ".join(bucket_label(m) for m in sorted(unavailable, key=tier_rank))
        console.print(f"[yellow]note: the {miss} tier needs model access this key lacks, so it was "
                      "skipped, not graded. Grant access or remap the tier to validate it.[/yellow]")

    if failed_buckets:
        console.print(
            f"[red]Below threshold on the {', '.join(failed_buckets)} tier. A cheaper "
            "tier cannot trade quality for cost without this gate catching it, the "
            "regression a per-tier check sees and an aggregate gate hides. Failing the "
            "build.[/red]")
        sys.exit(1)
    if not ran or score < PASS_THRESHOLD:
        console.print("[red]Below threshold overall. Failing the build. That's the point.[/red]")
        sys.exit(1)
    console.print("[green]Every available tier cleared the bar. Ship it.[/green]\n"
                  "Next: python 04_cost_engineering.py\n")


if __name__ == "__main__":
    main()
