#!/usr/bin/env python
r"""
inventory.py — what is actually in the Postgres `trading` database, right now.

Prints one table per line with row count, size, and the date span it covers, so
the shape of the database is visible without opening psql or guessing which of
the eleven former SQLite files a table came from.

Row counts default to the planner's estimate (`reltuples`), which is instant.
`mkt.price_daily` holds ~49M rows, and an exact `count(*)` on it is a seq scan
that takes seconds — fine when you want it, wasteful when you are orienting.
Pass --exact when a precise number matters.

Usage:
    python inventory.py                 # every schema, estimated counts
    python inventory.py --exact         # exact counts (slower on mkt.*)
    python inventory.py --schema res    # one schema
    python inventory.py --columns       # add every column and type
    python inventory.py --checks        # run the integrity checks too
    python inventory.py --json          # machine-readable
"""
from __future__ import annotations

import argparse
import json
import sys

# The shared adapter owns the DSN (localhost:5433, pgpass for the password).
sys.path.insert(0, r"C:\Users\ssair\trading-db")

RESEARCH_SCHEMAS = ("ref", "mkt", "evt", "res", "etl", "stg")

# Time columns worth reporting a span for, in the order they should be tried.
DATE_COLS = ("obs_date", "filed_date", "expected_date", "ex_date", "d0",
             "date", "valid", "staged_at", "created_at")

# One line of orientation per table. Anything not listed still gets reported —
# this is a gloss, not a gate.
BLURB = {
    "ref.issuer": "One row per EDGAR filer (CIK). The company behind a listing.",
    "ref.security": "One row per LISTING, not per issuer — GOOG and GOOGL are "
                    "two securities sharing an issuer_cik.",
    "ref.ticker_span": "Ticker -> security_id over a date range. The identity "
                       "table: a gist EXCLUDE makes one ticker meaning two "
                       "securities on one date unstorable.",
    "ref.index_membership": "S&P 500 membership as intervals (~1,268 rows), not "
                            "dense daily rows. Point-in-time truth.",
    "ref.index_member_daily": "Derived dense view of the above — who was in the "
                              "index on a given day. Cannot drift out of sync.",
    "ref.trading_day": "The market calendar.",
    "mkt.price_daily": "The spine: split-adjusted daily closes + volume for the "
                       "whole US market, delisted names included.",
    "mkt.sp500_panel": "Matview of price_daily filtered to actual membership — "
                       "member-days only. Use this for survivorship-free work.",
    "mkt.dividend": "Cash distributions. Keyed (security_id, ex_date, amount, "
                    "freq) because a regular and a special can share an ex-date.",
    "mkt.split": "Split events.",
    "evt.earnings_filing": "8-K earnings filings from EDGAR.",
    "evt.earnings_event": "One announcement per row, with the ex-ante "
                          "expected_date. Trade off expected_date, never "
                          "filed_date — the filing date is realised, not knowable.",
    "res.run": "One row per screen or backtest, with universe + data_asof NOT "
               "NULL by design: a result cannot be stored without declaring "
               "whether it used point-in-time membership.",
    "res.screen_result": "Every QM screen row ever produced, keyed to run_id.",
    "res.backtest_period": "Per-rebalance returns for a backtest run, with SPY "
                           "and RSP alongside.",
    "res.backtest_selection": "What each backtest actually held per date.",
    "res.holding_snapshot": "Latest holdings for a run.",
    "res.latest_screen": "View: the newest screen under qm_panel_v2, joined to "
                         "tickers and sectors.",
    "res.top10_daily": "View: the top 10 of every screen date.",
    "etl.source_file": "Staging manifest — which SQLite file each stg table came "
                       "from and how many rows it had.",
    "etl.watermark": "Ingest progress markers.",
    "etl.news": "Market-news lines scraped into the screener workbooks.",
}


def connect():
    try:
        import pgdb
        return pgdb.connect()
    except Exception:
        import psycopg2
        return psycopg2.connect(host="localhost", port=5433,
                                user="postgres", dbname="trading")


def q(cur, sql, params=None):
    cur.execute(sql, params)
    return cur.fetchall()


def collect(cur, schemas, exact=False, want_columns=False):
    rows = q(cur, """
        SELECT n.nspname AS sch, c.relname AS tbl, c.relkind AS kind,
               c.reltuples::bigint AS est_rows,
               pg_total_relation_size(c.oid) AS bytes,
               pg_size_pretty(pg_total_relation_size(c.oid)) AS size
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = ANY(%s) AND c.relkind IN ('r','m','v','p')
        ORDER BY n.nspname, c.relname
    """, (list(schemas),))

    cols_by_tbl = {}
    if want_columns or True:      # always needed to find a date column
        for sch, tbl, col, typ in q(cur, """
            SELECT table_schema, table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = ANY(%s)
            ORDER BY table_schema, table_name, ordinal_position
        """, (list(schemas),)):
            cols_by_tbl.setdefault(f"{sch}.{tbl}", []).append((col, typ))

    out = []
    for sch, tbl, kind, est, nbytes, size in rows:
        obj = f"{sch}.{tbl}"
        cols = cols_by_tbl.get(obj, [])
        colnames = [c for c, _ in cols]

        n = None
        if exact or (kind == 'v') or (est is not None and est < 0):
            try:
                n = q(cur, f'SELECT count(*) FROM {obj}')[0][0]
            except Exception:
                n = None
        rowcount = n if n is not None else (est if est and est > 0 else None)

        span = None
        for dc in DATE_COLS:
            if dc in colnames:
                try:
                    if dc == "valid":         # a daterange, not a date
                        lo, hi = q(cur, f'SELECT min(lower({dc}))::text, '
                                        f'max(upper({dc}))::text FROM {obj}')[0]
                    else:
                        lo, hi = q(cur, f'SELECT min({dc})::text, '
                                        f'max({dc})::text FROM {obj}')[0]
                    if lo or hi:
                        span = {"column": dc, "from": (lo or "")[:10],
                                "to": (hi or "")[:10]}
                except Exception:
                    pass
                break

        out.append({
            "object": obj, "schema": sch, "name": tbl,
            "kind": {"r": "table", "m": "matview", "v": "view",
                     "p": "partitioned"}[kind],
            "rows": rowcount, "exact": n is not None,
            "size": size, "bytes": nbytes,
            "span": span,
            "columns": [{"name": c, "type": t} for c, t in cols],
            "note": BLURB.get(obj, ""),
        })
    return out


def checks(cur):
    """Integrity checks that matter for this database specifically.

    These are not generic hygiene — each one guards an invariant that has
    already been violated once in this workspace's history, which is why it is
    worth spending a query on.
    """
    res = []

    def add(name, sql, expect_zero=True, why=""):
        try:
            v = q(cur, sql)[0][0]
            res.append({"check": name, "value": int(v),
                        "ok": (int(v) == 0) if expect_zero else True, "why": why})
        except Exception as e:
            res.append({"check": name, "value": None, "ok": None,
                        "why": f"{why} (failed: {type(e).__name__})"})

    add("securities with no ticker span",
        "SELECT count(*) FROM ref.security s WHERE NOT EXISTS "
        "(SELECT 1 FROM ref.ticker_span t WHERE t.security_id = s.security_id)",
        why="a security nothing can resolve to is unreachable")
    add("price rows with no security",
        "SELECT count(*) FROM mkt.price_daily p WHERE NOT EXISTS "
        "(SELECT 1 FROM ref.security s WHERE s.security_id = p.security_id)",
        why="orphan prices would silently drop out of every join")
    add("screen rows whose run is missing",
        "SELECT count(*) FROM res.screen_result r WHERE NOT EXISTS "
        "(SELECT 1 FROM res.run u WHERE u.run_id = r.run_id)",
        why="a result with no provenance row")
    add("runs with universe='unknown'",
        "SELECT count(*) FROM res.run WHERE universe = 'unknown'",
        expect_zero=False,
        why="legacy imports where point-in-time-ness was unrecoverable; new "
            "work should write 'pit' or 'current'")
    add("tickers meaning more than one company",
        "SELECT count(*) FROM (SELECT ticker FROM ref.ticker_span "
        "GROUP BY ticker HAVING count(*) > 1) x",
        expect_zero=False,
        why="the reason never to join on a ticker string")
    add("panel dates ahead of the newest screen",
        "SELECT count(*) FROM (SELECT 1 WHERE (SELECT max(obs_date) FROM "
        "mkt.price_daily) > (SELECT max(obs_date) FROM res.screen_result)) x",
        expect_zero=False,
        why="1 means prices are fresher than the last screen — normal between "
            "the daily ingest and the next screener run")
    return res


def human(data, chk, want_columns):
    # Windows consoles default to cp1252 when stdout is redirected, and company
    # names in this data are not all ASCII. Output stays ASCII-only; this covers
    # the data.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    by_schema = {}
    for t in data:
        by_schema.setdefault(t["schema"], []).append(t)

    total = sum(t["bytes"] for t in data)
    _ns = len(by_schema)
    print(f"\ntrading — {len(data)} objects across {_ns} "
          f"schema{'s' if _ns != 1 else ''}, "
          f"{total/1e9:.1f} GB\n")

    for sch in sorted(by_schema):
        objs = by_schema[sch]
        print(f"-- {sch} " + "-" * (66 - len(sch)))
        for t in objs:
            n = t["rows"]
            nstr = "—" if n is None else f"{n:,}{'' if t['exact'] else '~'}"
            span = ""
            if t["span"]:
                span = f"  {t['span']['from']} -> {t['span']['to']}"
            print(f"  {t['name']:<26} {nstr:>14}  {t['size']:>9}{span}")
            if t["note"]:
                print(f"      {t['note']}")
            if want_columns:
                print("      cols: " + ", ".join(
                    f"{c['name']}" for c in t["columns"]))
        print()

    if chk:
        print("-- checks " + "-" * 62)
        for c in chk:
            mark = "ok " if c["ok"] else ("!! " if c["ok"] is False else "?? ")
            print(f"  {mark}{c['check']:<42} {c['value']}")
            if c["why"]:
                print(f"      {c['why']}")
        print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema", action="append",
                    help="limit to a schema (repeatable); default all")
    ap.add_argument("--exact", action="store_true",
                    help="exact count(*) instead of planner estimates")
    ap.add_argument("--columns", action="store_true", help="list every column")
    ap.add_argument("--checks", action="store_true", help="run integrity checks")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    schemas = args.schema or list(RESEARCH_SCHEMAS)
    con = connect()
    try:
        cur = con.cursor()
        data = collect(cur, schemas, args.exact, args.columns)
        chk = checks(cur) if args.checks else None
    finally:
        con.close()

    if args.json:
        print(json.dumps({"objects": data, "checks": chk}, indent=2, default=str))
    else:
        human(data, chk, args.columns)


if __name__ == "__main__":
    main()
