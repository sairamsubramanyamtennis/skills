# Evidence Scorecard — What Works, What Only Looks Like It Works, What Is Folklore

Read this before pronouncing on whether any strategy, factor, indicator, or pattern "works."
Grade every claim. Give the effect size *and* its fragility. Name the failure mode.

## Grading scale

| Grade | Meaning |
|---|---|
| **A — Robust** | Survives out-of-sample, across countries and decades, after realistic costs. Still has bad decades. |
| **B — Real but decayed** | Genuine discovery; effect materially shrank post-publication or post-2000s. Exploitable only with care. |
| **C — Conditional** | Works in specific regimes/universes/implementations. Sign can flip. Not a standalone edge. |
| **D — Unproven** | Plausible mechanism, thin or contested evidence, or untestable at retail scale after costs. |
| **F — Folklore / data-mined** | No credible evidence, or evidence consistent with multiple-testing noise. |

## The universal prior

Most published "edges" are false or dead. Three forces guarantee it:

1. **Multiple testing.** Hundreds of researchers × thousands of specifications. Harvey/Liu/Zhu argue the honest t-stat hurdle for a *new* factor is ≈ 3.0, not 2.0. Most of the ~400 published factors don't clear it.
2. **Post-publication decay.** McLean & Pontiff: anomaly returns fall ~26% out-of-sample (pure statistical bias) and ~58% post-publication (arbitrage). Assume any effect you read about is roughly half its published size.
3. **Costs.** Novy-Marx & Velikov: many anomalies have positive gross alpha and ~zero net alpha after realistic trading costs. High-turnover signals are the worst offenders.

**Default posture: skeptical.** The burden of proof is on the claim, and it is a heavy burden.

---

## A — Robust (still bring caveats)

| Claim | Evidence | Caveats / failure mode |
|---|---|---|
| **Cross-sectional momentum (12-1)** | The most replicated anomaly in finance. Works across countries, asset classes, and centuries of data. | Rare, violent crashes at market-bottom reversals (1932, 2009: −70%+ in months). Requires vol-scaling / dynamic hedging. High turnover. |
| **Quality / profitability** | Novy-Marx gross profitability, RMW in FF5. Robust globally; complements value. | Definition-sensitive. Crowded in mega-cap "quality compounders." |
| **Net issuance / buyback yield** | Among the cleanest and most persistent signals; low turnover. | Less exciting, therefore under-marketed. Confounded with quality/value. |
| **Time-series momentum / managed futures trend** | Multi-asset, multi-century evidence (Hurst/Ooi/Pedersen). Crisis-alpha profile: long convexity in sustained trends. | Sharpe has fallen materially post-2010. Chop kills it. Long flat periods test conviction. |
| **Diversification, low cost, tax efficiency, rebalancing** | The most reliable "alpha" available to a private investor. Costs and taxes are certain; returns are not. | Boring. Consistently under-weighted relative to its expected value. |
| **Behavioral discipline in drawdowns** | Dalbar-style investor-vs-fund return gaps are large and persistent. | This is a *process* edge, not a signal. Still the highest-ROI improvement for most investors. |

## B — Real but decayed

| Claim | Evidence | Caveats |
|---|---|---|
| **Value (HML)** | Deep theory + long history. But a brutal 2007–2020 drawdown; price-to-book is arguably broken by intangibles. | Works better with quality overlay, outside mega-caps, and with better value metrics (EV/EBIT, FCF yield) than P/B. Long horizons required. |
| **Post-earnings announcement drift (PEAD)** | Survived 50 years — one of the longest-lived anomalies. | Substantially decayed; concentrated in small/illiquid names and around the announcement window. Costs eat much of it. |
| **Low-volatility / betting-against-beta** | Real; leverage-constraint mechanism is credible (Frazzini/Pedersen). | Became a crowded, expensive trade. Sensitive to how beta-neutrality is implemented. Rate-sensitive. |
| **Carry (FX, rates, commodities)** | Persistent across asset classes. | Short-volatility in character: "picking up nickels." Crash risk clusters with risk-off. |
| **Volatility risk premium (selling options)** | Genuinely positive premium; IV > subsequent RV on average. | Negative skew, fat left tail, and vulnerable to sizing errors (Feb 2018, Mar 2020). Positive expectancy ≠ survivable. |
| **Size (SMB)** | Weak-to-nonexistent standalone since publication (1981). | Only meaningful *interacted* with quality/profitability — i.e., small **and** profitable. Small-and-junk is a return sink. |
| **Accruals** | Real discovery (Sloan 1996). | Largely arbitraged away. |
| **Seasonality/turn-of-month/holiday effects** | Some (turn-of-month) have real flow mechanisms. | Effect sizes are small relative to costs and heavily data-mined. Treat as C at best in practice. |

## C — Conditional (the sign can flip — this is where most self-deception happens)

| Claim | Verdict |
|---|---|
| **Trend/valuation regime filters (e.g. 200DMA timing)** | Reliably reduces drawdown; **does not** reliably improve return. Whipsaw cost in choppy markets is real, and it typically underperforms buy-and-hold in strong bull decades. Sell it as risk management, never as an alpha source. *(User's own QM work: a 200DMA timer HURT versus buy-and-hold.)* |
| **Quantitative Momentum / FIP quality overlay** | *(User's own falsification, full-history 2004–2026)*: raw QM ≈ −1.2pp/yr vs SPY; the FIP quality component contributes nothing (t ≤ 1.02); top configs **flip sign around 2015**. What survives is a weak *conditional* risk-on selection tilt, not an index-beater. Treat as a cautionary example of a signal that looks great in a 2022–26 window and dies on full history. |
| **Pre-earnings drift** | *(User's own study)*: +2.4bps, t = 1.74, **placebo kills it**. The naive +18bps was ~93% panel-baseline artifact. Not a tradable edge. |
| **Sector/factor rotation on macro signals** | Weak out-of-sample; requires forecasting macro, which fails (see F). Occasionally works in extreme regimes. |
| **Vol targeting / risk parity within a sleeve** | Improves Sharpe fairly robustly; does not add return. Leverage and rate-regime sensitivity are the risks. |
| **Index reconstitution / forced-flow trades (S&P adds, Russell recon)** | Real mechanism (mandated, price-insensitive buyers), but the classic add-effect has largely decayed as it became anticipated. Where it survives, it survives in the *less-anticipated* corners. Test point-in-time, with costs. |
| **Insider buying** | Cluster buying by multiple insiders in small caps retains some signal; single routine purchases do not. |
| **Short interest / crowding** | Informative as a *risk* input; a poor standalone entry signal. |
| **Options dealer gamma / GEX positioning** | Mechanism is real; the retail-available data and models are crude and the effect is widely overclaimed. Directionally useful for expected *volatility*, weak for expected *direction*. |
| **Mean reversion (intraday / short-horizon)** | *(User falsified this in own research.)* Gross edge exists in some specifications; net of spread and impact at retail scale it generally does not survive. |
| **Opening range breakout (ORB)** | *(User falsified this too.)* Sensitive to parameterization, regime, and cost assumptions — the hallmark of an overfit family. |

## D — Unproven

- Most sentiment and alternative-data signals at retail scale (decay fast; institutional-grade data required).
- Social-media / retail-flow signals (real for a few 2021-style episodes; not a durable strategy).
- Most machine-learning equity strategies as marketed — the honest ML literature (Gu/Kelly/Xiu) shows real but modest gross gains that shrink sharply after costs and require serious infrastructure.
- Crypto "on-chain" valuation frameworks.
- Thematic ETFs as a strategy (the theme is often right and the returns still poor — see the pricing-power point in SKILL.md).

## F — Folklore, data-mined, or empirically refuted

| Claim | Why it fails |
|---|---|
| **Macro forecasting to time markets** | Economists' recession-call record is famously poor; the IMF/consensus has missed the overwhelming majority of recessions in the year prior. Rate-path forecasts (including the dots and market-implied paths) are routinely wrong by 100bp+. Position robustly rather than predicting. |
| **Wall Street year-end index targets** | Systematically clustered near +8–10%, revised toward the market, and add no information. |
| **Chart patterns (head-and-shoulders, flags, pennants, Elliott waves, harmonics)** | No credible out-of-sample evidence; findings are consistent with pattern-seeking on noise. |
| **Standalone oscillators (RSI/MACD/stochastics) as entry signals** | Fail once parameter-search and multiple-testing are accounted for. |
| **Calendar folklore** — "Sell in May," Santa Claus rally, January barometer, presidential/Super Bowl cycles | Classic data-mining; effects vanish or reverse out-of-sample and are tiny versus costs. |
| **Trading geopolitical headlines** | Base rate says broad indices absorb geopolitical shocks within weeks. Trade the transmission channel or don't trade it (see SKILL.md). |
| **Active manager persistence** | SPIVA/Persistence scorecards: the large majority of active funds underperform their benchmark over 10–15 years, and top-quartile persistence is at or below chance. |
| **Mean-variance optimization on estimated inputs** | DeMiguel/Garlappi/Uppal: naive 1/N beats sample-based mean-variance out of sample across datasets. Estimation error swamps optimization benefit. |
| **Backtests without point-in-time universes** | Survivorship + look-ahead routinely inflate results by multiples. *(User's own case: an engine with 1-month look-ahead plus survivorship inflated QM results ~3×; a "+11.5%" result was fiction.)* |
| **Martingale / averaging-down position sizing** | Converts a small edge into an eventual ruin event. The math is not ambiguous. |

---

## Diagnostic questions for any strategy claim

1. **Sample.** What full history — not the flattering window? Does the sign flip across sub-periods? (If it flips at a regime boundary, that *is* the result.)
2. **Universe.** Point-in-time membership, or today's survivors backfilled?
3. **Timing.** Any information used before it was knowable? Signal on close, trade on close?
4. **Costs.** Spread, impact, borrow, financing, taxes — modeled pessimistically?
5. **Multiplicity.** How many variants were tried before this one? Report the search, not just the winner.
6. **Placebo.** Does a random/shuffled signal produce a similar result? If yes, you measured the panel baseline, not an edge.
7. **Capacity.** Does it still work at your size — and would it still work if it were widely known?
8. **Mechanism.** *Why* does someone lose money on the other side of this trade, persistently? No answer = no edge.
9. **Livability.** What's the worst drawdown and longest underwater period? Would you actually hold through it?

If a claim can't clear these, the honest verdict is "not established" — say that rather than manufacturing a hedged endorsement.
