# QM Autoresearch — Strategy Constraints & Search Directives

## Objective
Find the highest composite metric (Sharpe with quality filter) Quantitative Momentum
strategy on S&P 500 stocks. The quality filter ensures that the FIP dimension
actually predicts outperformance — it must "work" or it gets penalized.

## Composite metric formula
```
composite = sharpe_ratio - quality_penalty
quality_penalty = 0.25 * min(|t_qp|, 2.0)   if t_qp < -1.0, else 0
```

Where quality_premium = avg forward return of high-FIP quintile - low-FIP quintile,
and `t_qp` is its t-statistic across rebalances.

**Why the t-stat and not the raw premium (changed 2026-08-06):** the old form was
`sharpe - 0.5*|quality_premium|`. Sharpe here is ~0.25 while the raw premium has a
standard deviation of ~6.2, so one noisy draw could swamp every genuine difference in
risk-adjusted return. Searching 3.4M configurations against that objective optimizes
the sign of noise. The premium's own t-stat at baseline is **0.71 with a 50% hit rate**
— FIP quality does not predict outperformance on this data, so the penalty must not
fire on statistically empty draws.

## Costs are mandatory
Measured one-way turnover is **~278%/yr**; at 10bps/leg that is **0.56pp/yr** of drag,
several times any edge the strategy has shown. `cost_bps_per_leg` defaults to 10 and is
charged on the actual weight delta at each rebalance. Never set it to 0 to make a result
presentable — a zero-cost result is not a result.

## Every claim gets a placebo
Run `python qm_placebo.py` to build the null distribution: random N-name portfolios from
the same point-in-time universe, same dates, same costs. Report every config as a
**percentile of random**, not as a bare CAGR. Compare like with like — a net strategy
return against a net placebo band, never net against gross.

Baseline reference (50 holdings, quarterly, 10bps, 2004-2026): random-50 nets
**7.89% ± 0.83**, and QM nets 8.21% → **60th percentile**. The entire QM apparatus buys
0.39 standard deviations against a coin flip. Anything the search finds must clear this
band before it is described as an edge.

## Constraints (do not violate)
- **Universe**: S&P 500 only (no small caps, no international)
- **Long-only**: No shorting
- **Max positions**: 10–50 stocks
- **Rebalance**: Monthly or quarterly only (no daily/weekly — tax inefficient)
- **Sector cap**: At least some diversification (no single sector > 50%)
- **FIP must be tested**: Every experiment must include some FIP quality component
  (fip_weight >= 0.0 is fine, but the quality premium is always measured)

## Investor context
- Manages 401K + brokerage (long S&P index + concentrated overlay)
- Goal: beat S&P 500 through informed stock selection
- Follows macro closely
- Needs practical, implementable signals (not exotic)
- Already uses basic 6-1 momentum — this adds the quality dimension

## Search priorities (parameter search mode)
1. **First**: How much FIP weight matters (test fip_weight from 0.0 to 1.0)
2. **Then**: What FIP formula works best (pct_positive vs R² weighting)
3. **Then**: FIP lookback period (3, 6, 9, 12 months of daily data)
4. **Then**: Lookback-skip combos (3-1, 6-1, 9-1, 12-1)
5. **Finally**: Portfolio construction (holdings count, weighting, sector caps)

## Agent modification priorities (hybrid mode)
When modifying qm_strategy.py directly, try these in order:
1. Alternative quality metrics: information ratio, Hurst exponent, max consecutive up days
2. Momentum decay: exponentially weight recent months more than older months
3. Volatility-adjusted momentum: divide by realized vol (risk-adjusted momentum)
4. Regime awareness: increase FIP weight when VIX is high (quality matters more in volatile markets)
5. Composite ranking: try geometric mean of ranks instead of arithmetic mean

## Stopping criteria
- If 5 consecutive experiments fail to improve the best composite metric by > 0.01, stop
- If composite metric exceeds 2.0, flag as likely overfit and verify with different time period
- If quality premium is negative for > 80% of experiments, the FIP dimension may not add value
  for the chosen lookback — report this finding

## Overfitting safeguards
- Flag any strategy that dramatically outperforms baseline — it's likely overfit
- Prefer simple, single-parameter changes over complex multi-parameter combos
- Gray's original QM approach has academic backing; deviations need justification
- Always compare against pure momentum (fip_weight=0.0) to verify quality adds value
- **Split-sample every winner before reporting it.** The data now spans 2004-2026 —
  267 months. Any config picked as "best" across 30 experiments has been selected on
  the full sample and its headline number is optimistic by construction. Re-run the
  top few on 2004-2015 and 2016-2026 separately and report both. A config that wins
  in one half and loses in the other is a regime artefact, not an edge. This has
  already happened once here: a +6pp persistence signal measured over 2022-2026
  turned out to be -0.9pp over the full history.
- **Report excess vs SPY, not CAGR.** Prices are price-return, so a raw CAGR looks
  ~2pp low against any total-return figure quoted elsewhere. Excess-vs-SPY on the
  same basis is the only comparable number.
