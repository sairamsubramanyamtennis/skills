"""
Build the cached price panel for pre-earnings drift research.

Source is the Postgres `trading` database (localhost:5433): evt.earnings_event
for the announcement dates, mkt.price_daily for the bars. The pull is a few
million rows and the result is only ~50 MB wide, so we pay it once and cache it;
every later run of event_study.py loads in under a second.

THE PANEL IS KEYED BY security_id, NOT BY TICKER. 217 tickers in this universe
are reused by unrelated companies, and a ticker-keyed price column splices them
into one series -- a 2016 EMC Corp event would be priced partly against a 2024
Global X ETF's bars. Postgres already resolves every event to the right security,
so keying on the id removes that whole failure mode rather than patching it with
a listing-segment filter.

Outputs (to --outdir, default the skill's data/ folder):
    close.parquet    date x security_id   split-adjusted close
    volume.parquet   date x security_id   share volume
    events.parquet   the event table, already aligned to trading days
    symbols.parquet  security_id -> ticker / name, for labels and benchmarks

Prices are split-adjusted but NOT dividend-adjusted, on both the stock and the
benchmark side, so the abnormal returns are price returns net of a price-return
benchmark. That is consistent; it is only wrong if you mix in a total-return
series from somewhere else.
"""
from __future__ import annotations

import argparse
import sys
import time
from io import StringIO
from pathlib import Path

import pandas as pd

PG_ADAPTER_DIR = r"C:\Users\ssair\trading-db"

# Benchmarks. RSP (equal-weight S&P) is the default because the event portfolio
# is equal-weighted -- benchmarking equal-weight events against cap-weighted SPY
# smuggles in a size factor that shows up as fake drift.
BENCHMARKS = ["SPY", "RSP"]
SECTOR_ETFS = ["XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB",
               "XLRE", "XLC"]


def _pgdb():
    if PG_ADAPTER_DIR not in sys.path:
        sys.path.insert(0, PG_ADAPTER_DIR)
    import pgdb
    return pgdb


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default=str(Path(__file__).resolve().parents[1] / "data"))
    ap.add_argument("--end-date", default=None,
                    help="cap the panel here (YYYY-MM-DD) for a reproducible rebuild")
    args = ap.parse_args()

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    pgdb = _pgdb()
    with pgdb.connect() as pg:
        cur = pg.cursor()

        # ---- events ---------------------------------------------------------
        # No listing-segment join: security_id is already the point-in-time
        # identity, resolved when the filing was harvested.
        cur.execute("""
            SELECT e.security_id, e.cik, e.seq, e.filed_date, e.expected_date,
                   e.gap_days, e.session
              FROM evt.earnings_event e
             WHERE e.expected_date IS NOT NULL
               AND (%s::date IS NULL OR e.filed_date <= %s::date)
             ORDER BY e.security_id, e.seq
        """, (args.end_date, args.end_date))
        ev = pd.DataFrame(cur.fetchall(), columns=[
            "security_id", "cik", "seq", "filed_date", "expected_date",
            "gap_days", "session"])
        sec_ids = sorted(ev["security_id"].unique().tolist())
        print(f"events {len(ev):,}  securities {len(sec_ids):,}")

        # ---- benchmark / sector ETF identities ------------------------------
        bench_tickers = BENCHMARKS + SECTOR_ETFS
        cur.execute("""SELECT t.ticker, ref.resolve(t.ticker, CURRENT_DATE)
                         FROM unnest(%s::text[]) AS t(ticker)""", (bench_tickers,))
        bench = {t: sid for t, sid in cur.fetchall() if sid is not None}
        missing_bench = [t for t in bench_tickers if t not in bench]
        if missing_bench:
            print(f"  WARNING: no security for {missing_bench}")
        want = sorted(set(sec_ids) | set(bench.values()))

        # ---- prices ---------------------------------------------------------
        print(f"loading bars for {len(want):,} securities ...", flush=True)
        sql = """SELECT p.obs_date, p.security_id, p.close, p.volume
                   FROM mkt.price_daily p
                  WHERE p.security_id = ANY(%s)
                    AND (%s::date IS NULL OR p.obs_date <= %s::date)"""
        q = cur.mogrify(sql, (want, args.end_date, args.end_date)).decode()
        buf = StringIO()
        cur.copy_expert(f"COPY ({q}) TO STDOUT WITH CSV HEADER", buf)
        buf.seek(0)
        px = pd.read_csv(buf, parse_dates=["obs_date"])
        print(f"  {len(px):,} bars in {time.time()-t0:.0f}s")

        # ---- labels ---------------------------------------------------------
        cur.execute("""SELECT s.security_id, s.primary_ticker, s.name
                         FROM ref.security s WHERE s.security_id = ANY(%s)""", (want,))
        symbols = pd.DataFrame(cur.fetchall(),
                               columns=["security_id", "ticker", "name"])

    symbols["role"] = symbols["ticker"].map(
        lambda t: "benchmark" if t in bench_tickers else "stock")

    close = px.pivot_table(index="obs_date", columns="security_id", values="close").sort_index()
    volume = px.pivot_table(index="obs_date", columns="security_id", values="volume").sort_index()

    missing = sorted(set(sec_ids) - set(close.columns))
    if missing:
        print(f"  {len(missing)} event securities have no bars: {missing[:10]}")

    # ---- align each event to a trading-day index ----------------------------
    # day 0 = the first session on which the news is public.
    #   BMO / DURING filed on D -> D itself already reflects it
    #   AMC filed on D          -> D is still a clean pre-event day, so day 0 = D+1
    # Getting this backwards puts the announcement return inside the "pre" window
    # and produces drift that is really just the earnings reaction.
    sessions = close.index
    ev["filed_date"] = pd.to_datetime(ev["filed_date"])
    ev["expected_date"] = pd.to_datetime(ev["expected_date"])

    def to_idx(dates: pd.Series, side: str) -> pd.Series:
        """Map dates onto trading-day positions ('ffill' = on/before, 'bfill' = on/after)."""
        meth = "ffill" if side == "before" else "bfill"
        loc = sessions.get_indexer(pd.to_datetime(dates), method=meth)
        return pd.Series(loc, index=dates.index).replace(-1, pd.NA)

    ev["filed_idx"] = to_idx(ev["filed_date"], "after")
    ev["expected_idx"] = to_idx(ev["expected_date"], "after")
    ev["event0_idx"] = ev["filed_idx"] + (ev["session"] == "AMC").astype(int)

    ev = ev.dropna(subset=["filed_idx", "expected_idx"])
    for c in ("filed_idx", "expected_idx", "event0_idx"):
        ev[c] = ev[c].astype(int)
    ev = ev[ev["security_id"].isin(close.columns)].reset_index(drop=True)
    ev = ev.merge(symbols[["security_id", "ticker"]], on="security_id", how="left")

    close.to_parquet(out / "close.parquet")
    volume.to_parquet(out / "volume.parquet")
    ev.to_parquet(out / "events.parquet")
    symbols.to_parquet(out / "symbols.parquet")

    print(f"\nwrote {out}")
    print(f"  close.parquet   {close.shape[0]:,} sessions x {close.shape[1]:,} securities")
    print(f"  events.parquet  {len(ev):,} events, {ev['security_id'].nunique():,} securities")
    print(f"  span {close.index.min():%Y-%m-%d} -> {close.index.max():%Y-%m-%d}")
    print(f"done in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
