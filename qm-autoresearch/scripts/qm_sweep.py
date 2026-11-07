"""
qm_sweep.py — parallel, resumable driver for the QM parameter sweep.

The stock harness (`qm_autoresearch.py`) runs experiments sequentially, each as a
fresh subprocess that reloads the panel. On the full 2004-2026 window that is
~4 minutes per experiment and ~2 hours for a 25-experiment sweep, which does not
survive a bounded execution window — the run dies and every completed experiment
dies with it.

This driver fixes both problems:
  * results are appended to disk AFTER EACH experiment, so a kill costs at most
    one experiment and `--resume` picks up where it stopped
  * experiments run across a process pool instead of one at a time

The experiment list comes from `qm_autoresearch.generate_experiments`, so this
searches exactly the same space; only the execution changes.

    python qm_sweep.py --n 25 --strategy neighborhood --workers 6
    python qm_sweep.py --n 25 --strategy neighborhood --workers 6 --resume
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

RESULTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sweep_results.json")

_PANEL = {}


def _load_once():
    """Panel/membership/sectors/benchmark, loaded once per worker process."""
    if not _PANEL:
        import qm_pg_data as pgd
        _PANEL["prices"] = pgd.load_panel()
        _PANEL["membership"] = pgd.load_membership()
        _PANEL["sectors"] = pgd.load_sectors()
        _PANEL["bench"] = pgd.load_benchmark()
    return _PANEL


def run_one(job):
    """Run a single experiment. Returns the full result dict."""
    name, params, start_year = job
    t0 = time.time()
    try:
        import qm_strategy as qs
        d = _load_once()
        r = qs.backtest(d["prices"], d["sectors"], params,
                        start_year=start_year, membership=d["membership"],
                        benchmark=d["bench"])
        r["experiment"] = name
        r["elapsed_seconds"] = round(time.time() - t0, 1)
        r["status"] = "ok"
        return r
    except Exception as e:
        return {"experiment": name, "status": f"error: {e}", "params": params,
                "composite_metric": -999, "sharpe_ratio": -999,
                "elapsed_seconds": round(time.time() - t0, 1)}


def load_done():
    if os.path.exists(RESULTS):
        try:
            return json.load(open(RESULTS))
        except Exception:
            return []
    return []


def save(results):
    tmp = RESULTS + ".tmp"
    with open(tmp, "w") as f:
        json.dump(results, f, indent=2, default=str)
    os.replace(tmp, RESULTS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=25)
    ap.add_argument("--strategy", default="neighborhood",
                    choices=["neighborhood", "fip_focus", "smart_random", "grid_sample"])
    ap.add_argument("--start-year", type=int, default=2004)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    from qm_autoresearch import generate_experiments
    exps = generate_experiments(args.n, args.strategy)

    results = load_done() if args.resume else []
    done = {r["experiment"] for r in results}

    jobs = []
    for e in exps:
        name = e.get("label") or e.get("name") or f"exp{e.get('id')}"
        params = e.get("params", e)
        if name in done:
            continue
        jobs.append((name, params, args.start_year))

    print(f"{len(exps)} experiments, {len(done)} already done, {len(jobs)} to run "
          f"on {args.workers} workers", flush=True)

    if not jobs:
        print("nothing to do", flush=True)
        return

    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futs = {pool.submit(run_one, j): j[0] for j in jobs}
        for fut in as_completed(futs):
            r = fut.result()
            results.append(r)
            save(results)                      # checkpoint after EVERY experiment
            print(f"  [{len(results)}/{len(exps)}] {r['experiment']:<34} "
                  f"composite={r.get('composite_metric')} "
                  f"cagr={r.get('annual_return')} "
                  f"exVsEW={r.get('excess_vs_ew')} "
                  f"({r.get('elapsed_seconds')}s)", flush=True)

    ok = [r for r in results if r.get("status") == "ok"]
    ok.sort(key=lambda r: r.get("composite_metric", -999), reverse=True)
    print(f"\nwrote {RESULTS}")
    print("\nTop 8 by composite:")
    for r in ok[:8]:
        print(f"  {r['composite_metric']:>7.4f}  cagr {r.get('annual_return'):>6.2f}  "
              f"exVsEW {str(r.get('excess_vs_ew')):>6}  "
              f"t {str(r.get('t_excess_vs_ew')):>6}  {r['experiment']}")


if __name__ == "__main__":
    main()
