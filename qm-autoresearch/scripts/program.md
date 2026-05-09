# QM Autoresearch — Strategy Constraints & Search Directives

## Objective
Find the highest composite metric (Sharpe with quality filter) Quantitative Momentum
strategy on S&P 500 stocks. The quality filter ensures that the FIP dimension
actually predicts outperformance — it must "work" or it gets penalized.

## Composite metric formula
```
composite = sharpe_ratio - quality_penalty
quality_penalty = 0.5 * |quality_premium| if quality_premium < 0, else 0
```

Where quality_premium = avg forward return of high-FIP quintile - low-FIP quintile.

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
