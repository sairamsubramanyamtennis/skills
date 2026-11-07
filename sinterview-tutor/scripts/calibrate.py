"""calibrate.py -- computes whether this skill's predictions and scores are any good.

Run by `/sinterview-tutor review`. Every number is computed from memory/forecasts.md and
memory/outcomes.md. Nothing here is asserted in prose, because a model doing arithmetic in
prose about its own accuracy will round in its own favour every time.

    python scripts/calibrate.py            # the scorecard
    python scripts/calibrate.py --verbose  # + every forecast row

It prints INSUFFICIENT DATA rather than a flattering number when n is too small. That is
the whole point: an interview coach with no debriefs has no evidence it works, and should
say so before quoting another readiness score.

Data it reads
-------------
memory/forecasts.md rows:
    | F001 | E001 | 2026-08-29 | Very High | <question> | UNGRADED |
    grade is ASKED / NOT_ASKED / UNGRADED

memory/outcomes.md, one machine-readable line per debrief:
    **CALIB:** engagement=E001 round=architecture readiness=78 coverage=62
               asked=18 unpredicted=4 taught_tested=6 taught_held=5 outcome=ADVANCED
    outcome is ADVANCED / REJECTED / OFFER / PENDING
"""
from __future__ import annotations

import argparse
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MEMORY = os.path.join(os.path.dirname(HERE), "memory")

MIN_N = 3  # below this, report the count and refuse to draw a conclusion

FORECAST_ROW = re.compile(
    r"^\|\s*(F\d+)\s*\|\s*(E\d+)\s*\|\s*(\d{4}-\d\d-\d\d)\s*\|\s*"
    r"(Very High|High|Medium|Low)\s*\|\s*(.*?)\s*\|\s*(ASKED|NOT_ASKED|UNGRADED)\s*\|",
    re.I | re.M)

CALIB = re.compile(r"\*\*CALIB:\*\*\s*(.+?)(?:\n\n|\n#|\Z)", re.S)
KV = re.compile(r"(\w+)=([A-Za-z0-9_.-]+)")

BANDS = [("90-100", 90, 101), ("80-89", 80, 90), ("70-79", 70, 80), ("below 70", 0, 70)]


def read(name):
    p = os.path.join(MEMORY, name)
    if not os.path.exists(p):
        return ""
    return io.open(p, encoding="utf-8", errors="replace").read()


def strip_fences(body):
    return re.sub(r"^```.*?^```", "", body, flags=re.S | re.M)


def pct(a, b):
    return "--" if not b else "%.0f%%" % (100.0 * a / b)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()

    out = []
    add = out.append

    forecasts = FORECAST_ROW.findall(strip_fences(read("forecasts.md")))
    calibs = []
    # fences hold the schema template, whose example CALIB line is not a real debrief
    for blob in CALIB.findall(strip_fences(read("outcomes.md"))):
        d = dict(KV.findall(blob))
        if d.get("engagement"):
            calibs.append(d)

    add("=" * 68)
    add("SINTERVIEW-TUTOR  calibration scorecard")
    add("=" * 68)
    add("forecast rows: %d      debriefs with CALIB lines: %d" % (len(forecasts), len(calibs)))
    add("")

    # ---------------- 1. PREDICTION PRECISION ----------------
    add("1. PREDICTION PRECISION -- of what we forecast, how much was asked?")
    graded = [f for f in forecasts if f[5].upper() in ("ASKED", "NOT_ASKED")]
    if not graded:
        add("   INSUFFICIENT DATA -- %d forecasts logged, 0 graded." % len(forecasts))
        add("   Nothing can be said about prediction quality until a real interview")
        add("   is debriefed and each row is marked ASKED / NOT_ASKED.")
    else:
        add("   %-12s %8s %8s %10s" % ("band", "graded", "asked", "precision"))
        for label in ("Very High", "High", "Medium", "Low"):
            rows = [f for f in graded if f[3].lower() == label.lower()]
            hit = [f for f in rows if f[5].upper() == "ASKED"]
            if rows:
                add("   %-12s %8d %8d %10s" % (label, len(rows), len(hit), pct(len(hit), len(rows))))
        top = [f for f in graded if f[3].lower() in ("very high", "high")]
        tophit = [f for f in top if f[5].upper() == "ASKED"]
        add("   HEADLINE  Very High + High precision: %s (n=%d)" % (pct(len(tophit), len(top)), len(top)))
        if len(top) < MIN_N:
            add("   (n < %d -- report the number, draw no conclusion)" % MIN_N)

    # ---------------- 2. PREDICTION RECALL ----------------
    add("")
    add("2. PREDICTION RECALL -- of what was asked, how much did we forecast?")
    if not calibs:
        add("   INSUFFICIENT DATA -- no debrief has recorded asked/unpredicted counts.")
    else:
        asked = sum(int(c.get("asked", 0)) for c in calibs)
        unpred = sum(int(c.get("unpredicted", 0)) for c in calibs)
        add("   questions asked: %d | never forecast: %d | recall: %s"
            % (asked, unpred, pct(asked - unpred, asked)))
        add("   Low recall = the competency map is too narrow. Low precision with high")
        add("   recall = the map is padded and the ranking is doing no work. They fail")
        add("   differently and both must be reported.")

    # ---------------- 3. READINESS CALIBRATION ----------------
    add("")
    add("3. READINESS CALIBRATION -- do high scores actually advance?")
    scored = [c for c in calibs if c.get("readiness", "").isdigit()
              and c.get("outcome", "PENDING").upper() != "PENDING"]
    if len(scored) < MIN_N:
        add("   INSUFFICIENT DATA -- %d resolved interviews with a readiness score." % len(scored))
        add("   Until this reaches n>=%d, a readiness score is an opinion, not a" % MIN_N)
        add("   calibrated estimate. SAY SO when quoting one.")
    else:
        add("   %-10s %8s %10s %10s" % ("band", "n", "advanced", "rate"))
        inverted = []
        for label, lo, hi in BANDS:
            rows = [c for c in scored if lo <= int(c["readiness"]) < hi]
            adv = [c for c in rows if c["outcome"].upper() in ("ADVANCED", "OFFER")]
            if rows:
                add("   %-10s %8d %10d %10s" % (label, len(rows), len(adv), pct(len(adv), len(rows))))
                inverted.append((label, len(adv) / float(len(rows))))
        if len(inverted) >= 2:
            rates = [r for _, r in inverted]
            if max(rates) - min(rates) < 0.15:
                add("   >> BANDS DO NOT SEPARATE. The readiness score is not")
                add("      discriminating. This finding OUTRANKS everything else in the")
                add("      review and must be stated before quoting another score.")

    # ---------------- 4. TEACHING EFFECTIVENESS ----------------
    add("")
    add("4. TEACHING EFFECTIVENESS -- of what we taught, how much held?")
    tt = sum(int(c.get("taught_tested", 0)) for c in calibs)
    th = sum(int(c.get("taught_held", 0)) for c in calibs)
    if not tt:
        add("   INSUFFICIENT DATA -- no debrief has recorded taught-then-tested topics.")
    else:
        add("   taught and tested for real: %d | held: %d | rate: %s" % (tt, th, pct(th, tt)))
        add("   A low rate is a TEACHING defect (level too low, or no cold retest).")
        add("   It is not the same as a prediction defect and has a different fix.")

    add("")
    if a.verbose and forecasts:
        add("FORECAST ROWS")
        for f in forecasts:
            add("   %-5s %-5s %-10s %-10s %-8s %s" % (f[0], f[1], f[2], f[3], f[5], f[4][:44]))
        add("")

    add("=" * 68)
    txt = "\n".join(out)
    try:
        print(txt)
    except UnicodeEncodeError:
        print(txt.encode("ascii", "replace").decode("ascii"))


if __name__ == "__main__":
    main()
