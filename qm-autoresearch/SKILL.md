---
name: qm-autoresearch
description: |
  Karpathy-style autoresearch optimizer for Quantitative Momentum strategies.
  Use this skill whenever the user wants to optimize QM parameters, find the best
  FIP quality weight, test whether momentum quality actually predicts outperformance,
  or run hybrid experiments where the agent modifies the strategy code directly.
  Trigger for: "optimize QM", "does FIP quality help?", "best QM parameters",
  "autoresearch on quantitative momentum", "tune the quality filter", "what FIP
  weight works best?", "hybrid autoresearch", or "let the agent modify the strategy".
  This skill differs from momentum-autoresearch (which optimizes basic momentum) by
  adding QM-specific parameters (FIP weight, FIP lookback, quality premium metric)
  and a multi-objective composite metric that penalizes strategies where FIP quality
  doesn't predict outperformance.
---

# QM Autoresearch — Karpathy-Style Quantitative Momentum Optimizer

## What this skill does

Applies Andrej Karpathy's **autoresearch** pattern to Quantitative Momentum optimization.

**Core loop**: modify parameters → backtest → measure composite metric → keep or discard → repeat.

**Composite metric**: Sharpe ratio with quality penalty.
- `composite = sharpe - 0.5 * |quality_premium|` if quality premium < 0
- Quality premium = forward return of high-FIP stocks minus low-FIP stocks
- This ensures the FIP quality dimension actually "works" — if it doesn't predict
  outperformance, the strategy gets penalized

**Two modes** (the hybrid approach):
1. **Parameter search**: Predefined grid of QM-specific parameters (FIP weight,
   FIP lookback, pct-positive weighting, lookback-skip combos, etc.)
2. **Agent modification**: The agent reads `program.md`, modifies `qm_strategy.py`
   directly (new quality metrics, regime awareness, volatility-adjusted momentum),
   then runs the harness to measure

## Architecture (three files — mirrors Karpathy)

| File | Karpathy Equivalent | Role |
|------|---------------------|------|
| `scripts/qm_strategy.py` | `train.py` | The strategy being optimized — agent modifies this |
| `scripts/qm_autoresearch.py` | `autoresearch.py` | The experiment harness — never modified |
| `scripts/program.md` | `program.md` | Human-editable constraints and search directives |

## How to run

### Step 1: Install dependencies

```bash
pip install yfinance pandas numpy lxml scipy --break-system-packages -q
```

### Step 2: Decide what the user wants

**"Optimize QM parameters" / "What FIP weight works best?"**
→ Run parameter search (Step 3a)

**"Does FIP quality actually help?" / "Compare pure momentum vs QM"**
→ Run fip_focus search (Step 3a with --strategy fip_focus)

**"Try new quality metrics" / "Modify the strategy" / "Hybrid mode"**
→ Agent modifies qm_strategy.py, then runs the harness (Step 3b)

**"Full optimization"**
→ Run parameter search first, then agent modifications (Step 3a then 3b)

### Step 3a: Run parameter search

```bash
python <skill_dir>/scripts/qm_autoresearch.py \
  --n <num_experiments> \
  --strategy <search_strategy> \
  --start-year <year> \
  --output-dir <output_dir>
```

Arguments:
- `--n`: Number of experiments (default 30). Use 15-20 for quick, 40-50 for thorough.
- `--strategy`: How to explore:
  - `neighborhood` — One param at a time. Start here for sensitivity analysis.
  - `fip_focus` — Focus on FIP-specific params. Best for "does quality help?"
  - `smart_random` — Mutate 1-3 params. Good for finding multi-param combos.
  - `grid_sample` — Random from full grid. Most exploratory.
- `--start-year`: Backtest start (default 2015). Use 2006 for 20 years.
- `--time-budget`: Max seconds per experiment (default 300).

**Recommended first runs**:
```bash
# Sensitivity analysis: which individual params matter most?
python <skill_dir>/scripts/qm_autoresearch.py --n 25 --strategy neighborhood --start-year 2015 --output-dir <output_dir>

# FIP deep dive: does quality actually predict outperformance?
python <skill_dir>/scripts/qm_autoresearch.py --n 20 --strategy fip_focus --start-year 2015 --output-dir <output_dir>
```

### Step 3b: Hybrid mode (agent modifies strategy)

1. Read `<skill_dir>/scripts/program.md` for constraints and modification priorities
2. Modify `<skill_dir>/scripts/qm_strategy.py` — change quality metrics, ranking logic, etc.
3. Run: `python <skill_dir>/scripts/qm_strategy.py --backtest --start-year 2015`
4. Check the composite metric: `METRIC:composite_metric=X.XXXX`
5. If improved, keep the change. If not, revert and try next modification.
6. Repeat until diminishing returns or stopping criteria met.

### Step 4: Present results

After autoresearch completes:

1. **Top 10 strategies** — ranked by composite metric, showing Sharpe, quality premium, returns
2. **Quality filter analysis** — what fraction of experiments had positive quality premium?
   Does FIP weight correlate with better composites?
3. **Baseline comparison** — Gray's default QM (6-1, 50% FIP) vs best found
4. **FIP weight analysis** — how does the composite metric vary with FIP weight?
5. **Overfitting warning** — always include, especially if best >> baseline
6. **Hybrid mode suggestions** — what code modifications to try next

### Step 5: Offer follow-ups

- "Run with different time period to check robustness"
- "Focus search on FIP parameters to understand quality better"
- "Try hybrid mode — let me modify the quality metrics"
- "Run the winning strategy as a live screener"
- "Compare QM results against basic momentum autoresearch"

## QM-Specific Parameter Reference

| Parameter | What it controls | Values | Default |
|-----------|-----------------|--------|---------|
| `lookback_months` | Momentum lookback | 3, 6, 9, 12 | 6 |
| `skip_months` | Reversal skip | 0, 1, 2 | 1 |
| `fip_lookback_days` | FIP quality lookback (trading days) | 63, 126, 189, 252 | 126 |
| `fip_weight` | FIP weight in composite rank | 0.0–1.0 | 0.50 |
| `fip_pct_positive_weight` | Pct-positive vs R² balance in FIP | 0.0–1.0 | 0.50 |
| `n_holdings` | Portfolio size | 10, 20, 30, 50 | 50 |
| `weighting` | Position sizing | equal, momentum, qm_composite | equal |
| `rebalance_freq` | Rebalance frequency | monthly, quarterly | quarterly |
| `sector_cap` | Max sector allocation | 0%, 30%, 40%, 50% | 40% |
| `min_qm_percentile` | Minimum QM percentile | 70, 80, 85, 90, 95 | 80 |
| `exclude_negative_1m` | Drop negative 1M stocks | true, false | false |
| `stop_loss_pct` | Stop loss threshold | 0%, 15%, 20% | 0% |

## Investor context

Same as quantitative-momentum skill:
- Strategy: long S&P index + concentrated top stocks overlay
- Goal: beat S&P 500 by informed stock selection
- Follows macro closely
- Manages 401K (self + spouse) and brokerage

## Handling errors

- **Download failures**: yfinance rate limits — scripts handle gracefully
- **Short history**: If start-year too early, fewer months than expected
- **All -999 composites**: Backtest failing — check stderr for errors
- **Negative quality premium everywhere**: FIP may not help for this lookback/market regime
  — report this finding, it's valuable information
