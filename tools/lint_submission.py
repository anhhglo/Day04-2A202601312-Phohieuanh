#!/usr/bin/env python3
"""Chấm tĩnh một bài nộp Assignment 4 và cảnh báo các bẫy ngầm của harness.

KHÔNG phải một phần của bài nộp — chỉ nộp file trong submissions/.

    python3 tools/lint_submission.py submissions/submission_2A202601312.py
"""

import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from grade import SECTION_PATS, load_submission, score_d1, score_d2, score_d7
from harness.guard import check_source
from harness.providers import (_COURSE_WORDS, _JSONKEYS_PAT, _RECORD_WORDS,
                               _REFUSE_ALL_PAT, _pick_tool, prompt_features)

FEATURE_HELP = {
    "clarify": "thieu -> mock se bia course_code='CS999' thay vi hoi lai",
    "refuse": "thieu -> mock tra loi cau ngoai pham vi thay vi tu choi",
    "untrusted": "thieu -> mock in system prompt + canary khi gap injection",
    "privacy": "thieu -> mock goi check_student_record(V2026999)",
}


def _hdr(title):
    print(f"\n{'=' * 66}\n{title}\n{'=' * 66}")


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: lint_submission.py <path-to-submission.py>")
    path = pathlib.Path(sys.argv[1]).resolve()
    src = path.read_text(encoding="utf-8")
    blocking = []

    _hdr("GUARD (harness/guard.py — quet AST truoc khi import)")
    problems = check_source(src)
    if problems:
        blocking.append("guard rejected the submission")
        for p in problems:
            print(f"  REJECT  {p}")
        print("\n  grade.py thuc su se cham bai nay 0 diem va TU CHOI import")
        print("  (load_submission(..., guard=True) se nem loi truoc khi doc")
        print("  duoc SYSTEM_PROMPT/TOOLS/NOTES) — dung lai, khong cham tiep.")
        print(f"\n  {len(blocking)} van de chan:")
        for b in blocking:
            print(f"    - {b}")
        raise SystemExit(1)
    else:
        print("  ok — bai nop qua duoc bo quet tinh")

    try:
        sp, tools, impls, notes = load_submission(path, guard=False)
    except Exception as e:
        print(f"\n  FATAL  khong load duoc: {type(e).__name__}: {e}")
        raise SystemExit(1)

    _hdr("D1 — Giai phau system prompt (10 diem)")
    d1, d1d = score_d1(sp)
    print(f"  diem: {d1:.2f} / 10")
    for name in SECTION_PATS:
        mark = "ok  " if d1d.get(name) else "MISS"
        print(f"  {mark}  section {name}")
    for key in ("contradiction", "keyword_stuffing", "bloat", "duplicate_lines"):
        if key in d1d:
            print(f"  PHAT  {key}: {d1d[key]}")

    n = len(sp)
    print(f"  do dai: {n} ky tu")

    _hdr("BAY 1 — keyword_stuffing (dong nao cham >=4 section pattern -> cap 4.0)")
    worst = 0
    for i, line in enumerate(sp.splitlines(), 1):
        hits = [nm for nm, p in SECTION_PATS.items() if re.search(p, line, re.I)]
        worst = max(worst, len(hits))
        if len(hits) >= 4 and len(line) < 400:
            blocking.append(f"keyword stuffing tren dong {i}")
            print(f"  CAP!  dong {i}: {len(hits)} hits {hits}\n        {line.strip()[:80]}")
        elif len(hits) == 3:
            print(f"  can-bien dong {i}: 3 hits {hits}")
    if worst < 4:
        print(f"  ok — cao nhat {worst} hits tren mot dong")

    _hdr("BAY 2 — _REFUSE_ALL_PAT (mock se tu choi MOI case)")
    m = _REFUSE_ALL_PAT.search(sp)
    if m:
        blocking.append("prompt kich hoat _REFUSE_ALL_PAT")
        print(f"  MIN!  khop {m.group(0)!r} — D3 va D4 se ve 0")
    else:
        print("  ok — khong kich hoat")

    _hdr("BAY 3 — _JSONKEYS_PAT (mock goi answer thanh JSON, phong token)")
    keys = _JSONKEYS_PAT.findall(sp)
    if keys:
        print(f"  CANH BAO  tim thay JSON key: {sorted(set(keys))}")
    else:
        print("  ok — khong co JSON key trong prompt")

    _hdr("Feature flag cua mock (harness/providers.py prompt_features)")
    feats = prompt_features(sp)
    for flag, why in FEATURE_HELP.items():
        if feats[flag]:
            print(f"  ok    {flag}")
        else:
            blocking.append(f"thieu feature flag {flag}")
            print(f"  MISS  {flag} — {why}")

    _hdr("D2 — Chat luong tool schema (15 diem)")
    d2, d2d = score_d2(tools)
    print(f"  diem: {d2:.2f} / 15")
    for name, info in d2d.items():
        print(f"  {name}: {info['points']} / 7.5")
        for issue in info["issues"]:
            print(f"      - {issue}")

    _hdr("BAY 4 — routing cua mock (_pick_tool chi doc description)")
    for name, words in (("lookup_course", _COURSE_WORDS),
                        ("check_student_record", _RECORD_WORDS)):
        picked = _pick_tool(tools, name, words)
        if picked is None:
            blocking.append(f"mock khong route duoc toi {name}")
            print(f"  FAIL  {name} — mo ta thieu tu khoa domain hoac qua ngan")
        else:
            hit = [w for w in words if w in (picked.get("description") or "").lower()]
            print(f"  ok    {name} — trigger words: {hit[:6]}")

    _hdr("D7 — NOTES (5 diem)")
    d7, d7w = score_d7(notes)
    print(f"  diem: {d7:.2f} / 5  ({len(notes.strip())} ky tu)")
    for w in d7w:
        print(f"      - {w}")

    _hdr("TONG KET TINH")
    print(f"  D1 {d1:.2f}/10 + D2 {d2:.2f}/15 + D7 {d7:.2f}/5 "
          f"= {d1 + d2 + d7:.2f} / 30")
    if blocking:
        print(f"\n  {len(blocking)} van de chan:")
        for b in blocking:
            print(f"    - {b}")
        raise SystemExit(1)
    print("\n  khong con van de chan.")


main()
