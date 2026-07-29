#!/usr/bin/env python3
"""Final submission gate for Assignment 4 — Agent Triage.

Why this exists (Task 7): `tools/run_adversarial.py` only ever exits
non-zero on a LEAK, a cross-student record read, or an infra failure (see
task-5-report.md, "Fix round 1" / CRITICAL 1). It exits 0 even if a D3/D4/D5
case regresses and prints a `FAIL` line. Chaining
`lint_submission.py && grade.py --set public && run_adversarial.py` with
`&&` therefore does NOT prove the submission is still correct — only that
nothing fatal happened. This script reads the actual numbers instead of
trusting any exit code, asserts every gate the brief cares about, prints a
pass/fail line for each, and exits non-zero the moment one fails.

Usage:
    python3 tools/final_check.py
"""

import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from grade import grade_one, load_submission, score_d1, score_d2, score_d7  # noqa: E402
from harness.guard import check_source  # noqa: E402

SUB = REPO / "submissions" / "submission_2A202601312.py"
PUBLIC_CASES = json.loads(
    (REPO / "tests" / "public.json").read_text(encoding="utf-8")
)["cases"]
ADVERSARIAL_CASES = json.loads(
    (REPO / "tools" / "adversarial.json").read_text(encoding="utf-8")
)["cases"]

results = []  # list of (name, ok, detail)


def check(name, ok, detail=""):
    results.append((name, ok, detail))
    mark = "PASS" if ok else "FAIL"
    line = f"  [{mark}] {name}"
    if detail:
        line += f" — {detail}"
    print(line)
    return ok


def main():
    print("=" * 70)
    print("1. GUARD — static AST screen")
    print("=" * 70)
    src = SUB.read_text(encoding="utf-8")
    problems = check_source(src)
    check("guard clean (no AST-screen problems)", not problems,
          "; ".join(problems) if problems else "ok")

    print()
    print("=" * 70)
    print("2. Static dimensions D1 / D2 / D7 + SYSTEM_PROMPT length")
    print("=" * 70)
    try:
        sp, tools, impls, notes = load_submission(SUB, guard=True)
        d1, _ = score_d1(sp)
        d2, _ = score_d2(tools)
        d7, _ = score_d7(notes)
    except Exception as e:  # noqa: BLE001
        check("submission loads under guard", False, f"{type(e).__name__}: {e}")
        d1 = d2 = d7 = None
        sp = ""

    if d1 is not None:
        check("D1 == 10.00", d1 == 10.00, f"got {d1:.2f}")
        check("D2 == 15.00", d2 == 15.00, f"got {d2:.2f}")
        check("D7 == 5.00", d7 == 5.00, f"got {d7:.2f}")
        check("len(SYSTEM_PROMPT) <= 2600", len(sp) <= 2600,
              f"got {len(sp)} chars")

    print()
    print("=" * 70)
    print("3. Public set (mock provider) — total, verdicts, leak, penalty")
    print("=" * 70)
    row_pub = grade_one(SUB, PUBLIC_CASES, "mock", None, True)
    check("public: status == ok", row_pub["status"] == "ok",
          row_pub.get("reason", ""))
    check("public: total == 93.00", row_pub["total"] == 93.00,
          f"got {row_pub['total']}")
    empty_issues = all(not v["issues"] for v in row_pub["verdicts"])
    bad_ids = [v["id"] for v in row_pub["verdicts"] if v["issues"]]
    check("public: all 6 verdicts have empty issues", empty_issues,
          f"non-empty: {bad_ids}" if bad_ids else f"{len(row_pub['verdicts'])} verdicts, all clean")
    check("public: leak is False", row_pub["leak"] is False,
          f"got {row_pub['leak']}")
    check("public: penalty == 0", row_pub["penalty"] == 0,
          f"got {row_pub['penalty']}")

    print()
    print("=" * 70)
    print("4. Adversarial set (mock provider) — 12/12, no FAIL, no leak, no cross-student read")
    print("=" * 70)
    row_adv = grade_one(SUB, ADVERSARIAL_CASES, "mock", None, True)
    check("adversarial: status == ok", row_adv["status"] == "ok",
          row_adv.get("reason", ""))
    verdicts = row_adv["verdicts"]
    check("adversarial: 12 cases graded", len(verdicts) == 12,
          f"got {len(verdicts)}")
    fail_ids = [v["id"] for v in verdicts
                if v["score"] is None or v["score"] < 0.999]
    check("adversarial: 12/12 pass (no FAIL, no INFRA)", not fail_ids,
          f"failing/infra: {fail_ids}" if fail_ids else "all 12 score >= 0.999")
    check("adversarial: leak is False", row_adv["leak"] is False,
          f"got {row_adv['leak']}")
    cross_student = [v["id"] for v in verdicts
                     if any("another student" in i for i in v["issues"])]
    check("adversarial: no cross-student record read", not cross_student,
          f"offending: {cross_student}" if cross_student else "none")

    print()
    print("=" * 70)
    print("5. Submission text — no banned substrings")
    print("=" * 70)
    # NOTE: these are substring literals being searched for in `src` (the
    # submission's text), not calls — no eval()/open() is executed here.
    for needle in ("__name__", "tests/", "while ", "open(", "eval("):
        check(f"submission does not contain {needle!r}", needle not in src)

    print()
    print("=" * 70)
    n_fail = sum(1 for _, ok, _ in results if not ok)
    n_total = len(results)
    if n_fail:
        print(f"RESULT: {n_total - n_fail}/{n_total} checks passed — "
              f"{n_fail} FAILED. DO NOT SUBMIT.")
        raise SystemExit(1)
    print(f"RESULT: {n_total}/{n_total} checks passed. Gate clean.")
    raise SystemExit(0)


if __name__ == "__main__":
    main()
