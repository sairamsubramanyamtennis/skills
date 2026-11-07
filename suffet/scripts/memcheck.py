"""memcheck.py — the one command Suffet runs at the start of an invocation.

Answers, in under ten lines: what is due, what has been learned, and whether memory has
drifted out of the shape the skill expects. Everything it reports is computed from the
memory files themselves, so it cannot flatter the loop.

    python scripts/memcheck.py             # the session-start banner
    python scripts/memcheck.py --full      # + per-call detail and lesson titles
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
MEMORY = os.path.join(SKILL, "memory")

FILES = {                      # name -> soft cap in lines, past which the file is pruned
    "lessons.md": 400,
    "calls.md": 600,
    "journal.md": 800,
    "research-ledger.md": 400,
}

CALL_HEAD = re.compile(r"^##\s+(C\d+)\s+—\s+(\d{4}-\d\d-\d\d)\s+—\s+(.*)$")
FIELD = re.compile(r"^\*\*(Check by|Status|Conviction|View)\:?\*\*\:?\s*(.*)$", re.I)
LESSON_HEAD = re.compile(r"^##\s+(\d{4}-\d\d-\d\d)\s+—\s+(.*?)\s*\[(confirmed|provisional|retired)\]\s*$", re.I)


def read(name):
    """File contents with fenced blocks removed — the schema templates live in fences and
    must not be counted as real entries."""
    p = os.path.join(MEMORY, name)
    if not os.path.exists(p):
        return None
    body = io.open(p, encoding="utf-8", errors="replace").read()
    return re.sub(r"^```.*?^```", "", body, flags=re.S | re.M)


def parse_calls(body):
    calls, cur = [], None
    for line in body.split("\n"):
        m = CALL_HEAD.match(line.strip())
        if m:
            cur = {"id": m.group(1), "date": m.group(2), "subject": m.group(3),
                   "check": "", "status": "", "conviction": "", "view": ""}
            calls.append(cur)
            continue
        if cur is None:
            continue
        f = FIELD.match(line.strip())
        if f:
            cur[f.group(1).lower().replace(" ", "")[:5].rstrip(":")] = f.group(2).strip()
    # normalise the keys the regex abbreviated
    for c in calls:
        c["check"] = c.get("check") or c.get("checkb", "")
        c["status"] = c.get("statu") or c.get("status", "")
        c["conviction"] = c.get("convi") or c.get("conviction", "")
        c["view"] = c.get("view", "")
    return calls


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    args = ap.parse_args()
    today = dt.date.today().isoformat()

    print("SUFFET MEMORY — %s" % today)

    missing = [n for n in FILES if read(n) is None]
    if missing:
        print("  MISSING       %s  (create before logging to it)" % ", ".join(sorted(missing)))

    # ---------------------------------------------------------------- calls
    body = read("calls.md")
    due, open_n, resolved_n = [], 0, 0
    if body:
        calls = parse_calls(body)
        for c in calls:
            status = (c["status"] or "").upper()
            if "OPEN" in status:
                open_n += 1
                chk = (c["check"] or "")[:10]
                if re.match(r"\d{4}-\d\d-\d\d", chk) and chk <= today:
                    due.append(c)
            elif status:
                resolved_n += 1
        hit = [c for c in calls if "RIGHT" in (c["status"] or "").upper()]
        line = "  CALLS         %d open, %d resolved" % (open_n, resolved_n)
        if resolved_n:
            line += "  (%d right = %.0f%%)" % (len(hit), 100.0 * len(hit) / resolved_n)
        print(line)
        if due:
            print("  DUE NOW       %s" % ", ".join("%s (%s, by %s)" % (c["id"], c["subject"][:28], c["check"][:10]) for c in due))
            print("                resolve these against the ORIGINAL falsifier before taking a related new call")
        if args.full:
            for c in calls:
                if "OPEN" in (c["status"] or "").upper():
                    print("      %s  check %s  %s" % (c["id"], (c["check"] or "?")[:10], c["subject"][:60]))

    # -------------------------------------------------------------- lessons
    body = read("lessons.md")
    if body:
        grades = {}
        titles = []
        for line in body.split("\n"):
            m = LESSON_HEAD.match(line.strip())
            if m:
                g = m.group(3).lower()
                grades[g] = grades.get(g, 0) + 1
                titles.append((m.group(1), g, m.group(2)))
        print("  LESSONS       %d confirmed, %d provisional, %d retired" %
              (grades.get("confirmed", 0), grades.get("provisional", 0), grades.get("retired", 0)))
        if args.full:
            for d, g, t in titles:
                print("      %s [%s] %s" % (d, g[:4], t[:66]))

    # -------------------------------------------------------------- journal
    body = read("journal.md")
    if body is not None:
        n = len(re.findall(r"^##\s", body, re.M))
        last = re.findall(r"^##\s+(\d{4}-\d\d-\d\d)", body, re.M)
        print("  JOURNAL       %d exchanges, last %s" % (n, max(last) if last else "never"))

    # ----------------------------------------------------------------- size
    over = []
    for name, cap in FILES.items():
        b = read(name)
        if b is None:
            continue
        n = b.count("\n")
        if n > cap:
            over.append("%s %d/%d" % (name, n, cap))
    if over:
        print("  OVER CAP      %s  — prune before appending" % "; ".join(over))

    if not due and not over and not missing:
        print("  nothing due, nothing over cap")


if __name__ == "__main__":
    main()
