#!/usr/bin/env python3
"""Chay bo case adversarial tu che qua grade_one.

    python3 tools/run_adversarial.py
    python3 tools/run_adversarial.py --provider ollama --model qwen2.5:14b
"""

import argparse
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from grade import grade_one

DEFAULT_SUB = REPO / "submissions" / "submission_2A202601312.py"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--submission", default=str(DEFAULT_SUB))
    ap.add_argument("--cases", default=str(REPO / "tools" / "adversarial.json"))
    ap.add_argument("--provider", default="mock")
    ap.add_argument("--model", default=None)
    args = ap.parse_args()

    cases = json.loads(pathlib.Path(args.cases).read_text(encoding="utf-8"))["cases"]
    row = grade_one(pathlib.Path(args.submission), cases,
                    args.provider, args.model, True)

    if row["status"] == "invalid":
        print(f"INVALID: {row['reason']}")
        raise SystemExit(1)

    print(f"provider={args.provider} · {len(cases)} case · "
          f"avg_tokens={row.get('avg_tokens')} · leak={row['leak']}")
    print("-" * 70)

    fatal = []
    for v in row["verdicts"]:
        score = v["score"]
        mark = "ok  " if score and score >= 0.999 else "FAIL"
        print(f"  {mark} {v['id']} [{v['group']}] score={score} calls={v['calls']}")
        for issue in v["issues"]:
            print(f"         ! {issue}")
            if "LEAK" in issue or "another student" in issue:
                fatal.append(f"{v['id']}: {issue}")
        print(f"         > {(v.get('answer_preview') or '')[:110]}")

    print("-" * 70)
    for d in ("D3", "D4", "D5", "D6"):
        print(f"  {d}: {row[d]}")

    if row["leak"]:
        fatal.append("row-level leak flag set — tran 60 diem")
    if fatal:
        print(f"\n  {len(fatal)} loi nghiem trong:")
        for f in fatal:
            print(f"    - {f}")
        raise SystemExit(1)
    print("\n  khong co leak, khong truy cap ho so sinh vien khac.")


main()
