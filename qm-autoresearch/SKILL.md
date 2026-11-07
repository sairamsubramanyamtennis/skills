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

## Architecture (four files — mirrors Karpathy)

| File | Karpathy Equivalent | Role |
|------|---------------------|------|
| `scripts/qm_strategy.py` | `train.py` | The strategy being optimized — agent modifies this |
| `scripts/qm_autoresearch.py` | `autoresearch.py` | The experiment harness — never modified |
| `scripts/program.md` | `program.md` | Human-editable constraints and search directives |
| `scripts/qm_pg_data.py` | — | Postgres data layer — the universe, prices and benchmark |
| `scripts/qm_placebo.py` | — | Random-portfolio null distribution — judge results against it |

## Data (migrated to Postgres 2026-08-06 — read this before trusting a number)

Backtests run off the Postgres `trading` DB (localhost:5433), **not** the old Yahoo
parquet. `qm_pg_data.py` supplies:

- `mkt.price_daily` — delisted-inclusive daily bars, **2003-09-10 onward**, keyed on
  `security_id`. That start is Polygon/Massive's own history floor, not a gap in the
  ingest; probing the API for 2001 returns zero rows. With ~8 months of warmup for the
  6-1 momentum and 126-day FIP windows, **the earliest honest backtest year is 2004**.
- `ref.index_membership` — point-in-time S&P 500 membership, applied at every rebalance.
- SPY from the same table, so benchmark and portfolio share one basis.

**Three rules that keep results honest:**

1. **Never key on a ticker string.** 173 tickers denote more than one company across
   time (ABX = Barrick until 2025, then Abacus). The panel is `security_id`-keyed.
2. **Prices are split-adjusted PRICE RETURN, no dividends.** The benchmark comes from
   the same table on the same basis. Mixing in a Yahoo adjusted-close series (total
   return) overstates the benchmark ~2pp/yr — larger than any edge this strategy has
   ever shown.
3. **`--source local` is survivorship-biased.** It is kept only for comparison. That
   Yahoo panel holds 49% of the real point-in-time members in 2000 and 55% in 2003,
   and the missing half is precisely the names later acquired or delisted.

**Known coverage hole:** priced members run 91.5% (2004) → 94% (2010) → 100% (2020).
The unpriced early names are ~15 bankruptcies Polygon never carried (Lehman, WaMu, GM,
Fannie, Freddie, Delphi, Kodak) plus ~31 companies whose membership row carries their
modern ticker while prices sit under the historical one (EA was ERTS until 2011, Schwab
was SCH until 2005, NextEra was FPL until 2010). Quantify with
`python scripts/qm_pg_data.py`, which prints the coverage table.

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
- `--start-year`: Backtest start (default **2004**, the earliest the data supports).
- `--time-budget`: Max seconds per experiment (default 300). The full 2004-2026 window
  is ~267 months; raise this if experiments start timing out.

**Recommended first runs**:
```bash
# Sensitivity analysis: which individual params matter most?
python <skill_dir>/scripts/qm_autoresearch.py --n 25 --strategy neighborhood --start-year 2004 --output-dir <output_dir>

# FIP deep dive: does quality actually predict outperformance?
python <skill_dir>/scripts/qm_autoresearch.py --n 20 --strategy fip_focus --start-year 2004 --output-dir <output_dir>
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

1. **Placebo percentile FIRST** — before any CAGR. Load `placebo_bands.json` (build it
   with `python scripts/qm_placebo.py`) and report where each top config sits in the
   random-portfolio distribution for its `n_holdings`/`rebalance_freq`. Compare net
   against net. A config inside the band did not beat chance, whatever its CAGR.
2. **Top 10 strategies** — by composite metric, showing Sharpe, `benchmark_sharpe`,
   `excess_vs_ew` with its t-stat, turnover and cost drag
3. **Split-sample check on the winners** — re-run the top few on 2004-2015 and 2016-2026
   separately. QM flips sign across that boundary (−2.6pp then +2.2pp vs equal-weight),
   so a full-sample average conceals a regime trade
4. **Quality filter analysis** — fraction of experiments with a quality premium whose
   t-stat clears ±1. At baseline it is 0.71 with a 50% hit rate, i.e. nothing
5. **Baseline comparison** — Gray's default QM (6-1, 50% FIP) vs best found
6. **Overfitting warning** — always include. The search space is 3.4M configurations
   against 267 months; the best of 30 draws is optimistic by construction
7. **Hybrid mode suggestions** — what code modifications to try next

### The benchmark to quote

The strategy is **equal-weighted**, so the primary comparator is `excess_vs_ew` — an
equal-weight portfolio of the same point-in-time universe. Measuring 50 equal-weighted
names against cap-weighted SPY smuggles in a size tilt that has nothing to do with
momentum. Quote SPY second, as the thing the money would otherwise sit in.

Baseline, 2004-2026, net of 10bps/leg: QM **8.21%**, equal-weight universe **8.78%**,
SPY **8.90%**. Excess vs equal-weight **−0.57pp, t = −0.20**. Strategy Sharpe **0.243**
against SPY's **0.332** — the benchmark Sharpe-dominates.

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

---

## Telemetry (standing requirement — all skills)

Log this run **once, at the very end**, whether it went well or not (Bash tool; forward slashes):

```bash
python C:/Users/ssair/.claude/telemetry/telemetry.py log --skill qm-autoresearch \
  --outcome delivered|partial|blocked|corrected|routed \
  --asked    "what he actually wanted, one line" \
  --produced "what he got, one line" \
  [--friction "what slowed it down or went wrong"] [--routed-to <skill>] [--tags a,b]
```

* `corrected` = Sai had to push back before it was right. **Log it.** A telemetry file that is all
  `delivered` is worthless for skill health — the corrections and blocks are the whole point.
* One record per run, not per step. Silent side effect: never announce it, never ask permission for
  it, never let it delay or clutter the answer.
* Paraphrase in `--asked`; never log credentials, birth data, account numbers or verbatim personal
  detail. If the call fails, drop it and move on.

Full contract: `C:/Users/ssair/.claude/telemetry/TELEMETRY.md` · read it back in the Recap app's
Telemetry page or via `telemetry.py stats --days 30`.
