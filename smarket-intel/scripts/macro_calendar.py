#!/usr/bin/env python3
"""
Market Intel — Macro event calendar, with realized market reactions

Answers "what actually happened this month, and what is coming" for the
scheduled macro events that move the tape: FOMC decisions and minutes, the
jobs report, CPI, PPI and PCE.

Usage:
    python macro_calendar.py --output cal.json
    python macro_calendar.py --back-days 60 --forward-days 30 --output cal.json
    python macro_calendar.py --as-of 2026-03-13 --output cal.json

Two halves, and the second is the reason this exists:

1. A STATIC SCHEDULE. These releases are published a year or more ahead, so
   the dates are data, not something to discover with a web search at runtime.
   Searching for them each run is slow, non-reproducible, and — the real
   problem — cannot be made point-in-time, because a search run today returns
   today's calendar no matter what --as-of says.

2. THE REALIZED REACTION, joined from mkt.price_daily. For every event already
   past, this reports what SPY/QQQ/IWM/TLT/GLD/XLU/XLF actually did on the day
   and the day after. That turns "the Fed met on July 29" into "the Fed met on
   July 29 and the rate-sensitivity spread moved N points", which is the form
   the briefing can actually reason from.

The `rate_path` block is the derived read worth having: did the market reprice
the rate path on this event, measured from prices rather than inferred from
the tone of press coverage. It uses TWO axes and reports when they disagree.

Why two and not one: the obvious single metric is XLF minus XLU — financials
want higher-for-longer, utilities are a bond proxy, so the gap should show a
hawkish repricing. It fails on exactly the event it most needs to catch. On
2026-07-29, when three FOMC members dissented FOR A HIKE and the 30Y hit its
highest since 2007, XLF fell 1.60% and XLU fell 1.34% — spread −0.26, which
reads as "nothing happened." Broad risk-off moved both legs together and
washed the signal out. The hawkish tell that day was TLT at −1.65%: duration
got sold. So duration leads, the sector spread confirms, and a conflict
between them is surfaced instead of being averaged into mush.

=== WHY THE DATES ARE HARDCODED AND NOT DERIVED ===

The obvious implementation is a rule: "jobs lands the first Friday, CPI the
second Wednesday." That rule is WRONG, and quietly so. The real 2026 jobs
schedule runs Feb 11, Mar 6, Apr 3, May 8, Jun 5, Jul 2, Aug 7 — Wednesdays,
Fridays and Thursdays, rarely the first Friday. PPI 2026 skips May entirely
and has two January releases. A derived calendar would place events on days
nothing happened and then invite the briefing to explain a move that never
occurred. So the tables below are transcribed from published schedules, each
carries a source tier, and coverage ENDS at a stated date rather than
extrapolating past what was verified.
"""

import argparse
import json
import sys
from datetime import date, datetime, timedelta

# --------------------------------------------------------------- the schedule
#
# tier: "high"   = official source, or two independent sources in exact
#                  agreement across every overlapping date
#       "medium" = single secondary source; believe the month, confirm the day
#       "derived"= computed from a rule, not transcribed. Stated as such.
#
# Verified 2026-08-07. Re-check each December when the agencies publish the
# following year; `coverage_end` below is what stops this going stale silently.

FOMC_DECISION_DAYS = {  # day 2 of each 2-day meeting; statement 14:00 ET
    "2026": ["2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17",
             "2026-07-29", "2026-09-16", "2026-10-28", "2026-12-09"],
    "2027": ["2027-01-27", "2027-03-17", "2027-04-28", "2027-06-09",
             "2027-07-28", "2027-09-15", "2027-10-27", "2027-12-08"],
}

# (release date, reference period)
CPI_2026 = [
    ("2026-01-13", "Dec 2025"), ("2026-02-13", "Jan 2026"),
    ("2026-03-11", "Feb 2026"), ("2026-04-10", "Mar 2026"),
    ("2026-05-12", "Apr 2026"), ("2026-06-10", "May 2026"),
    ("2026-07-14", "Jun 2026"), ("2026-08-12", "Jul 2026"),
    ("2026-09-11", "Aug 2026"), ("2026-10-14", "Sep 2026"),
    ("2026-11-10", "Oct 2026"), ("2026-12-10", "Nov 2026"),
]

JOBS_2026 = [
    ("2026-01-09", "Dec 2025"), ("2026-02-11", "Jan 2026"),
    ("2026-03-06", "Feb 2026"), ("2026-04-03", "Mar 2026"),
    ("2026-05-08", "Apr 2026"), ("2026-06-05", "May 2026"),
    ("2026-07-02", "Jun 2026"), ("2026-08-07", "Jul 2026"),
    ("2026-09-04", "Aug 2026"), ("2026-10-02", "Sep 2026"),
    ("2026-11-06", "Oct 2026"), ("2026-12-04", "Nov 2026"),
]

# Single-sourced, and visibly irregular (two January dates, no May release).
# The irregularity is in the source, not a transcription slip — but it is
# exactly why this is tier "medium" and the briefing is told to say so.
PPI_2026 = [
    ("2026-01-14", None), ("2026-01-30", None), ("2026-02-27", None),
    ("2026-03-18", None), ("2026-04-14", None), ("2026-06-11", None),
    ("2026-07-15", None), ("2026-08-13", "Jul 2026"),
    ("2026-09-10", "Aug 2026"), ("2026-10-15", "Sep 2026"),
    ("2026-11-13", "Oct 2026"), ("2026-12-15", "Nov 2026"),
]

# Forward-only: the source listed upcoming releases, so earlier 2026 PCE dates
# are absent rather than wrong. An absent event is reported as absent.
PCE_2026 = [
    ("2026-08-26", "Jul 2026"), ("2026-09-30", "Aug 2026"),
    ("2026-10-29", "Sep 2026"), ("2026-11-25", "Oct 2026"),
    ("2026-12-23", "Nov 2026"),
]

SERIES_COVERAGE = {          # last date this script will claim to know about
    "FOMC": "2027-12-08",
    "FOMC minutes": "2027-12-29",
    "Jobs report": "2026-12-04",
    "CPI": "2026-12-10",
    "PPI": "2026-12-15",
    "PCE": "2026-12-23",
}
COVERAGE_START = "2026-01-09"

# Instruments whose reaction gets measured. Chosen to span the axes an event
# can move: the tape, duration, the inflation hedge, and the two equity
# sectors that sit on opposite sides of the rate path.
REACTION_SYMBOLS = ["SPY", "QQQ", "IWM", "TLT", "GLD", "XLU", "XLF"]


def build_calendar():
    """Flatten the tables into one date-sorted event list."""
    events = []

    for year, days in FOMC_DECISION_DAYS.items():
        for d in days:
            events.append({
                "date": d, "event": "FOMC", "tier": "high",
                "label": "FOMC rate decision",
                "detail": "statement 14:00 ET, day 2 of a 2-day meeting; "
                          "press conference 14:30 ET",
                "covers": None, "importance": "high",
            })
            # Minutes land three weeks after the decision, by long-standing
            # Fed practice. That is a rule, not a transcription, so it is
            # tiered "derived" — it has been stable for years but nobody
            # published this specific date.
            md = datetime.strptime(d, "%Y-%m-%d").date() + timedelta(days=21)
            events.append({
                "date": md.isoformat(), "event": "FOMC minutes",
                "tier": "derived", "label": "FOMC minutes",
                "detail": "14:00 ET; derived as decision + 21 days, "
                          "confirm before relying on it",
                "covers": f"{d} meeting", "importance": "medium",
            })

    for d, covers in JOBS_2026:
        events.append({"date": d, "event": "Jobs report", "tier": "high",
                       "label": "Employment Situation (nonfarm payrolls)",
                       "detail": "08:30 ET, pre-open", "covers": covers,
                       "importance": "high"})
    for d, covers in CPI_2026:
        events.append({"date": d, "event": "CPI", "tier": "high",
                       "label": "Consumer Price Index",
                       "detail": "08:30 ET, pre-open", "covers": covers,
                       "importance": "high"})
    for d, covers in PPI_2026:
        events.append({"date": d, "event": "PPI", "tier": "medium",
                       "label": "Producer Price Index",
                       "detail": "08:30 ET, pre-open", "covers": covers,
                       "importance": "medium"})
    for d, covers in PCE_2026:
        events.append({"date": d, "event": "PCE", "tier": "medium",
                       "label": "Personal Income & Outlays (PCE deflator)",
                       "detail": "08:30 ET, pre-open; the Fed's preferred "
                                 "inflation gauge",
                       "covers": covers, "importance": "high"})

    events.sort(key=lambda e: e["date"])
    return events


# ------------------------------------------------------------------ reactions
def load_prices(symbols, start, end):
    """{symbol: {date: close}} from Postgres, resolved by security_id.

    Identity is resolved per symbol as of `end`, never joined on the ticker
    string — 173 tickers denote more than one company across time and a string
    join splices them into one series. See pg-skill's data-model reference.
    """
    out = {}
    try:
        sys.path.insert(0, r"C:\Users\ssair\trading-db")
        import pgdb
        with pgdb.connect() as pg:
            cur = pg.cursor()
            for sym in symbols:
                cur.execute("""
                    SELECT p.obs_date, p.close
                      FROM mkt.price_daily p
                     WHERE p.security_id = ref.resolve(%s, %s)
                       AND p.obs_date BETWEEN %s AND %s
                     ORDER BY p.obs_date
                """, (sym, end, start, end))
                rows = cur.fetchall()
                if rows:
                    out[sym] = {r[0]: float(r[1]) for r in rows if r[1]}
    except Exception as e:
        return {}, f"{type(e).__name__}: {e}"
    return out, None


def pct(series, day, offset=0):
    """Return over the session `offset` days after `day`, in percent.

    Walks forward to the next available bar so a holiday or weekend event date
    maps onto the session that actually absorbed it, and returns None rather
    than a number when the bar simply is not there.
    """
    days = sorted(series)
    idx = None
    for i, d in enumerate(days):
        if d >= day:
            idx = i
            break
    if idx is None:
        return None
    idx += offset
    if idx <= 0 or idx >= len(days):
        return None
    prev, cur = series[days[idx - 1]], series[days[idx]]
    if not prev:
        return None
    return round((cur / prev - 1) * 100, 2)


def add_reactions(events, prices, as_of):
    """Attach realized moves to every event on or before `as_of`."""
    for e in events:
        d = datetime.strptime(e["date"], "%Y-%m-%d").date()
        if d > as_of:
            e["status"] = "upcoming"
            continue
        e["status"] = "released"
        r, r1 = {}, {}
        for sym in REACTION_SYMBOLS:
            if sym not in prices:
                continue
            v = pct(prices[sym], d, 0)
            v1 = pct(prices[sym], d, 1)
            if v is not None:
                r[sym] = v
            if v1 is not None:
                r1[sym] = v1
        if not r:
            e["reaction"] = None
            # An event dated today whose session has not settled is not the
            # same thing as a hole in the store, and the briefing must not
            # report the first as if it were the second.
            e["reaction_note"] = (
                "the session for this date has not settled in the bar store "
                "yet — the event has been released, its market reaction has "
                "not been measured"
                if d >= as_of else
                "no bars for this date in the store")
            continue
        e["reaction"] = r
        e["reaction_next_day"] = r1 or None
        e["rate_path"] = _rate_path_read(r)
    return events


def _rate_path_read(r):
    """Did the market reprice the rate path on this event?

    Duration (TLT) leads; the XLF-XLU sector spread confirms. See the module
    docstring for why the spread cannot be trusted alone. Thresholds are
    deliberately coarse — sub-0.5% on TLT and sub-1pt on the spread are
    ordinary noise, and labelling those would manufacture signal.
    """
    tlt = r.get("TLT")
    spread = (round(r["XLF"] - r["XLU"], 2)
              if "XLF" in r and "XLU" in r else None)

    def sign(v, thresh):
        if v is None:
            return 0
        return 1 if v >= thresh else (-1 if v <= -thresh else 0)

    # Hawkish = duration sold, so a NEGATIVE TLT move is a POSITIVE hawkish
    # reading; the sector spread is already signed hawkish-positive.
    dur = -sign(tlt, 0.5)
    sec = sign(spread, 1.0)

    if dur and sec:
        if dur == sec:
            label = ("hawkish repricing — duration sold and banks outperformed "
                     "bond proxies" if dur > 0 else
                     "dovish repricing — duration bid and bond proxies "
                     "outperformed banks")
            agree = True
        else:
            label = ("mixed — duration and the sector spread disagree; treat "
                     "as no clean rate-path signal")
            agree = False
    elif dur:
        label = (f"hawkish on duration ({tlt}% on TLT); sector spread flat, "
                 f"which is typical when broad risk-off moves both legs"
                 if dur > 0 else
                 f"dovish on duration ({tlt}% on TLT); sector spread flat")
        agree = None
    elif sec:
        label = (f"sector spread leans {'hawkish' if sec > 0 else 'dovish'} "
                 f"({spread:+} pts) but duration did not confirm")
        agree = None
    else:
        label = "no rate-path repricing on either axis"
        agree = None

    return {"duration_tlt": tlt, "sector_spread_xlf_minus_xlu": spread,
            "read": label, "axes_agree": agree}


def summarize(events, as_of):
    """The month in one object: what landed, what is next, what it did."""
    released = [e for e in events if e.get("status") == "released"]
    upcoming = [e for e in events if e.get("status") == "upcoming"]

    biggest = None
    scored = [e for e in released
              if e.get("reaction") and e["reaction"].get("SPY") is not None]
    if scored:
        biggest = max(scored, key=lambda e: abs(e["reaction"]["SPY"]))

    # No cross-event average here. Averaging a CPI print against FOMC minutes
    # against a PPI release produces a number with no referent — the first
    # draft did exactly that and returned 0.13, which was neither wrong nor
    # about anything. Count the days instead, and surface the FOMC separately
    # because it is the event that actually sets the path.
    rated = [e for e in released if e.get("rate_path")]
    hawk = sum(1 for e in rated if e["rate_path"]["read"].startswith("hawkish"))
    dov = sum(1 for e in rated if e["rate_path"]["read"].startswith("dovish"))
    fomc = [e for e in released if e["event"] == "FOMC"]
    last_fomc = fomc[-1] if fomc else None

    return {
        "rate_path_days": {
            "hawkish": hawk, "dovish": dov,
            "neutral_or_mixed": len(rated) - hawk - dov,
            "basis": f"{len(rated)} released events with measurable reactions",
        },
        "last_fomc_in_window": ({
            "date": last_fomc["date"],
            "spy": (last_fomc.get("reaction") or {}).get("SPY"),
            "rate_path": last_fomc["rate_path"]["read"]
            if last_fomc.get("rate_path") else None,
        } if last_fomc else None),
        "events_released_in_window": len(released),
        "events_upcoming_in_window": len(upcoming),
        "next_event": ({"date": upcoming[0]["date"],
                        "event": upcoming[0]["event"],
                        "label": upcoming[0]["label"],
                        "covers": upcoming[0]["covers"],
                        "days_away": (datetime.strptime(
                            upcoming[0]["date"], "%Y-%m-%d").date() - as_of).days}
                       if upcoming else None),
        "next_high_importance": next(
            ({"date": e["date"], "event": e["event"],
              "days_away": (datetime.strptime(e["date"], "%Y-%m-%d").date()
                            - as_of).days}
             for e in upcoming if e["importance"] == "high"), None),
        "biggest_spy_reaction": ({"date": biggest["date"],
                                  "event": biggest["event"],
                                  "spy": biggest["reaction"]["SPY"]}
                                 if biggest else None),
        "interpretation_note": (
            "Reactions are same-session closes, so they capture the market's "
            "response but say nothing about whether the print BEAT or MISSED "
            "consensus — there is no expectations data here. A small reaction "
            "can mean an in-line print or an offsetting news flow; do not "
            "read it as 'the data was unremarkable'."),
    }


def main():
    p = argparse.ArgumentParser(
        description="Macro event calendar + realized reactions for Market Intel")
    p.add_argument("--back-days", type=int, default=35,
                   help="How far back to list events (default 35 — 'the month')")
    p.add_argument("--forward-days", type=int, default=21,
                   help="How far ahead to list scheduled events (default 21)")
    p.add_argument("--output", required=True)
    p.add_argument("--as-of", "--date", dest="as_of", default=None,
                   metavar="YYYY-MM-DD")
    a = p.parse_args()

    today = date.today()
    as_of = today
    if a.as_of:
        try:
            as_of = datetime.strptime(a.as_of, "%Y-%m-%d").date()
        except ValueError:
            raise SystemExit(f"--as-of must be YYYY-MM-DD, got '{a.as_of}'")
        if as_of > today:
            raise SystemExit(f"--as-of {as_of} is in the future")

    start = as_of - timedelta(days=a.back_days)
    end = as_of + timedelta(days=a.forward_days)

    events = [e for e in build_calendar() if start.isoformat() <= e["date"]
              <= end.isoformat()]

    prices, err = load_prices(REACTION_SYMBOLS, start - timedelta(days=10), as_of)
    events = add_reactions(events, prices, as_of)

    # Coverage honesty: if the requested forward window runs past what the
    # tables actually cover, say which series went dark rather than implying
    # the calendar is empty because nothing is scheduled.
    gaps = {}
    for series, last in SERIES_COVERAGE.items():
        if end.isoformat() > last:
            gaps[series] = f"schedule verified only through {last}"

    out = {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "as_of": str(as_of),
        "window": f"{start} .. {end}",
        "source": ("static published schedules (FOMC/BLS/BEA) + realized "
                   "reactions from Postgres mkt.price_daily"),
        "schedule_verified_on": "2026-08-07",
        "coverage": {"start": COVERAGE_START, "by_series": SERIES_COVERAGE},
        "reaction_symbols": REACTION_SYMBOLS,
        "events": events,
        "summary": summarize(events, as_of),
    }
    if a.as_of:
        out["historical"] = True
        out["historical_note"] = (
            f"Events after {as_of} are listed as upcoming-as-of-then with no "
            f"outcome attached. No price data after {as_of} was read.")
    if gaps:
        out["coverage_gaps"] = gaps
    if err or not prices:
        out["reaction_error"] = err or "no price data loaded"
        out["reaction_note"] = ("event dates are still correct; only the "
                                "realized-move columns are missing")

    with open(a.output, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"Macro calendar written to {a.output} "
          f"({len(events)} events, {out['summary']['events_released_in_window']} "
          f"released / {out['summary']['events_upcoming_in_window']} upcoming)")


if __name__ == "__main__":
    main()
