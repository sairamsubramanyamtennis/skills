"""
qm_pg_data.py — Postgres data layer for the QM autoresearch engine.

Replaces the old local-file path (Yahoo `sp500_prices_daily.parquet` + a
membership CSV), which was survivorship-biased before ~2010: only 49% of the
point-in-time S&P 500 members on 2000-01-03 had prices in that file, and the
missing half was precisely the names that were later acquired or delisted.

Everything here is keyed on **security_id**, never on a ticker string. 173
tickers denote more than one company across time (ABX = Barrick then Abacus),
so a ticker-keyed panel silently merges two firms into one price series.

Source: PostgreSQL `trading` on localhost:5433
  mkt.price_daily        49.4M split-adjusted daily bars, delisted-inclusive,
                         2003-09-10 onward (Polygon/Massive's own history floor)
  ref.index_membership   point-in-time S&P 500 membership, 1996-2026
  ref.security           name / sector / primary_ticker
  ref.ticker_span        ticker <-> security_id, valid-dated

BASIS: prices are SPLIT-adjusted only — price return, no dividends. The SPY
benchmark returned here comes from the same table on the same basis, so the
comparison is apples-to-apples. Do not mix in a Yahoo adjusted-close series
(total return); that overstates the benchmark by roughly 2pp a year.

The panel is cached to parquet because the autoresearch harness runs each
experiment as its own subprocess — without a cache, 30 experiments would each
re-pull ~3.5M rows.
"""
from __future__ import annotations

import os
import sys

import pandas as pd

TRADING_DB = r"C:\Users\ssair\trading-db"
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_pg_cache")

# Polygon/Massive grouped-daily history begins here. Nothing earlier exists.
PANEL_FLOOR = "2003-09-10"
DEFAULT_INDEX = "SP500"
BENCHMARK = "SPY"


def _pgdb():
    if TRADING_DB not in sys.path:
        sys.path.insert(0, TRADING_DB)
    import pgdb
    return pgdb


def _connect():
    return _pgdb().connect()


# ---------------------------------------------------------------------------
# Universe
# ---------------------------------------------------------------------------

def member_ids(index_code=DEFAULT_INDEX, start=PANEL_FLOOR, end=None):
    """Every security_id that was an index member at any point in [start, end]."""
    end = end or "2026-12-31"
    with _connect() as pg:
        cur = pg.cursor()
        cur.execute(
            "SELECT DISTINCT security_id FROM ref.index_membership "
            "WHERE index_code = %s AND valid && daterange(%s::date, %s::date)",
            (index_code, start, end),
        )
        return sorted(r[0] for r in cur.fetchall())


def load_membership(index_code=DEFAULT_INDEX, start=PANEL_FLOOR, end=None):
    """
    Point-in-time membership as sorted [(Timestamp, frozenset(security_id))].

    One entry per date on which the index composition changed. The engine
    forward-fills from the last change on or before each rebalance date, so
    the universe it screens is the universe that existed that day — no
    survivorship, no look-ahead.
    """
    end = end or "2026-12-31"
    with _connect() as pg:
        cur = pg.cursor()
        cur.execute(
            "SELECT security_id, lower(valid), upper(valid) FROM ref.index_membership "
            "WHERE index_code = %s AND valid && daterange(%s::date, %s::date)",
            (index_code, start, end),
        )
        spans = cur.fetchall()

    if not spans:
        return None

    # Every date on which somebody entered or left.
    change_dates = set()
    for _sid, lo, hi in spans:
        if lo is not None:
            change_dates.add(lo)
        if hi is not None:
            change_dates.add(hi)
    change_dates = sorted(d for d in change_dates if d is not None)

    out = []
    for d in change_dates:
        members = frozenset(
            sid for sid, lo, hi in spans
            if (lo is None or lo <= d) and (hi is None or d < hi)
        )
        if members:
            out.append((pd.Timestamp(d), members))
    return out


def load_sectors(index_code=DEFAULT_INDEX):
    """
    {security_id: sector}. Only ~60% of historical members carry a sector —
    the gaps are mostly long-delisted names. Callers must treat a missing
    sector as unknown rather than lumping them into one bucket, or the
    sector cap will bind on an artefact.
    """
    with _connect() as pg:
        cur = pg.cursor()
        cur.execute(
            "SELECT s.security_id, s.sector FROM ref.security s "
            "WHERE s.sector IS NOT NULL AND s.security_id IN ("
            "  SELECT security_id FROM ref.index_membership WHERE index_code = %s)",
            (index_code,),
        )
        return {sid: sec for sid, sec in cur.fetchall()}


def id_to_ticker(index_code=DEFAULT_INDEX):
    """{security_id: primary_ticker} — for human-readable reporting ONLY."""
    with _connect() as pg:
        cur = pg.cursor()
        cur.execute(
            "SELECT s.security_id, COALESCE(s.primary_ticker, s.name, s.security_id::text) "
            "FROM ref.security s WHERE s.security_id IN ("
            "  SELECT security_id FROM ref.index_membership WHERE index_code = %s)",
            (index_code,),
        )
        return dict(cur.fetchall())


# ---------------------------------------------------------------------------
# Prices
# ---------------------------------------------------------------------------

def _panel_cache_path(index_code, start, end):
    return os.path.join(CACHE_DIR, f"panel_{index_code}_{start}_{end}.parquet")


def load_panel(index_code=DEFAULT_INDEX, start=PANEL_FLOOR, end=None, use_cache=True):
    """
    Wide daily close panel: index = date, columns = security_id (int).

    Covers every security that was an index member at any point in the window,
    including those later delisted — that is what makes it survivorship-free.
    """
    end = end or pd.Timestamp.today().strftime("%Y-%m-%d")
    path = _panel_cache_path(index_code, start, end)

    if use_cache and os.path.exists(path):
        df = pd.read_parquet(path)
        df.index = pd.to_datetime(df.index)
        df.columns = [int(c) for c in df.columns]
        return df.sort_index()

    with _connect() as pg:
        cur = pg.cursor()
        cur.execute(
            "SELECT p.obs_date, p.security_id, p.close "
            "FROM mkt.price_daily p "
            "WHERE p.obs_date BETWEEN %s::date AND %s::date "
            "  AND p.security_id IN ("
            "    SELECT security_id FROM ref.index_membership "
            "    WHERE index_code = %s AND valid && daterange(%s::date, %s::date))",
            (start, end, index_code, start, end),
        )
        rows = cur.fetchall()

    if not rows:
        return None

    long = pd.DataFrame(rows, columns=["obs_date", "security_id", "close"])
    long["obs_date"] = pd.to_datetime(long["obs_date"])
    long["close"] = pd.to_numeric(long["close"], errors="coerce")
    df = long.pivot(index="obs_date", columns="security_id", values="close").sort_index()

    if use_cache:
        os.makedirs(CACHE_DIR, exist_ok=True)
        out = df.copy()
        out.columns = [str(c) for c in out.columns]
        out.to_parquet(path)

    return df


def load_benchmark(ticker=BENCHMARK, start=PANEL_FLOOR, end=None):
    """
    Benchmark daily closes as a Series — same table, same split-adjusted
    price-return basis as the panel.
    """
    end = end or pd.Timestamp.today().strftime("%Y-%m-%d")
    with _connect() as pg:
        cur = pg.cursor()
        cur.execute(
            "SELECT p.obs_date, p.close FROM mkt.price_daily p "
            "JOIN ref.ticker_span t ON t.security_id = p.security_id "
            "                      AND p.obs_date <@ t.valid "
            "WHERE t.ticker = %s AND p.obs_date BETWEEN %s::date AND %s::date "
            "ORDER BY p.obs_date",
            (ticker, start, end),
        )
        rows = cur.fetchall()

    if not rows:
        return None
    s = pd.Series(
        [float(c) for _d, c in rows],
        index=pd.to_datetime([d for d, _c in rows]),
        name=ticker,
    )
    return s[~s.index.duplicated(keep="last")].sort_index()


# ---------------------------------------------------------------------------
# Coverage diagnostics — run this before believing any backtest
# ---------------------------------------------------------------------------

def coverage_report(index_code=DEFAULT_INDEX, dates=None):
    """
    For each date: how many point-in-time members actually have a price.

    A number well below 100% means the backtest silently screened a subset of
    the real universe. If the unpriced names skew toward the acquired and the
    bankrupt, the result is survivorship-inflated regardless of how careful
    the rest of the engine is.
    """
    dates = dates or ["2004-06-30", "2006-06-30", "2008-06-30", "2010-06-30",
                      "2015-06-30", "2020-06-30", "2026-06-30"]
    out = []
    with _connect() as pg:
        cur = pg.cursor()
        for d in dates:
            cur.execute(
                "SELECT count(*) FROM ref.index_membership m "
                "WHERE m.index_code = %s AND m.valid @> %s::date",
                (index_code, d),
            )
            total = cur.fetchone()[0]
            cur.execute(
                "SELECT count(*) FROM ref.index_membership m "
                "WHERE m.index_code = %s AND m.valid @> %s::date AND EXISTS ("
                "  SELECT 1 FROM mkt.price_daily p WHERE p.security_id = m.security_id "
                "    AND p.obs_date BETWEEN %s::date - 10 AND %s::date)",
                (index_code, d, d, d),
            )
            priced = cur.fetchone()[0]
            out.append({"date": d, "members": total, "priced": priced,
                        "pct": round(100.0 * priced / max(total, 1), 1)})
    return pd.DataFrame(out)


if __name__ == "__main__":
    print("Coverage of point-in-time members by priced securities:")
    print(coverage_report().to_string(index=False))

    panel = load_panel()
    print(f"\nPanel: {panel.shape[0]} days x {panel.shape[1]} securities, "
          f"{panel.index.min().date()} .. {panel.index.max().date()}")

    memb = load_membership()
    print(f"Membership: {len(memb)} change-dates, "
          f"{memb[0][0].date()} .. {memb[-1][0].date()}")

    spy = load_benchmark()
    print(f"Benchmark {BENCHMARK}: {len(spy)} closes, "
          f"{spy.index.min().date()} .. {spy.index.max().date()}")

    sec = load_sectors()
    print(f"Sectors: {len(sec)} securities carry one")
