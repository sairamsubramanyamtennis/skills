"""
qm_split_check.py — the test that decides whether a sweep winner is an edge or an artefact.

A config selected as "best" out of N experiments has been chosen ON the full sample,
so its headline number is optimistic by construction. The expected maximum of 25
independent standard-normal draws is about +1.97 sd, which means a winner sitting
two standard deviations above the null is exactly what pure chance produces at this
search width.

The discriminating question is not "how big is it" but "does it hold in both halves".
QM has already been caught failing this once: it runs -2.6pp vs equal-weight over
2004-2013 and +2.2pp over 2014-2026, so its flat full-sample average is a decade of
losing cancelling a decade of winning.

For each config this reports the full sample, both halves, and the concentration of
the portfolio (effective N), since a "winner" that is really a concentrated bet on a
handful of names is a different strategy, not a better parameterization.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

import qm_pg_data as pgd
import qm_strategy as qs

SPLIT = 2015  # first year of the out-of-sample half


def effective_n(prices, membership, sectors, params, start_year=2004):
    """
    Concentration diagnostic: 1/sum(w^2), the number of names the portfolio
    behaves like. Equal-weight 50 gives 50; a momentum-tilted book can be far lower.
    """
    monthly = prices.resample("ME").last()
    daily_returns = prices.pct_change(fill_method=None)
    lookback, skip = params["lookback_months"], params["skip_months"]
    eff = []
    for i in range(lookback + skip + 2, len(monthly)):
        date = monthly.index[i]
        if date.year < start_year:
            continue
        if params["rebalance_freq"] == "quarterly" and date.month not in (3, 6, 9, 12):
            continue
        try:
            mom, ret_1m = qs.calculate_momentum(monthly.iloc[:i], lookback, skip)
            fip = qs.calculate_fip(daily_returns.loc[:monthly.index[i - 1]],
                                   params["fip_lookback_days"],
                                   params["fip_pct_positive_weight"])
            allowed = qs.members_on(membership, date) if membership else None
            w, _ = qs.select_portfolio(mom, fip, ret_1m, sectors, params, allowed=allowed)
            if len(w):
                eff.append(1.0 / float((w ** 2).sum()))
        except Exception:
            pass
    return float(np.mean(eff)) if eff else float("nan")


_D = {}


def _data():
    if not _D:
        _D["prices"] = pgd.load_panel()
        _D["membership"] = pgd.load_membership()
        _D["sectors"] = pgd.load_sectors()
        _D["bench"] = pgd.load_benchmark()
    return _D


def _job(spec):
    """(experiment, kind, params, start_year, end_year) -> row dict"""
    name, kind, params, sy, ey = spec
    d = _data()
    if kind == "effn":
        return {"name": name, "kind": kind,
                "effn": effective_n(d["prices"], d["membership"], d["sectors"], params)}
    px = d["prices"] if ey is None else d["prices"][d["prices"].index.year < ey]
    bn = d["bench"] if ey is None else d["bench"][d["bench"].index.year < ey]
    r = qs.backtest(px, d["sectors"], params, start_year=sy,
                    membership=d["membership"], benchmark=bn)
    return {"name": name, "kind": kind, "cagr": r.get("annual_return"),
            "ew": r.get("ew_universe_annual"), "ex": r.get("excess_vs_ew"),
            "t": r.get("t_excess_vs_ew"), "sharpe": r.get("sharpe_ratio"),
            "bsharpe": r.get("benchmark_sharpe"), "months": r.get("n_months")}


def main():
    from concurrent.futures import ProcessPoolExecutor

    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--workers", type=int, default=7)
    ap.add_argument("--results", default="sweep_results.json")
    ap.add_argument("--out", default="split_check.json")
    args = ap.parse_args()

    rows = json.load(open(args.results))
    ok = [r for r in rows if r.get("status") == "ok"]
    ok.sort(key=lambda r: r.get("excess_vs_ew") or -99, reverse=True)
    picks = ok[: args.top]

    specs = []
    for r in picks:
        p = r["params"]
        specs.append((r["experiment"], "full 2004-26", p, 2004, None))
        specs.append((r["experiment"], "in  2004-14", p, 2004, SPLIT))
        specs.append((r["experiment"], "out 2015-26", p, SPLIT, None))
        specs.append((r["experiment"], "effn", p, 2004, None))

    print(f"{len(specs)} jobs on {args.workers} workers", file=sys.stderr)
    out = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for res in pool.map(_job, specs):
            out.append(res)
            json.dump(out, open(args.out, "w"), indent=2, default=str)
            print(".", end="", file=sys.stderr, flush=True)
    print(file=sys.stderr)

    effn = {r["name"]: r["effn"] for r in out if r["kind"] == "effn"}
    print(f"\n{'config':<28} {'window':<13} {'CAGR':>7} {'EW':>7} {'exVsEW':>8} "
          f"{'t':>6} {'sharpe':>7} {'bench':>7} {'effN':>6}")
    print("-" * 96)
    for r in picks:
        for kind in ("full 2004-26", "in  2004-14", "out 2015-26"):
            m = next((x for x in out if x["name"] == r["experiment"] and x["kind"] == kind), None)
            if not m:
                continue
            print(f"{r['experiment'][:27]:<28} {kind:<13} {str(m['cagr']):>7} "
                  f"{str(m['ew']):>7} {str(m['ex']):>8} {str(m['t']):>6} "
                  f"{str(m['sharpe']):>7} {str(m['bsharpe']):>7} "
                  f"{effn.get(r['experiment'], float('nan')):>6.1f}")
        print()

    _tail()


def _tail():
    band = None
    bp = "placebo_bands.json"
    if os.path.exists(bp):
        band = json.load(open(bp)).get("50_quarterly_2004")
    if band:
        a = np.array(band["samples"])
        print(f"Placebo (random-50, quarterly, net of costs): "
              f"{a.mean():.2f}% +/- {a.std(ddof=1):.2f}")
        print("NOTE: that band is EQUAL-weighted. A momentum-weighted config is a")
        print("different animal and needs its own null before it can be compared.")
    print("\nA config that wins in one half and loses in the other is a regime trade,")
    print("not an edge. Sign consistency across halves matters more than full-sample size.")


if __name__ == "__main__":
    main()
