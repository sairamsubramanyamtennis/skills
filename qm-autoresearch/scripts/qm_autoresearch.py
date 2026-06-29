"""
qm_autoresearch.py — Karpathy-style autoresearch harness for Quantitative Momentum.

Architecture (mirrors Karpathy's autoresearch):
    program.md        →  Human-editable constraints, search priorities, stopping criteria
    qm_strategy.py    →  The strategy being optimized (the ONLY file modified)
    qm_autoresearch.py →  THIS FILE: the experiment harness (NEVER modified by agent)

Two modes:
    1. PARAMETER SEARCH — Predefined param grid, swap values, measure, keep/discard
    2. HYBRID / AGENT MODE — The agent reads program.md, modifies qm_strategy.py
       (architecture, filters, ranking logic), runs this harness, measures composite metric

Composite metric: Sharpe ratio with quality penalty
    composite = sharpe - 0.5 * |quality_premium| if quality_premium < 0

This means: optimize for returns, but penalize strategies where FIP quality
doesn't actually predict outperformance (i.e., it's not "working").
"""

import json
import random
import time
import sys
import os
import subprocess
import hashlib
from datetime import datetime
from copy import deepcopy

# Windows consoles default to cp1252 and choke on this harness's Unicode output.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import numpy as np


# ============================================================================
# SEARCH SPACE — All QM-specific parameter variants
# ============================================================================

SEARCH_SPACE = {
    # Lookback & skip
    "lookback_months": [3, 6, 9, 12],
    "skip_months": [0, 1, 2],

    # FIP quality tuning
    "fip_lookback_days": [63, 126, 189, 252],      # ~3, 6, 9, 12 months
    "fip_weight": [0.0, 0.25, 0.50, 0.75, 1.0],   # pure momentum → pure quality
    "fip_pct_positive_weight": [0.0, 0.25, 0.50, 0.75, 1.0],

    # Portfolio construction
    "n_holdings": [10, 20, 30, 50],
    "weighting": ["equal", "momentum", "qm_composite"],

    # Rebalancing
    "rebalance_freq": ["monthly", "quarterly"],

    # Filters
    "sector_cap": [0.0, 0.30, 0.40, 0.50],
    "min_qm_percentile": [70, 80, 85, 90, 95],
    "exclude_negative_1m": [True, False],

    # Risk
    "stop_loss_pct": [0.0, 0.15, 0.20],
}

# Baseline — the starting point (Gray's default QM approach)
BASELINE = {
    "lookback_months": 6,
    "skip_months": 1,
    "fip_lookback_days": 126,
    "fip_weight": 0.50,
    "fip_pct_positive_weight": 0.50,
    "n_holdings": 50,
    "weighting": "equal",
    "rebalance_freq": "quarterly",
    "sector_cap": 0.40,
    "min_qm_percentile": 80,
    "exclude_negative_1m": False,
    "stop_loss_pct": 0.0,
}


# ============================================================================
# EXPERIMENT GENERATION
# ============================================================================

def generate_experiments(n_experiments=30, strategy="neighborhood"):
    """
    Generate parameter combinations to test.

    Strategies:
        neighborhood — Change one param at a time from baseline (best for sensitivity analysis)
        smart_random — Mutate 1-3 params randomly (good for finding combos)
        grid_sample  — Random sample from full grid (most exploratory)
        fip_focus    — Focus experiments on FIP-specific parameters (quality tuning)
    """
    experiments = [{"id": 0, "params": BASELINE.copy(), "label": "baseline"}]

    if strategy == "neighborhood":
        i = 1
        for key, values in SEARCH_SPACE.items():
            for val in values:
                if val != BASELINE.get(key):
                    params = BASELINE.copy()
                    params[key] = val
                    experiments.append({"id": i, "params": params, "label": f"{key}={val}"})
                    i += 1
                    if i >= n_experiments:
                        break
            if i >= n_experiments:
                break

    elif strategy == "smart_random":
        for i in range(1, n_experiments):
            params = BASELINE.copy()
            n_mut = random.randint(1, 3)
            keys = random.sample(list(SEARCH_SPACE.keys()), n_mut)
            for k in keys:
                params[k] = random.choice(SEARCH_SPACE[k])
            label = "+".join(f"{k}={params[k]}" for k in keys)
            experiments.append({"id": i, "params": params, "label": label})

    elif strategy == "grid_sample":
        for i in range(1, n_experiments):
            params = {k: random.choice(v) for k, v in SEARCH_SPACE.items()}
            label = hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()[:8]
            experiments.append({"id": i, "params": params, "label": label})

    elif strategy == "fip_focus":
        # Focused exploration of FIP-specific parameters
        fip_keys = ["fip_lookback_days", "fip_weight", "fip_pct_positive_weight"]
        i = 1
        # First: each FIP param individually
        for key in fip_keys:
            for val in SEARCH_SPACE[key]:
                if val != BASELINE.get(key):
                    params = BASELINE.copy()
                    params[key] = val
                    experiments.append({"id": i, "params": params, "label": f"{key}={val}"})
                    i += 1
                    if i >= n_experiments:
                        break
            if i >= n_experiments:
                break

        # Then: FIP param combos
        while i < n_experiments:
            params = BASELINE.copy()
            n_mut = random.randint(1, len(fip_keys))
            keys = random.sample(fip_keys, n_mut)
            for k in keys:
                params[k] = random.choice(SEARCH_SPACE[k])
            label = "+".join(f"{k}={params[k]}" for k in keys)
            experiments.append({"id": i, "params": params, "label": label})
            i += 1

    return experiments


# ============================================================================
# EXPERIMENT RUNNER
# ============================================================================

def run_experiment(params, experiment_id, script_path, start_year=2015, time_budget=300):
    """
    Run a single backtest experiment.

    Following Karpathy's pattern: each experiment gets a fixed time budget.
    If it times out, it's discarded.

    Returns dict with metrics and status.
    """
    params_json = json.dumps(params)
    start_time = time.time()

    try:
        result = subprocess.run(
            ["python", script_path, "--backtest",
             "--params-json", params_json,
             "--start-year", str(start_year)],
            capture_output=True, text=True, timeout=time_budget
        )

        elapsed = time.time() - start_time
        stdout = result.stdout
        stderr = result.stderr

        # Parse metrics
        sharpe = None
        quality_premium = None
        composite = None
        full_result = {}

        for line in stdout.split("\n"):
            if line.startswith("METRIC:sharpe_ratio="):
                sharpe = float(line.split("=")[1])
            elif line.startswith("METRIC:quality_premium="):
                quality_premium = float(line.split("=")[1])
            elif line.startswith("METRIC:composite_metric="):
                composite = float(line.split("=")[1])
            elif line.strip().startswith("{"):
                try:
                    json_start = stdout.index("{")
                    full_result = json.loads(stdout[json_start:])
                except Exception:
                    pass

        # Fallback to parsed JSON
        if sharpe is None:
            sharpe = full_result.get("sharpe_ratio", -999)
        if quality_premium is None:
            quality_premium = full_result.get("quality_premium", 0)
        if composite is None:
            composite = full_result.get("composite_metric", sharpe)

        return {
            "experiment_id": experiment_id,
            "sharpe_ratio": sharpe if sharpe is not None else -999,
            "quality_premium": quality_premium if quality_premium is not None else 0,
            "composite_metric": composite if composite is not None else -999,
            "elapsed_seconds": round(elapsed, 1),
            "full_result": full_result,
            "status": "success" if sharpe is not None and sharpe > -999 else "parse_error",
            "stderr_snippet": stderr[:500] if stderr else "",
        }

    except subprocess.TimeoutExpired:
        return {
            "experiment_id": experiment_id,
            "sharpe_ratio": -999,
            "quality_premium": 0,
            "composite_metric": -999,
            "elapsed_seconds": time_budget,
            "full_result": {},
            "status": "timeout",
        }
    except Exception as e:
        return {
            "experiment_id": experiment_id,
            "sharpe_ratio": -999,
            "quality_premium": 0,
            "composite_metric": -999,
            "elapsed_seconds": time.time() - start_time,
            "full_result": {},
            "status": f"error: {str(e)}",
        }


# ============================================================================
# AUTORESEARCH MAIN LOOP
# ============================================================================

def run_autoresearch(n_experiments=30, strategy="neighborhood",
                     output_dir=".", start_year=2015, time_budget=300):
    """
    The Karpathy autoresearch loop for Quantitative Momentum:
      1. Generate experiments (parameter variants)
      2. Run each: modify params → backtest → measure composite metric
      3. Keep track of best result
      4. Produce ranked report with quality analysis

    Composite metric: sharpe - penalty if FIP quality doesn't work.
    """
    print("=" * 70)
    print("  QM AUTORESEARCH: Quantitative Momentum Optimizer")
    print("  Pattern: Karpathy autoresearch (modify → run → measure → keep/discard)")
    print(f"  Strategy: {strategy} | Experiments: {n_experiments} | Start: {start_year}")
    print(f"  Metric: Sharpe with quality filter (penalize if FIP doesn't predict)")
    print(f"  Time budget per experiment: {time_budget}s")
    print("=" * 70)

    experiments = generate_experiments(n_experiments, strategy)
    print(f"\nGenerated {len(experiments)} experiments.\n")

    results = []
    best_composite = -999
    best_experiment = None

    script_path = os.path.join(os.path.dirname(__file__), "qm_strategy.py")

    for exp in experiments:
        eid = exp["id"]
        label = exp["label"]
        params = exp["params"]

        print(f"[Exp {eid + 1}/{len(experiments)}] {label}")
        print(f"  lookback={params['lookback_months']}m skip={params['skip_months']}m "
              f"fip_w={params['fip_weight']} fip_days={params['fip_lookback_days']} "
              f"n={params['n_holdings']} wt={params['weighting']} "
              f"freq={params['rebalance_freq']}")

        result = run_experiment(params, eid, script_path,
                                start_year=start_year, time_budget=time_budget)
        result["label"] = label
        result["params"] = params
        results.append(result)

        comp = result["composite_metric"]
        sharpe = result["sharpe_ratio"]
        qp = result["quality_premium"]

        if comp > best_composite:
            improvement = comp - best_composite if best_composite > -999 else 0
            print(f"  → Composite: {comp:.4f} (Sharpe={sharpe:.4f}, QP={qp:.4f})"
                  f"  *** NEW BEST *** (+{improvement:.4f})")
            best_composite = comp
            best_experiment = result
        else:
            print(f"  → Composite: {comp:.4f} (Sharpe={sharpe:.4f}, QP={qp:.4f})"
                  f"  — DISCARDED (best={best_composite:.4f})")
        print()

    # ================================================================
    # FINAL REPORT
    # ================================================================
    print("\n" + "=" * 70)
    print("  QM AUTORESEARCH COMPLETE — RESULTS")
    print("=" * 70)

    results.sort(key=lambda x: x["composite_metric"], reverse=True)

    # Top 10
    header = f"{'Rank':<5} {'Composite':<11} {'Sharpe':<9} {'QualPrem':<10} {'AnnRet%':<10} {'MaxDD%':<9} {'Excess%':<10} {'Label'}"
    print(f"\n{header}")
    print("-" * 90)
    for i, r in enumerate(results[:10]):
        fr = r.get("full_result", {})
        print(f"{i+1:<5} {r['composite_metric']:<11.4f} {r['sharpe_ratio']:<9.4f} "
              f"{r['quality_premium']:<10.4f} "
              f"{fr.get('annual_return', 'N/A')!s:<10} "
              f"{fr.get('max_drawdown', 'N/A')!s:<9} "
              f"{fr.get('excess_return', 'N/A')!s:<10} "
              f"{r['label'][:35]}")

    # Best strategy
    if best_experiment:
        print(f"\n{'=' * 70}")
        print("  BEST STRATEGY:")
        print(f"{'=' * 70}")
        fr = best_experiment.get("full_result", {})
        print(json.dumps({
            "composite_metric": best_experiment["composite_metric"],
            "sharpe_ratio": best_experiment["sharpe_ratio"],
            "quality_premium": best_experiment["quality_premium"],
            "annual_return": fr.get("annual_return"),
            "annual_vol": fr.get("annual_vol"),
            "max_drawdown": fr.get("max_drawdown"),
            "excess_return": fr.get("excess_return"),
            "total_return": fr.get("total_return"),
            "n_years": fr.get("n_years"),
            "params": best_experiment["params"],
        }, indent=2))

    # Baseline comparison
    baseline = next((r for r in results if r["label"] == "baseline"), None)
    if baseline:
        print(f"\n  BASELINE (Gray's default QM — 6-1 mom, 50% FIP weight):")
        bfr = baseline.get("full_result", {})
        print(f"  Composite: {baseline['composite_metric']:.4f}, "
              f"Sharpe: {baseline['sharpe_ratio']:.4f}, "
              f"QP: {baseline['quality_premium']:.4f}, "
              f"AnnRet: {bfr.get('annual_return', 'N/A')}%")

        if best_experiment and baseline["composite_metric"] > -999:
            improvement = best_experiment["composite_metric"] - baseline["composite_metric"]
            print(f"\n  Improvement over baseline: +{improvement:.4f} composite points")

    # Quality analysis
    print(f"\n{'=' * 70}")
    print("  QUALITY FILTER ANALYSIS")
    print(f"{'=' * 70}")
    pos_qp = [r for r in results if r["quality_premium"] > 0 and r["status"] == "success"]
    neg_qp = [r for r in results if r["quality_premium"] <= 0 and r["status"] == "success"]
    print(f"  Experiments where FIP quality predicted outperformance: {len(pos_qp)}/{len(pos_qp)+len(neg_qp)}")
    if pos_qp:
        avg_pos = np.mean([r["quality_premium"] for r in pos_qp])
        print(f"  Avg quality premium (when positive): +{avg_pos:.4f}%")
    if neg_qp:
        avg_neg = np.mean([r["quality_premium"] for r in neg_qp])
        print(f"  Avg quality premium (when negative): {avg_neg:.4f}%")

    # FIP weight analysis: does more FIP weight help?
    fip_analysis = {}
    for r in results:
        fw = r["params"].get("fip_weight", 0.5)
        if fw not in fip_analysis:
            fip_analysis[fw] = []
        if r["composite_metric"] > -999:
            fip_analysis[fw].append(r["composite_metric"])

    if len(fip_analysis) > 1:
        print(f"\n  Composite metric by FIP weight:")
        for fw in sorted(fip_analysis.keys()):
            vals = fip_analysis[fw]
            if vals:
                print(f"    FIP weight {fw:.2f}: avg composite = {np.mean(vals):.4f} (n={len(vals)})")

    # Save results
    output_file = os.path.join(output_dir, "qm_autoresearch_results.json")
    with open(output_file, "w") as f:
        json.dump({
            "run_timestamp": datetime.now().isoformat(),
            "n_experiments": len(results),
            "strategy": strategy,
            "start_year": start_year,
            "best_composite": best_composite,
            "best_params": best_experiment["params"] if best_experiment else None,
            "all_results": [{
                "rank": i + 1,
                "experiment_id": r["experiment_id"],
                "label": r["label"],
                "composite_metric": r["composite_metric"],
                "sharpe_ratio": r["sharpe_ratio"],
                "quality_premium": r["quality_premium"],
                "params": r["params"],
                "full_result": r.get("full_result", {}),
                "status": r["status"],
                "elapsed_seconds": r.get("elapsed_seconds"),
            } for i, r in enumerate(results)],
        }, f, indent=2, default=str)

    print(f"\nFull results saved to: {output_file}")

    # OVERFITTING WARNING
    print(f"\n{'=' * 70}")
    print("  OVERFITTING WARNING")
    print(f"{'=' * 70}")
    print(f"  Ran {len(results)} experiments on the same historical data.")
    print(f"  The best composite ({best_composite:.4f}) may be inflated by data snooping.")
    print(f"  The quality filter helps somewhat (penalizes strategies where FIP doesn't")
    print(f"  predict outperformance), but it's not a substitute for out-of-sample testing.")
    print(f"  ALWAYS validate with walk-forward or out-of-sample data before trading.")
    print(f"{'=' * 70}")

    # HYBRID MODE SUGGESTIONS
    print(f"\n{'=' * 70}")
    print("  HYBRID MODE — AGENT MODIFICATION SUGGESTIONS")
    print(f"{'=' * 70}")
    print("  The parameter search above covers the predefined grid.")
    print("  For hybrid mode, the agent can also try modifying qm_strategy.py directly:")
    print("  - Alternative FIP formulas (e.g., information ratio, Hurst exponent)")
    print("  - Different composite ranking methods (e.g., geometric mean of ranks)")
    print("  - Regime-aware filters (e.g., use more FIP weight in high-vol markets)")
    print("  - Momentum decay factors (weight recent months more than older months)")
    print("  - Volatility-adjusted momentum (divide returns by realized vol)")
    print("  Run this harness after each modification to measure the composite metric.")
    print(f"{'=' * 70}")

    return results, best_experiment


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="QM Autoresearch — Karpathy-style optimizer")
    parser.add_argument("--n", type=int, default=30, help="Number of experiments")
    parser.add_argument("--strategy",
                        choices=["neighborhood", "smart_random", "grid_sample", "fip_focus"],
                        default="neighborhood",
                        help="Search strategy")
    parser.add_argument("--output-dir", type=str, default=".")
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--time-budget", type=int, default=300,
                        help="Max seconds per experiment (default: 300)")

    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    results, best = run_autoresearch(
        n_experiments=args.n,
        strategy=args.strategy,
        output_dir=args.output_dir,
        start_year=args.start_year,
        time_budget=args.time_budget,
    )
