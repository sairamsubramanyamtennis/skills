"""
qm_screen_source.py — read a published screen back out of Postgres.

The pipeline's single handoff. `run_qm.py` publishes the screener's result to
`res.screen_result` first, and every downstream step (workbook, pick tracking,
email) then reads it back through here. Nothing downstream parses the CSV or the
workbook, so those become pure outputs: regenerating a report can never disagree
with what was actually recorded, and a failed publish stops the run instead of
producing a report for a screen that was never stored.

Columns come back with the screener's own header names, so callers that were
written against `qm_full_ranking.csv` need no other change.

Identity: rows key on `security_id`; the ticker printed is the security's
canonical form (BRK.B, not BRK-B), which is what every price source keys on.
"""
from __future__ import annotations

import datetime as dt
import sys

import pandas as pd

PG_ADAPTER_DIR = r"C:\Users\ssair\trading-db"
DEFAULT_RUN_LABEL = "qm_panel_v2"

# res.screen_result column -> the screener's own CSV header
COLUMNS = [
    ("rank", "Rank"),
    ("ticker", "Ticker"),
    ("name", "Company"),
    ("sector", "Sector"),
    ("price", "Price"),
    ("mom", "6-1M VolAdj"),
    ("ret3m", "3M Ret%"),
    ("ret1m", "1M Ret%"),
    ("fip", "FIP Score"),
    ("fip_pctpos", "Pct Positive Days"),
    ("fip_r2", "R-Squared"),
    ("momrank", "Mom Rank"),
    ("fiprank", "FIP Rank"),
    ("qmscore", "Composite QM Rank"),
    ("percentile", "Percentile"),
    ("signal", "Signal"),
]


def _pgdb():
    if PG_ADAPTER_DIR not in sys.path:
        sys.path.insert(0, PG_ADAPTER_DIR)
    import pgdb
    return pgdb


def fetch_screen(screen_date=None, run_label: str = DEFAULT_RUN_LABEL) -> pd.DataFrame:
    """One published screen, shaped like the screener's own output.

    `screen_date=None` takes the newest published date for the run rather than
    assuming today: on a holiday, or when the job runs after midnight, today's
    date has no screen and silently returning empty would be worse than
    returning the screen that actually exists.
    """
    pgdb = _pgdb()
    if isinstance(screen_date, str):
        screen_date = dt.date.fromisoformat(screen_date)

    with pgdb.connect() as pg:
        cur = pg.cursor()
        cur.execute("SELECT run_id FROM res.run WHERE label = %s", (run_label,))
        row = cur.fetchone()
        if row is None:
            raise RuntimeError(f"no res.run labelled {run_label}")
        run_id = row[0]

        if screen_date is None:
            cur.execute("SELECT max(obs_date) FROM res.screen_result WHERE run_id = %s",
                        (run_id,))
            screen_date = cur.fetchone()[0]
            if screen_date is None:
                raise RuntimeError(f"run {run_label} has no screens")

        cur.execute("""
            SELECT s.rank, sec.primary_ticker, sec.name, sec.sector, s.price,
                   s.mom, s.ret3m, s.ret1m, s.fip, s.fip_pctpos, s.fip_r2,
                   s.momrank, s.fiprank, s.qmscore, s.percentile, s.signal
              FROM res.screen_result s
              JOIN ref.security sec USING (security_id)
             WHERE s.run_id = %s AND s.obs_date = %s
             ORDER BY s.rank
        """, (run_id, screen_date))
        rows = cur.fetchall()

    df = pd.DataFrame(rows, columns=[hdr for _, hdr in COLUMNS])
    df.attrs["screen_date"] = screen_date
    df.attrs["run_label"] = run_label
    return df


def screen_date_of(df: pd.DataFrame):
    """The date a frame from fetch_screen() belongs to."""
    return df.attrs.get("screen_date")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Print a published screen from Postgres")
    ap.add_argument("--screen-date", default=None)
    ap.add_argument("--run-label", default=DEFAULT_RUN_LABEL)
    ap.add_argument("--head", type=int, default=10)
    a = ap.parse_args()
    d = fetch_screen(a.screen_date, a.run_label)
    print(f"{len(d)} rows for {screen_date_of(d)} [{a.run_label}]")
    print(d.head(a.head).to_string(index=False))
