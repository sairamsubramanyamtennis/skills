"""
qm_placebo.py — the band a coin flip achieves, so a result can be judged against it.

A momentum backtest that returns 8.9% a year sounds like it did something. The
question that settles it is: what would picking N names at RANDOM from the same
point-in-time universe, on the same rebalance dates, with the same costs, have
returned? If the strategy sits inside that distribution, the ranking machinery
contributed nothing and the return is the universe's own drift.

This computes that null distribution once per (n_holdings, rebalance_freq) and
caches it. The autoresearch harness reads the cache and reports every experiment
as a PERCENTILE OF RANDOM rather than as a bare CAGR.

Run:  python qm_placebo.py                 # default bands
      python qm_placebo.py --trials 500    # tighter
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

import qm_pg_data as pgd
from qm_strategy import members_on

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "placebo_bands.json")


def placebo_band(prices, membership, n_holdings, rebalance_freq="quarterly",
                 start_year=2004, trials=200, cost_bps_per_leg=10, seed=0):
    """
    Distribution of annualized return for random n_holdings portfolios drawn from
    the point-in-time universe, rebalanced and costed exactly as the strategy is.
    """
    monthly = prices.resample("ME").last()
    monthly_ret = monthly.pct_change(fill_method=None)
    if len(monthly) > 1:
        last_bar = prices.index.max()
        if last_bar < monthly.index[-1] - pd.Timedelta(days=5):
            monthly = monthly.iloc[:-1]
            monthly_ret = monthly_ret.iloc[:-1]

    rebal_months = [3, 6, 9, 12] if rebalance_freq == "quarterly" else list(range(1, 13))
    cost_rate = cost_bps_per_leg / 10000.0
    rng = np.random.default_rng(seed)

    idx = [i for i in range(9, len(monthly)) if monthly.index[i].year >= start_year]
    if not idx:
        return None

    # Precompute the eligible (member AND priced) set for each month once.
    eligible = {}
    for i in idx:
        date = monthly.index[i]
        row = monthly_ret.iloc[i]
        univ = members_on(membership, date) if membership else None
        cand = row.reindex(list(univ)).dropna() if univ else row.dropna()
        eligible[i] = (cand.index.to_numpy(), cand.to_numpy(dtype=float))

    cagrs = []
    for _t in range(trials):
        held = np.array([], dtype=object)
        rets = []
        for i in idx:
            date = monthly.index[i]
            ids, vals = eligible[i]
            if len(ids) < n_holdings:
                continue
            cost = 0.0
            if date.month in rebal_months or len(held) == 0:
                pick = rng.choice(len(ids), size=n_holdings, replace=False)
                new_held = ids[pick]
                # turnover = fraction of the book replaced
                if len(held):
                    kept = len(np.intersect1d(held, new_held))
                    turnover = (n_holdings - kept) / n_holdings
                else:
                    turnover = 1.0
                cost = turnover * 2 * cost_rate
                held = new_held
            pos = pd.Index(ids).get_indexer(pd.Index(held))
            pos = pos[pos >= 0]
            if len(pos) == 0:
                continue
            rets.append(float(vals[pos].mean()) - cost)

        if len(rets) > 12:
            s = pd.Series(rets)
            cagrs.append(((1 + s).prod() ** (12.0 / len(s)) - 1) * 100)

    a = np.array(cagrs)
    return {
        "n_holdings": n_holdings,
        "rebalance_freq": rebalance_freq,
        "start_year": start_year,
        "trials": len(a),
        "cost_bps_per_leg": cost_bps_per_leg,
        "mean": round(float(a.mean()), 3),
        "sd": round(float(a.std(ddof=1)), 3),
        "p5": round(float(np.percentile(a, 5)), 3),
        "p50": round(float(np.percentile(a, 50)), 3),
        "p95": round(float(np.percentile(a, 95)), 3),
        "samples": [round(float(x), 4) for x in a],
    }


def percentile_of(cagr, band):
    """Where a strategy's CAGR sits in the random distribution, 0-100."""
    a = np.array(band["samples"])
    return round(float((a < cagr).mean() * 100), 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=200)
    ap.add_argument("--start-year", type=int, default=2004)
    ap.add_argument("--holdings", type=int, nargs="+", default=[10, 20, 30, 50])
    ap.add_argument("--freqs", nargs="+", default=["quarterly", "monthly"])
    args = ap.parse_args()

    print("Loading panel...", file=sys.stderr)
    prices = pgd.load_panel()
    membership = pgd.load_membership()

    bands = {}
    if os.path.exists(CACHE):
        bands = json.load(open(CACHE))

    for freq in args.freqs:
        for n in args.holdings:
            key = f"{n}_{freq}_{args.start_year}"
            print(f"  placebo n={n} {freq} ({args.trials} trials)...", file=sys.stderr)
            b = placebo_band(prices, membership, n, freq,
                             start_year=args.start_year, trials=args.trials)
            if b:
                bands[key] = b
                print(f"    random-{n} {freq}: {b['mean']:.2f}% +/- {b['sd']:.2f} "
                      f"(p5 {b['p5']:.2f}, p95 {b['p95']:.2f})")

    with open(CACHE, "w") as f:
        json.dump(bands, f, indent=2)
    print(f"\nwrote {CACHE}")
    print("\nA strategy inside this band did not beat chance, whatever its CAGR.")


if __name__ == "__main__":
    main()
