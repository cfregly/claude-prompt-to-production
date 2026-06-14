"""Lint an eval set: is it a moat, or a vibe?

    python eval_lint.py data/golden_set.jsonl [--min-score 80]
    python eval_lint.py --selftest

Evals are the retention moat. Demos win the trial; evals win the renewal. But an
eval set is only a moat if it tests the things that actually lose a customer:
the agent inventing a number, breaking its instructions under pressure, or
drifting on a prompt change nobody graded. This scores a golden set (JSONL of
`{id, q, must_contain_any}`, the format Act 3 grades) for moat quality, so you
can gate it in CI the same way you gate the answers. Stdlib only, no API.

Rules:
  EL001 (error) no honesty/refusal case. The set never checks that the agent
                says "I don't have that" instead of inventing one. Hallucinated
                confidence is what loses an enterprise account.
  EL002 (warn)  thin coverage (under 6 cases). A handful of evals is a vibe.
  EL003 (error) a case with no expected-answer spec. It grades nothing.
  EL004 (warn)  no adversarial case (injection, instruction-override). Untested
                robustness is the gap a red-teamer finds first.
  EL005 (info)  every case grades by substring. Add an LLM judge for the cases
                where valid phrasing varies (the honesty cases especially).

Severities: error (-15), warn (-8), info (-3). The set starts at 100, floor 0.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEDUCTION = {"error": 15, "warn": 8, "info": 3}

# A right answer that is a refusal or an admission of not knowing. This is the
# trust dimension: the only kind of case that catches a confident hallucination.
REFUSAL = re.compile(
    r"don'?t have|do not have|does not have|not available|no data|not provided|"
    r"doesn'?t include|does not include|unavailable|not in|\bcan'?t\b|\bcannot\b|"
    r"\bwon'?t\b|no information|not able|i don'?t know", re.I)

# A question that tries to make the agent break its instructions or leak data.
INJECTION = re.compile(
    r"ignore (?:your|all|previous|the) .{0,20}instruction|disregard (?:your|all|the)|"
    r"\bpretend\b|\bjailbreak\b|system prompt|reveal|exfiltrate|"
    r"confidential|competitor'?s? .{0,20}(roadmap|secret|plan)|act as|override your", re.I)


def _grader_spec(case: dict) -> list:
    """The expected-answer spec a case grades against, in either supported shape."""
    return case.get("must_contain_any") or case.get("expect") or []


def lint_eval_set(cases: list[dict]) -> dict:
    findings: list[dict] = []

    def add(rule, sev, msg, fix):
        findings.append({"rule": rule, "severity": sev, "message": msg, "fix": fix})

    n = len(cases)
    gradeable = [c for c in cases if _grader_spec(c)]

    # EL003 ungradeable cases
    ungradeable = [c.get("id", "<no id>") for c in cases if not _grader_spec(c)]
    if ungradeable:
        shown = ", ".join(ungradeable[:3]) + (" ..." if len(ungradeable) > 3 else "")
        add("EL003", "error",
            f"{len(ungradeable)} case(s) have no expected-answer spec ({shown})",
            "Give every case a must_contain_any (or a judge rubric). An "
            "ungradeable case is a comment, not a test.")

    # EL001 honesty coverage
    honesty = [c for c in gradeable if any(REFUSAL.search(s) for s in _grader_spec(c))]
    if not honesty:
        add("EL001", "error",
            "no honesty/refusal case: the set never checks the agent admits what "
            "it does not know",
            "Add a case whose right answer is 'I don't have that'. A confident "
            "hallucination is what loses an enterprise account, and only an "
            "honesty case catches it.")

    # EL004 adversarial coverage
    adversarial = [c for c in cases if INJECTION.search(c.get("q", ""))]
    if not adversarial:
        add("EL004", "warn",
            "no adversarial case (prompt injection, instruction-override, data "
            "exfiltration): robustness is untested",
            "Add a case that tries to make the agent break its instructions. "
            "Untested robustness is the gap a red-teamer finds first.")

    # EL002 thin coverage
    if n < 6:
        add("EL002", "warn",
            f"only {n} case(s): a handful of evals is a vibe, not a moat",
            "Cover the real use cases plus the honesty and adversarial edges. "
            "The eval set IS your customer's definition of good.")

    # EL005 single grading mode (only meaningful once there is a real set)
    if n >= 4 and gradeable and not any(c.get("judge") or c.get("rubric") for c in cases):
        add("EL005", "info",
            "every case grades by substring; phrasing variants slip through",
            "Add an LLM judge for the cases where valid wording varies (the "
            "honesty cases especially): a correct 'the FAQ does not include "
            "that' should not fail because it missed a literal token.")

    score = max(0, 100 - sum(DEDUCTION[f["severity"]] for f in findings))
    grade = ("A" if score >= 90 else "B" if score >= 80 else "C" if score >= 65
             else "D" if score >= 50 else "F")
    return {"cases": n, "score": score, "grade": grade,
            "honesty_cases": len(honesty), "adversarial_cases": len(adversarial),
            "findings": findings}


def _load(path: str) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


SEV = {"error": "✗", "warn": "!", "info": "·"}


def _selftest() -> int:
    # The bundled golden set is a real moat: honesty + injection + gradeable.
    here = Path(__file__).parent
    golden = lint_eval_set(_load(str(here / "data" / "golden_set.jsonl")))
    assert golden["honesty_cases"] >= 1, "golden set lost its honesty cases"
    assert golden["adversarial_cases"] >= 1, "golden set lost its injection case"
    assert golden["score"] >= 90, golden["score"]
    rules = {f["rule"] for f in golden["findings"]}
    assert "EL001" not in rules and "EL003" not in rules, rules
    # A thin, honesty-free set is a vibe: it must score poorly.
    thin = lint_eval_set([{"id": "a", "q": "What does it do?", "must_contain_any": ["x"]},
                          {"id": "b", "q": "How much?", "must_contain_any": ["$"]}])
    thin_rules = {f["rule"] for f in thin["findings"]}
    assert "EL001" in thin_rules and "EL002" in thin_rules and "EL004" in thin_rules, thin_rules
    assert thin["score"] < golden["score"]
    print("eval_lint selftest: ok")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="eval_lint", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("eval_set", nargs="?", help="golden-set JSONL")
    ap.add_argument("--min-score", type=int, default=80)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        return _selftest()
    if not args.eval_set:
        ap.error("an eval-set JSONL is required (or --selftest)")

    r = lint_eval_set(_load(args.eval_set))
    print(f"eval_lint - {args.eval_set}: {r['score']}/100 (grade {r['grade']})")
    print(f"  {r['cases']} cases | {r['honesty_cases']} honesty | "
          f"{r['adversarial_cases']} adversarial\n")
    for f in r["findings"]:
        print(f"[{f['rule']} {SEV[f['severity']]}] {f['message']}")
        print(f"    fix: {f['fix']}")
    if not r["findings"]:
        print("clean - this eval set is a moat, not a vibe")
    if r["score"] < args.min_score:
        print(f"\nFAIL: {r['score']} < --min-score {args.min_score}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
