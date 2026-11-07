"""memcheck.py -- the one command sinterview-tutor runs at the start of every invocation.

Answers, in a short banner: what engagement is open, what is due, what has actually been
learned, and -- most importantly -- whether the last session WROTE what it learned.

Everything it reports is computed from the memory files themselves, so it cannot flatter
the loop. A skill that grades its own memory from prose will always report that memory is
fine; this reads mtimes and counts rows instead.

    python scripts/memcheck.py            # session-start banner
    python scripts/memcheck.py --full     # + per-engagement detail, lesson titles
    python scripts/memcheck.py --strict   # exit 1 if a write gap or overdue item exists

Output is deliberately ASCII-only: this runs on a Windows console whose code page mangles
em-dashes and emoji.
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

TODAY = dt.date.today()

# soft caps: past these a file stops being read, which is the only real failure mode
CAPS = {
    "lessons.md": 400,
    "engagements.md": 600,
    "knowledge-tracker.md": 600,
    "story-bank.md": 900,
    "outcomes.md": 800,
    "forecasts.md": 900,
}

# Files that should show recent activity when an engagement was worked on.
# candidate-profile and lessons are the two the model most often skips.
LEARNING_FILES = ["candidate-profile.md", "lessons.md", "knowledge-tracker.md", "story-bank.md"]

ENG_HEAD = re.compile(r"^##\s+(E\d+)\s+.*?(\d{4}-\d\d-\d\d)\s+.*?--?\s*(.*)$")
ENG_HEAD_ALT = re.compile(r"^##\s+(E\d+)\s")
FIELD = re.compile(r"^\*\*([A-Za-z /]+?):?\*\*:?\s*(.*)$")
LESSON_HEAD = re.compile(
    r"^##\s+(\d{4}-\d\d-\d\d)\s+.*?\[(confirmed|provisional|retired)\]", re.I | re.M)
STORY_ROW = re.compile(r"^\|\s*([A-Za-z/ ()-]+?)\s*\|\s*(.*?)\s*\|\s*(EMPTY|FILLED|[A-Z0-9 ,-]*)\s*\|")
FORECAST_ROW = re.compile(
    r"^\|\s*(F\d+)\s*\|\s*(E\d+)\s*\|\s*(\d{4}-\d\d-\d\d)\s*\|\s*"
    r"(Very High|High|Medium|Low)\s*\|\s*(.*?)\s*\|\s*(ASKED|NOT_ASKED|UNGRADED)\s*\|",
    re.I | re.M)
ATTEMPT_HEAD = re.compile(
    r"^###\s+(.*?)\s+[-—]+\s+(\d{4}-\d\d-\d\d)\s+[-—]+\s+Level\s+(\d)", re.M)
DATE_ANY = re.compile(r"(\d{4}-\d\d-\d\d)")


def ascii_only(s):
    """Memory files are UTF-8 prose; this console is not. Fold rather than mangle."""
    return (s.replace("—", "--").replace("–", "-")
             .replace("‘", "'").replace("’", "'")
             .replace("“", '"').replace("”", '"')
             .replace("·", "|").replace("≥", ">=")
             .encode("ascii", "replace").decode("ascii"))


def path(name):
    return os.path.join(MEMORY, name)


def read(name, strip_fences=True):
    """File contents with fenced blocks removed -- schema templates live in fences and
    must never be counted as real entries."""
    p = path(name)
    if not os.path.exists(p):
        return None
    body = io.open(p, encoding="utf-8", errors="replace").read()
    if strip_fences:
        body = re.sub(r"^```.*?^```", "", body, flags=re.S | re.M)
    return body


def mtime(name):
    p = path(name)
    if not os.path.exists(p):
        return None
    return dt.datetime.fromtimestamp(os.path.getmtime(p))


def days(d):
    """Days from today to an ISO date string. Negative = in the past."""
    try:
        return (dt.date.fromisoformat(d) - TODAY).days
    except Exception:
        return None


def parse_engagements(body):
    out, cur = [], None
    for raw in (body or "").split("\n"):
        line = raw.strip()
        if ENG_HEAD_ALT.match(line):
            cur = {"id": line.split()[1], "title": line.lstrip("# ").strip(), "fields": {}}
            out.append(cur)
            continue
        if cur is None:
            continue
        f = FIELD.match(line)
        if f:
            cur["fields"][f.group(1).strip().lower()] = f.group(2).strip()
    return out


def count_open_questions(text):
    """FIELD captures only a field's FIRST line, so prefer an explicit count written
    there ("**9 open**") over inferring one from Q-ids that may sit on later lines."""
    m = re.search(r"(\d+)\s+open\b", text or "", re.I)
    if m:
        return int(m.group(1))
    m = re.search(r"Q1-Q(\d+)", text or "")
    if m:
        return int(m.group(1))
    return len(re.findall(r"\bQ\d+\b", text or "")) or None


def banner(full=False):
    problems = []
    lines = []
    add = lines.append

    add("=" * 68)
    add("SINTERVIEW-TUTOR  memcheck   %s" % TODAY.isoformat())
    add("=" * 68)

    # ---------- engagements ----------
    eng_body = read("engagements.md")
    if eng_body is None:
        add("engagements.md MISSING -- memory is not initialised.")
        problems.append("engagements.md missing")
        engagements = []
    else:
        engagements = parse_engagements(eng_body)

    active = [e for e in engagements
              if e["fields"].get("status", "").upper().startswith(("PREPPING", "READY"))]
    interviewed = [e for e in engagements
                   if "INTERVIEWED" in e["fields"].get("status", "").upper()]

    add("")
    add("ENGAGEMENTS  %d total | %d active | %d interviewed" %
        (len(engagements), len(active), len(interviewed)))
    for e in engagements:
        f = e["fields"]
        status = f.get("status", "?")[:60]
        nxt = f.get("next round", "")
        d = None
        m = DATE_ANY.search(nxt)
        if m:
            d = days(m.group(1))
        when = ("in %d d" % d) if d is not None and d >= 0 else (
            "%d d AGO" % abs(d) if d is not None else "date UNKNOWN")
        add("  %-5s %-46s" % (e["id"], e["title"][:46]))
        add("        status : %s" % status)
        add("        next   : %s" % when)
        oq = count_open_questions(f.get("open questions", ""))
        if oq:
            add("        OPEN QUESTIONS: %d unanswered" % oq)
            problems.append("%s has %d open questions" % (e["id"], oq))
        if "NOT YET SCORED" in f.get("readiness", "").upper():
            add("        readiness: NOT YET SCORED (no answers observed)")
        if d is not None and 0 <= d <= 1:
            add("        >> INTERVIEW IMMINENT -- rapid review is due")
            problems.append("%s interview within 24h" % e["id"])

    # ---------- forecasts ----------
    fc_body = read("forecasts.md")
    add("")
    if fc_body is None:
        add("FORECASTS    forecasts.md MISSING -- predictions are not gradeable")
        problems.append("forecasts.md missing")
    else:
        rows = FORECAST_ROW.findall(fc_body)
        graded = [r for r in rows if r[5].upper() in ("ASKED", "NOT_ASKED")]
        ungraded = [r for r in rows if r[5].upper() == "UNGRADED"]
        add("FORECASTS    %d logged | %d graded | %d awaiting a DEBRIEF"
            % (len(rows), len(graded), len(ungraded)))
        if rows and not graded:
            add("             calibration IMPOSSIBLE until a real interview is debriefed")

    # ---------- knowledge tracker ----------
    kt = read("knowledge-tracker.md")
    add("")
    if kt is None:
        add("TRACKER      knowledge-tracker.md MISSING")
        problems.append("knowledge-tracker.md missing")
    else:
        attempts = ATTEMPT_HEAD.findall(kt)
        rows = [l for l in kt.split("\n")
                if l.startswith("|") and l.count("|") >= 8 and "---" not in l
                and not re.search(r"Competency\s*\|", l) and "|" in l and " - " not in l[:6]]
        real_rows = [l for l in rows if not re.match(r"^\|\s*-+\s*\|", l)]
        add("TRACKER      %d attempts logged | %d competency rows"
            % (len(attempts), max(0, len(real_rows) - 1)))
        if attempts:
            last = max(a[1] for a in attempts)
            add("             last tested %s (%d days ago)" % (last, -(days(last) or 0)))
        else:
            add("             NO ANSWERS EVER SCORED -- readiness cannot be computed")

    # ---------- story bank ----------
    sb = read("story-bank.md")
    add("")
    if sb is None:
        add("STORIES      story-bank.md MISSING")
        problems.append("story-bank.md missing")
    else:
        empty = len(re.findall(r"\|\s*EMPTY", sb))
        filled = len(re.findall(r"^##\s+S\d+", sb, re.M))
        add("STORIES      %d written | %d slots still EMPTY" % (filled, empty))
        if re.search(r"\*\*A failure\*\*.*EMPTY", sb) or re.search(r"A failure.*\|\s*EMPTY", sb):
            add("             >> FAILURE STORY EMPTY -- most-failed question at senior level")
            problems.append("failure story slot empty")

    # ---------- lessons ----------
    le = read("lessons.md")
    add("")
    if le is None:
        add("LESSONS      lessons.md MISSING")
        problems.append("lessons.md missing")
    else:
        ls = LESSON_HEAD.findall(le)
        conf = sum(1 for x in ls if x[1].lower() == "confirmed")
        prov = sum(1 for x in ls if x[1].lower() == "provisional")
        ret = sum(1 for x in ls if x[1].lower() == "retired")
        add("LESSONS      %d live | %d confirmed | %d provisional | %d retired"
            % (conf + prov, conf, prov, ret))
        if full:
            for d0, g in ls:
                add("             %s [%s]" % (d0, g))

    # ---------- outcomes ----------
    oc = read("outcomes.md")
    add("")
    if oc is None:
        add("OUTCOMES     outcomes.md MISSING")
        problems.append("outcomes.md missing")
    else:
        debriefs = re.findall(r"^##\s+D\d+", oc, re.M)
        add("OUTCOMES     %d debriefs recorded" % len(debriefs))
        for e in interviewed:
            if e["id"] not in oc:
                add("             >> %s is INTERVIEWED with no debrief -- run DEBRIEF" % e["id"])
                problems.append("%s interviewed, no debrief" % e["id"])

    # ---------- THE WRITE-GAP CHECK ----------
    # If an engagement was touched but the learning files were not, the session
    # probably learned something and did not write it. This is the check that
    # would have caught the E001 session.
    add("")
    add("WRITE GAP CHECK")
    eng_m = mtime("engagements.md")
    if eng_m is None:
        add("  cannot run -- engagements.md missing")
    else:
        stale = []
        for name in LEARNING_FILES:
            m = mtime(name)
            if m is None:
                stale.append((name, "MISSING"))
            elif m < eng_m - dt.timedelta(minutes=5):
                stale.append((name, "not written since %s" % m.strftime("%Y-%m-%d %H:%M")))
        if not stale:
            add("  OK -- learning files are current with the engagement ledger")
        else:
            add("  engagements.md last written %s" % eng_m.strftime("%Y-%m-%d %H:%M"))
            for name, why in stale:
                add("  UNWRITTEN? %-24s %s" % (name, why))
            add("  -> A session that worked an engagement almost always learns something")
            add("     about Sai, his answers, or how to coach him. If nothing was written")
            add("     to these files, say so explicitly rather than leaving it silent.")
            problems.append("%d learning file(s) not written since last engagement edit"
                            % len(stale))

    # ---------- caps ----------
    over = []
    for name, cap in CAPS.items():
        p = path(name)
        if os.path.exists(p):
            n = sum(1 for _ in io.open(p, encoding="utf-8", errors="replace"))
            if n > cap:
                over.append((name, n, cap))
    if over:
        add("")
        add("SIZE CAPS")
        for name, n, cap in over:
            add("  %-24s %d lines (cap %d) -- prune or archive" % (name, n, cap))
            problems.append("%s over cap" % name)

    add("")
    if problems:
        add("ACTION REQUIRED (%d):" % len(problems))
        for p0 in problems:
            add("  - %s" % p0)
    else:
        add("No action required.")
    add("=" * 68)
    return lines, problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    lines, problems = banner(full=a.full)
    print(ascii_only("\n".join(lines)))
    if a.strict and problems:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
