"""
qm_track.py — research tracking loop for the QM strategy (#1).

Two jobs:
  record  — append today's Top-N (default 10) composite-rank picks to picks_history.csv,
            tagged with the SPY 200-DMA regime at pick time.
  score   — for every recorded snapshot, compute the equal-weight basket's realized
            return-to-date vs SPY over the same window -> picks_scorecard.csv.

Forward returns are computed from a single consistent Polygon adjusted-close series per
ticker (NOT the screener's snapshot price), so ratios are correct regardless of the
screener's absolute-price quirk.

CLI:
  python qm_track.py record --ranking qm_full_ranking.csv --out DIR [--top-n 10]
  python qm_track.py score  --out DIR
"""
import argparse
import csv
import json
import os
import sys
from datetime import datetime

import pandas as pd

from qm_regime import fetch_daily_closes, get_regime

HISTORY_COLS = ["run_date", "rank", "ticker", "company", "sector", "signal",
                "screener_price", "regime", "spy_close", "sma200", "pct_vs_sma"]


def _history_path(out_dir):
    return os.path.join(out_dir, "picks_history.csv")


def _scorecard_path(out_dir):
    return os.path.join(out_dir, "picks_scorecard.csv")


def record_picks(ranking_csv, out_dir, top_n=10, regime=None):
    """Append the Top-N composite-rank picks for today to picks_history.csv (idempotent per day)."""
    df = pd.read_csv(ranking_csv)
    df = df.sort_values("Composite QM Rank").head(top_n)
    run_date = datetime.now().strftime("%Y-%m-%d")

    if regime is None:
        regime = get_regime()

    hist_path = _history_path(out_dir)
    existing_dates = set()
    if os.path.exists(hist_path):
        prev = pd.read_csv(hist_path)
        existing_dates = set(prev["run_date"].astype(str).unique())

    if run_date in existing_dates:
        print(f"picks_history already has {run_date}; skipping re-record.", file=sys.stderr)
        return hist_path, 0

    rows = []
    for _, r in df.iterrows():
        rows.append({
            "run_date": run_date,
            "rank": int(r["Composite QM Rank"]),
            "ticker": r["Ticker"],
            "company": r.get("Company", ""),
            "sector": r.get("Sector", ""),
            "signal": r.get("Signal", ""),
            "screener_price": r.get("Price", ""),
            "regime": regime.get("regime"),
            "spy_close": regime.get("spy_close"),
            "sma200": regime.get("sma200"),
            "pct_vs_sma": regime.get("pct_vs_sma"),
        })

    write_header = not os.path.exists(hist_path)
    with open(hist_path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=HISTORY_COLS)
        if write_header:
            w.writeheader()
        w.writerows(rows)
    print(f"Recorded {len(rows)} picks for {run_date} (regime={regime.get('regime')}) -> {hist_path}")
    return hist_path, len(rows)


def score(out_dir, benchmark="SPY"):
    """Compute each snapshot's equal-weight basket return-to-date vs SPY."""
    hist_path = _history_path(out_dir)
    if not os.path.exists(hist_path):
        print("No picks_history.csv yet — nothing to score.", file=sys.stderr)
        return None

    hist = pd.read_csv(hist_path)
    hist["run_date"] = pd.to_datetime(hist["run_date"])
    earliest = hist["run_date"].min()
    days_span = (datetime.now() - earliest.to_pydatetime()).days + 40

    # Fetch one consistent price series per unique ticker + the benchmark.
    tickers = sorted(hist["ticker"].unique())
    print(f"Fetching prices for {len(tickers)} tickers + {benchmark} "
          f"(span ~{days_span}d)...", file=sys.stderr)
    series = {}
    for t in tickers:
        s = fetch_daily_closes(t, days=days_span)
        if s is not None and len(s):
            series[t] = s.sort_index()
    spy = fetch_daily_closes(benchmark, days=days_span)
    spy = spy.sort_index() if spy is not None else None

    def ret_to_date(s, since):
        """Return from the close on/just before `since` to the latest close."""
        if s is None or not len(s):
            return None
        entry = s.asof(pd.Timestamp(since))
        if pd.isna(entry) or entry == 0:
            return None
        return float(s.iloc[-1] / entry - 1.0) * 100.0

    rows = []
    for run_date, grp in hist.groupby("run_date"):
        picks = list(grp["ticker"])
        pick_rets = [ret_to_date(series.get(t), run_date) for t in picks]
        pick_rets = [x for x in pick_rets if x is not None]
        if not pick_rets:
            continue
        basket = sum(pick_rets) / len(pick_rets)
        spy_ret = ret_to_date(spy, run_date)
        excess = (basket - spy_ret) if spy_ret is not None else None
        rows.append({
            "snapshot_date": run_date.strftime("%Y-%m-%d"),
            "n_picks": len(pick_rets),
            "days_held": (datetime.now() - run_date.to_pydatetime()).days,
            "regime": grp["regime"].iloc[0],
            "basket_return_pct": round(basket, 2),
            "spy_return_pct": round(spy_ret, 2) if spy_ret is not None else None,
            "excess_pct": round(excess, 2) if excess is not None else None,
        })

    if not rows:
        print("No scorable snapshots (price fetch failed?).", file=sys.stderr)
        return None

    out = pd.DataFrame(rows).sort_values("snapshot_date")
    sc_path = _scorecard_path(out_dir)
    out.to_csv(sc_path, index=False)

    # Aggregate headline
    wins = (out["excess_pct"] > 0).sum()
    n = out["excess_pct"].notna().sum()
    avg_excess = out["excess_pct"].mean()
    print(f"\nScored {len(out)} snapshots -> {sc_path}")
    print(f"  Avg excess vs {benchmark}: {avg_excess:+.2f} pp | "
          f"beat {benchmark}: {wins}/{n} snapshots")
    print(out.to_string(index=False))
    return sc_path


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    rp = sub.add_parser("record")
    rp.add_argument("--ranking", required=True)
    rp.add_argument("--out", required=True)
    rp.add_argument("--top-n", type=int, default=10)

    sp = sub.add_parser("score")
    sp.add_argument("--out", required=True)

    args = ap.parse_args()
    if args.cmd == "record":
        record_picks(args.ranking, args.out, top_n=args.top_n)
    elif args.cmd == "score":
        score(args.out)


if __name__ == "__main__":
    main()
