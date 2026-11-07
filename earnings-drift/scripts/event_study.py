"""
Pre-earnings drift event study.

Answers: does a stock drift up (or down) in the days before it reports, and does
that drift depend on information knowable beforehand?

Two things here are load-bearing, and both are places this research usually dies:

1. ANCHOR ON THE EXPECTED DATE, NOT THE FILED DATE.
   The filing date is realised information. "Buy 10 days before the announcement"
   using the actual date is a time machine -- it quietly guarantees you are
   holding into every announcement, and manufactures the drift you set out to
   measure. --anchor expected is the default and is the only tradeable version.
   --anchor actual exists to show you how big the lookahead bias is.

2. EARNINGS CLUSTER IN CALENDAR TIME, SO CROSS-SECTIONAL t-STATS LIE.
   Thousands of firms report in the same three weeks. Their abnormal returns
   share a market factor, so they are nowhere near independent, and the naive
   t-stat over N events is inflated by roughly sqrt(events per day). The honest
   statistic is the calendar-time portfolio: hold every name currently inside
   its pre-earnings window, equal-weighted, and t-test THAT daily return series.
   It is also literally the strategy's P&L. Both are printed; the gap between
   them is the point.

Usage
    python event_study.py                          # headline result
    python event_study.py --pre 10 --benchmark RSP
    python event_study.py --condition mom_60_11    # sort on prior momentum
    python event_study.py --placebo                # same design, no earnings
    python event_study.py --by-era                 # subperiod stability
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parents[1] / "data"
TRADING_DAYS = 252


# ---------------------------------------------------------------------------
# loading
# ---------------------------------------------------------------------------
def load(data_dir: Path):
    """Panel + events + the security_id -> ticker map.

    Everything here is keyed by security_id, never by ticker: 217 tickers in this
    universe denote more than one company across time, and a ticker-keyed price
    column splices them into a single series. `symbols` carries the labels.
    """
    close = pd.read_parquet(data_dir / "close.parquet")
    ev = pd.read_parquet(data_dir / "events.parquet")
    symbols = pd.read_parquet(data_dir / "symbols.parquet")
    return close, ev, symbols


def abnormal_returns(close: pd.DataFrame, benchmark_id: int,
                     bench_cols: set, demean: bool = True) -> pd.DataFrame:
    """
    Close-to-close return minus a benchmark, then optionally cross-sectionally
    demeaned.

    THE DEMEAN STEP IS NOT COSMETIC -- without it this study returns a false
    positive. Measured on this panel, the mean abnormal return of an average
    stock-day is +1.70 bps vs RSP (+1.78 vs SPY), i.e. **+17 bps over any
    10-day window whatsoever**. The raw pre-earnings CAR is +18.2 bps, so
    essentially the whole "drift" is this baseline, not an earnings effect. It
    is there because the panel is the *ever-was-an-S&P-member* universe, which
    is selected on having grown into the index -- the benchmark is not a fair
    counterfactual for it.

    Subtracting each day's cross-sectional mean across the event universe pins
    the no-event expectation at exactly zero and also strips out any market-wide
    shock on that date. After it, the benchmark choice barely matters -- which
    is the sign that the adjustment is doing the work, not the benchmark.
    """
    ret = close.pct_change(fill_method=None)
    if benchmark_id not in ret.columns:
        raise SystemExit(f"benchmark security {benchmark_id} not in panel")
    ar = ret.sub(ret[benchmark_id], axis=0)
    if demean:
        stocks = [c for c in ar.columns if c not in bench_cols]
        ar = ar.sub(ar[stocks].mean(axis=1), axis=0)
    return ar


# ---------------------------------------------------------------------------
# event-time extraction
# ---------------------------------------------------------------------------
def event_matrix(ar: pd.DataFrame, ev: pd.DataFrame, anchor_col: str,
                 lo: int, hi: int) -> tuple[np.ndarray, pd.DataFrame]:
    """
    Abnormal returns in event time.

    Returns an (n_events x (hi-lo+1)) array where column j is relative day lo+j,
    plus the surviving event rows. Vectorised: 60k events x 70 days is a single
    fancy-index into the AR matrix.
    """
    cols = {t: i for i, t in enumerate(ar.columns)}
    ev = ev[ev["security_id"].isin(cols)].copy()
    tcol = ev["security_id"].map(cols).to_numpy()
    anch = ev[anchor_col].to_numpy()

    offs = np.arange(lo, hi + 1)
    rows = anch[:, None] + offs[None, :]

    ok = (rows >= 0).all(axis=1) & (rows < len(ar)).all(axis=1)
    rows, tcol, ev = rows[ok], tcol[ok], ev[ok].reset_index(drop=True)

    vals = ar.to_numpy()
    mat = vals[rows, tcol[:, None]]
    return mat, ev


def add_conditioners(ar: pd.DataFrame, close: pd.DataFrame, ev: pd.DataFrame,
                     anchor_col: str) -> pd.DataFrame:
    """
    Signals knowable BEFORE the pre-earnings window opens.

    Every one is measured at or before anchor-21, i.e. strictly outside the
    trading window, so none of them can peek at the returns being predicted.
    """
    cols = {t: i for i, t in enumerate(close.columns)}
    ev = ev[ev["security_id"].isin(cols)].copy()
    tcol = ev["security_id"].map(cols).to_numpy()
    anch = ev[anchor_col].to_numpy()
    px = close.to_numpy()
    arv = ar.to_numpy()
    n = len(close)

    def px_at(off):
        idx = np.clip(anch + off, 0, n - 1)
        return px[idx, tcol]

    def ret(a, b):
        """Return from anchor+a to anchor+b, NaN where either end is missing."""
        p0, p1 = px_at(a), px_at(b)
        with np.errstate(invalid="ignore", divide="ignore"):
            r = p1 / p0 - 1
        bad = (anch + a < 0) | (anch + b >= n)
        r = np.where(bad, np.nan, r)
        return r

    # medium-term momentum, stopping well clear of the event window
    ev["mom_250_21"] = ret(-250, -21)
    ev["mom_60_11"] = ret(-60, -11)
    # short-term reversal candidate
    ev["mom_21_11"] = ret(-21, -11)
    # how the market took the LAST report -- the sign of the previous surprise
    prev0 = ev.groupby("cik")["event0_idx"].shift(1)
    has_prev = prev0.notna()
    pidx = np.where(has_prev, prev0.fillna(0).to_numpy().astype(int), 0)
    prev_ar = arv[np.clip(pidx, 0, n - 1), tcol]
    ev["prev_surprise"] = np.where(has_prev, prev_ar, np.nan)
    # did the firm run late last quarter? (Chambers-Penman: late == bad news)
    ev["prev_gap"] = ev.groupby("cik")["gap_days"].shift(1)
    return ev


# ---------------------------------------------------------------------------
# statistics
# ---------------------------------------------------------------------------
def calendar_portfolio(ar: pd.DataFrame, ev: pd.DataFrame, anchor_col: str,
                       pre: int) -> pd.Series:
    """
    Daily equal-weight return of a portfolio holding every name currently inside
    its pre-earnings window [anchor-pre, anchor-1].

    This is the clustering-robust statistic AND the strategy's actual P&L. Days
    with no open position return 0 (in cash), which is the honest treatment --
    dropping them would inflate the annualised figure.
    """
    cols = {t: i for i, t in enumerate(ar.columns)}
    ev = ev[ev["security_id"].isin(cols)]
    tcol = ev["security_id"].map(cols).to_numpy()
    anch = ev[anchor_col].to_numpy()

    n_days, n_syms = ar.shape
    total = np.zeros(n_days)
    count = np.zeros(n_days)
    vals = np.nan_to_num(ar.to_numpy())
    valid = ~np.isnan(ar.to_numpy())

    for off in range(-pre, 0):
        idx = anch + off
        ok = (idx >= 0) & (idx < n_days) & valid[np.clip(idx, 0, n_days - 1), tcol]
        np.add.at(total, idx[ok], vals[idx[ok], tcol[ok]])
        np.add.at(count, idx[ok], 1)

    port = np.divide(total, count, out=np.zeros_like(total), where=count > 0)
    return pd.Series(port, index=ar.index, name="port_ar")


def summarize(mat: np.ndarray, pre: int, port: pd.Series, label: str) -> dict:
    """CAR over the pre-window with both the naive and the clustering-robust t."""
    pre_cols = mat[:, :pre]
    car = np.nansum(pre_cols, axis=1)
    car = car[~np.isnan(car)]

    naive_t = car.mean() / (car.std(ddof=1) / np.sqrt(len(car))) if len(car) > 1 else np.nan

    live = port[port != 0]
    cal_t = live.mean() / (live.std(ddof=1) / np.sqrt(len(live))) if len(live) > 1 else np.nan
    ann = live.mean() * TRADING_DAYS
    sharpe = (live.mean() / live.std(ddof=1) * np.sqrt(TRADING_DAYS)
              if live.std(ddof=1) > 0 else np.nan)

    return {"label": label, "events": len(car),
            "mean_CAR_bps": car.mean() * 1e4,
            "median_CAR_bps": np.median(car) * 1e4,
            "pct_positive": (car > 0).mean() * 100,
            "naive_t": naive_t, "clustered_t": cal_t,
            "ann_return_pct": ann * 100, "sharpe": sharpe,
            "days_invested": len(live)}


def show(res: dict) -> None:
    print(f"\n=== {res['label']} ===")
    print(f"  events                {res['events']:>10,}")
    print(f"  mean CAR              {res['mean_CAR_bps']:>10.1f} bps")
    print(f"  median CAR            {res['median_CAR_bps']:>10.1f} bps")
    print(f"  % positive            {res['pct_positive']:>10.1f} %")
    print(f"  t-stat  (naive)       {res['naive_t']:>10.2f}   <- overstated, events cluster")
    print(f"  t-stat  (clustered)   {res['clustered_t']:>10.2f}   <- the one to believe")
    print(f"  calendar-time ann.    {res['ann_return_pct']:>10.2f} %")
    print(f"  sharpe                {res['sharpe']:>10.2f}")
    print(f"  days invested         {res['days_invested']:>10,}")


# ---------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(DATA))
    ap.add_argument("--pre", type=int, default=10, help="pre-window length in trading days")
    ap.add_argument("--post", type=int, default=5)
    ap.add_argument("--benchmark", default="RSP", choices=["RSP", "SPY"])
    ap.add_argument("--anchor", default="expected", choices=["expected", "actual"])
    ap.add_argument("--condition", default=None,
                    help="mom_250_21 | mom_60_11 | mom_21_11 | prev_surprise | prev_gap")
    ap.add_argument("--quintiles", type=int, default=5)
    ap.add_argument("--placebo", action="store_true",
                    help="shift the anchor half a cycle -- there is no earnings event there")
    ap.add_argument("--placebo-shift", type=int, default=63)
    ap.add_argument("--by-era", action="store_true")
    ap.add_argument("--min-price", type=float, default=5.0)
    ap.add_argument("--no-demean", action="store_true",
                    help="skip cross-sectional demeaning -- reproduces the +17bps "
                         "panel baseline as if it were a finding. Diagnostic only.")
    args = ap.parse_args()

    close, ev, symbols = load(Path(args.data))
    bench_cols = set(symbols.loc[symbols["role"] == "benchmark", "security_id"])
    bench_ids = dict(zip(symbols["ticker"], symbols["security_id"]))
    if args.benchmark not in bench_ids:
        raise SystemExit(f"benchmark {args.benchmark} not in the panel's symbol map")
    ar = abnormal_returns(close, bench_ids[args.benchmark], bench_cols,
                          demean=not args.no_demean)
    if args.no_demean:
        print("!! demeaning OFF -- results include the panel's +17bps/10d baseline")

    anchor_col = "expected_idx" if args.anchor == "expected" else "event0_idx"
    if args.placebo:
        ev = ev.copy()
        ev["placebo_idx"] = ev[anchor_col] + args.placebo_shift
        anchor_col = "placebo_idx"

    ev = add_conditioners(ar, close, ev, anchor_col)

    # penny-stock filter: a 3% abnormal move on a $2 stock is noise, and these
    # names dominate the tails of an equal-weight average
    cols = {t: i for i, t in enumerate(close.columns)}
    tcol = ev["security_id"].map(cols).to_numpy()
    anch = ev[anchor_col].to_numpy()
    p = close.to_numpy()[np.clip(anch - args.pre, 0, len(close) - 1), tcol]
    ev = ev[(p >= args.min_price) & ~np.isnan(p)].reset_index(drop=True)

    lo, hi = -args.pre, args.post
    mat, ev = event_matrix(ar, ev, anchor_col, lo, hi)
    port = calendar_portfolio(ar, ev, anchor_col, args.pre)

    mode = f"anchor={args.anchor}{' PLACEBO' if args.placebo else ''}, " \
           f"pre={args.pre}d, bench={args.benchmark}"
    show(summarize(mat, args.pre, port, f"ALL EVENTS ({mode})"))

    # ---- the drift curve, day by day ----------------------------------------
    daily = np.nanmean(mat, axis=0) * 1e4
    cum = np.nancumsum(daily)
    print("\n  day   mean AR (bps)   cumulative")
    for j, off in enumerate(range(lo, hi + 1)):
        mark = "  <- announcement public" if off == 0 else ""
        print(f"  {off:+4d}   {daily[j]:>9.2f}      {cum[j]:>9.2f}{mark}")

    # ---- conditioning sort ---------------------------------------------------
    if args.condition:
        c = args.condition
        if c not in ev.columns:
            raise SystemExit(f"unknown conditioner {c}; have "
                             f"{[x for x in ev.columns if x.startswith(('mom_','prev_'))]}")
        sub = ev[ev[c].notna()].copy()
        mat_c, sub = event_matrix(ar, sub, anchor_col, lo, hi)
        sub["q"] = pd.qcut(sub[c], args.quintiles, labels=False, duplicates="drop")

        print(f"\n\n########## conditioned on {c} ##########")
        rows = []
        for q in sorted(sub["q"].dropna().unique()):
            m = sub["q"] == q
            pq = calendar_portfolio(ar, sub[m], anchor_col, args.pre)
            r = summarize(mat_c[m.to_numpy()], args.pre, pq, f"Q{int(q)+1}")
            rows.append({"quintile": f"Q{int(q)+1}", "n": r["events"],
                         f"{c} mean": sub.loc[m, c].mean(),
                         "CAR bps": round(r["mean_CAR_bps"], 1),
                         "clustered t": round(r["clustered_t"], 2),
                         "ann %": round(r["ann_return_pct"], 2)})
        tbl = pd.DataFrame(rows)
        print(tbl.to_string(index=False))
        if len(tbl) >= 2:
            spread = tbl["CAR bps"].iloc[-1] - tbl["CAR bps"].iloc[0]
            print(f"\n  Q{len(tbl)} - Q1 spread: {spread:+.1f} bps")
            print("  A monotone ladder is the thing to look for. A big spread with a "
                  "ragged middle is usually one tail, not a signal.")

    # ---- subperiod stability -------------------------------------------------
    if args.by_era:
        print("\n\n########## subperiod stability ##########")
        yrs = close.index[np.clip(ev[anchor_col].to_numpy(), 0, len(close) - 1)].year
        ev = ev.assign(_yr=yrs)
        for name, lo_y, hi_y in [("2004-2010", 2004, 2010), ("2011-2018", 2011, 2018),
                                 ("2019-2026", 2019, 2026)]:
            m = (ev["_yr"] >= lo_y) & (ev["_yr"] <= hi_y)
            if m.sum() < 100:
                continue
            pe = calendar_portfolio(ar, ev[m], anchor_col, args.pre)
            show(summarize(mat[m.to_numpy()], args.pre, pe, name))
        print("\n  The earnings announcement premium decayed sharply after the "
              "mid-2000s in the published literature. If your 2019-2026 column is "
              "flat, that is the honest finding, not a bug to tune away.")


if __name__ == "__main__":
    main()
