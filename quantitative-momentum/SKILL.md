---
name: quantitative-momentum
description: |
  Wes Gray / Alpha Architect Quantitative Momentum screener and backtester for S&P 500 stocks.
  Use this skill whenever the user asks about Quantitative Momentum, Wes Gray's momentum approach,
  the FIP (Frog-in-the-Pan) score, momentum quality, path smoothness of returns, or wants to
  screen stocks using both raw momentum AND momentum quality together. Also trigger when the user
  mentions "quantitative momentum", "QMOM", "Alpha Architect momentum", "momentum quality filter",
  "smooth momentum", "consistent momentum", or wants to combine a momentum signal with a quality
  overlay. This skill differs from the basic momentum-ranker (which uses raw 6-1 momentum only)
  by adding the FIP composite quality score that measures HOW a stock earned its returns — steady
  grinders rank higher than volatile spikes. Trigger even for casual phrasing like "which stocks
  have the smoothest uptrend?" or "rank stocks by momentum quality" or "run the Gray screen".
  Also runs for a PAST date — "run the QM screener as of 2024-06-28", "what did QM say last
  March", "screen for the 2009 bottom", "what would this have picked before the selloff" —
  via --as-of, which rebuilds the screen point-in-time with historical S&P 500 membership and
  no look-ahead. Supports any date from ~2004-05-10 onward.
---

# Quantitative Momentum Screener & Backtester

> **Explaining the method rather than running it?** Read
> **`references/how-it-works.md`** — the canonical stage-by-stage walkthrough and flowchart
> (universe → prices → momentum → FIP → composite rank → top 50 → rebalance), with the exact
> formulas, the signal tiers, and the honest performance verdict. Use it verbatim for any
> "how does QM work", "what is FIP", "why skip a month", or "draw me a flowchart" question.
> No scripts need to run for those. **It must be kept in sync — see *Maintaining this skill*
> at the end of this file.**

## The pipeline is Postgres-only end to end

`run_qm.py` (in `C:\Users\ssair\qm-results\`) is the daily entry point, and since
2026-08-06 **Postgres is its only handoff**:

```
qm_screener.run_screener()   in-process, returns the DataFrame
  -> qm_pg.publish_frame()   res.screen_result   <- the record, written FIRST
  -> qm_screen_source.fetch_screen()             <- read back, round-trips the publish
  -> qm_excel.py --from-pg / qm_track.py --from-pg / qm_email.py --from-pg
```

No step downstream of the publish parses a CSV or a workbook. `qm_full_ranking.csv`
and `QM_Screener_<date>.xlsx` are **outputs** — the workbook is the emailed report
and qm-recon's independent check copy. Deleting both and re-running any downstream
step still works, because the source is the database.

Two consequences worth knowing:

- **A failed publish stops the run.** Previously the workbook was built first and
  the publish came after on a best-effort basis — which meant a publish failure
  lost the screen entirely, since the CSV it read was overwritten by the next run.
- **Re-running the screener the same day re-publishes it.** The write is an upsert
  on `(run_id, obs_date, security_id)`, so a second run replaces that date's rows
  with the newer prices. Regenerate the workbook afterwards (`--from-pg`), or
  qm-recon will correctly report the stale workbook as a mismatch.

`--no-pg` is the database-down escape hatch: workbook from the screener's own
frame, nothing recorded, no pick tracking.

## What this skill does

Implements Wes Gray and Jack Vogel's **Quantitative Momentum** methodology from their 2016 book
and the Alpha Architect QMOM ETF approach. The key insight beyond basic momentum: not all momentum
is created equal. A stock that grinds steadily upward has higher-quality, more persistent momentum
than one that spiked on a single event.

This skill calculates the following signals for every S&P 500 stock:

1. **Volatility-adjusted momentum (6-1M VolAdj)** — the 6-minus-1 return divided by realized
   volatility. This risk-adjusts the momentum signal so that stocks with steady uptrends rank
   higher than volatile spikes with the same raw return. Autoresearch (70 experiments, 20-year
   backtest) showed vol-adjusted momentum improves Sharpe by 0.1–0.4 and reduces max drawdown
   by 5–15 percentage points compared to raw momentum.
2. **3M Ret%** — trailing 3-month total return (most recent 3 months, no skip). Provides a
   shorter-term momentum read to complement the 6-1 signal — useful for spotting stocks that
   are accelerating or losing steam within the broader trend.
3. **1M Ret%** — trailing 1-month total return. Captures very recent price action and helps
   identify stocks that may be surging or fading relative to their 6-1 trend.
4. **Composite FIP (Frog-in-the-Pan) quality score** — a blend of:
   - **Percent positive days**: fraction of trading days with positive returns during the lookback
     (measures consistency)
   - **Path smoothness (R-squared)**: R-squared of cumulative returns regressed against a straight
     line (measures how linear the price path was)
   - The two are equally weighted into a single composite score

Stocks are ranked using a **pure-quality composite** (FIP weight = 1.0, set 2026-06-27).
FIP weight has a monotonically positive effect on the composite metric across every sample
tested — including the survivorship-reduced 20.5yr point-in-time backtest — so the rank is now
driven by FIP quality, with 6-1 momentum kept as a contextual column. FIP acts primarily
as a **risk/drawdown filter** (quality premium ~neutral) rather than a return enhancer: at
weight 1.0 it delivered the best Sharpe (1.28) and shallowest drawdown (-41.6%) vs the 0.5
baseline (0.91 / -48.6%). (Prior default was 0.75; 0.5 is Gray's original.)

The 3M Ret% and 1M Ret% columns are included as auxiliary context columns (not used in ranking)
to help the investor assess recent price trajectory.

**Four modes:**
- **Live screener**: Rank today's S&P 500 and output the top 50 stocks with scores and signals
- **Historical screener (`--as-of`)**: Reconstruct what the screen would have said on a past
  date, using point-in-time S&P 500 membership and prices that stop at that date
- **Backtester**: Walk-forward backtest of the QM strategy over a user-specified period
- **Market news research**: For Strong Buy stocks, gather 6 months of market news with current
  prices and analyst forecasts, added as a dedicated tab in the Excel report

Output is always an Excel spreadsheet (.xlsx) with formatted tables, conditional formatting, and
summary statistics.

## How to run

### Step 1: Install dependencies (if needed)

```bash
pip install yfinance pandas numpy openpyxl lxml scipy requests keyring pyarrow --break-system-packages -q
```

### Step 2: Determine what the user wants

**"Screen stocks using Quantitative Momentum" / "Run the QM screener" / "What has the best momentum quality?"**
-> Run the live screener (Step 3a)

**"Backtest Quantitative Momentum" / "How would QM have performed?"**
-> Run the backtester (Step 3b)

**"Screen AND backtest" / "Give me the full picture"**
-> Run both (Step 3a then 3b)

**"Market news for Strong Buy stocks" / "Research the Strong Buy picks" / "What's happening with the top momentum stocks?"**
-> Run the screener first (Step 3a), then market news research (Step 3c)

**"Run the screener as of <past date>" / "What did QM say last March?" / "Screen for 2024-06-28"**
-> Run the historical screener (Step 3a-hist)

**"How does Quantitative Momentum work?" / "Explain FIP" / "Draw me a flowchart" / "Why skip a month?"**
-> Do NOT run any script. Read `references/how-it-works.md` and answer from it.

**The screener should ALWAYS be run first. Market news research depends on screener output.**

### Step 3a: Run the live screener

```bash
python <skill_dir>/scripts/qm_screener.py <output_dir>
```

This downloads S&P 500 price data, computes volatility-adjusted 6-1 momentum, 3M return, 1M return,
and composite FIP for every stock, ranks them, and saves results as JSON to stdout plus CSV files
in the output directory. The CSV includes columns: Rank, Ticker, Company, Sector, 6-1M VolAdj,
3M Ret%, 1M Ret%, FIP Score, FIP Rank, Composite QM Rank, Percentile, Signal.

**Expected runtime**: 1-3 minutes (downloads ~500 stocks).

### Step 3a-hist: Run the screener for a specific past date

To reconstruct what the screen would have said on a past date, pass `--as-of`:

```bash
python <skill_dir>/scripts/qm_screener.py <output_dir> --as-of 2024-06-28
```

This differs from the live path in two ways that matter, both automatic:

1. **Point-in-time universe.** The S&P 500 constituents come from the fja05680 historical
   membership panel in `C:\Users\ssair\s&p Historic Data\` — the most recent snapshot dated
   on or before the as-of date — instead of today's Wikipedia table. Without this the screen
   would rank the companies that are in the index *now*, which is survivorship bias.
2. **Prices stop at the as-of date.** The 8-month price window ends there, so no post-date
   information enters the momentum or FIP calculations.

**An as-of run refuses to fall back to Yahoo.** The screener passes `strict=True` on this
path. Polygon's grouped bars are point-in-time and splits-only-adjusted; Yahoo serves
survivors only and dividend-adjusts its closes. Falling back mid-backfill would silently
swap in a biased, non-comparable price series with nothing in the output showing it. The
run fails loudly instead — that is intended, do not work around it by dropping the flag.

**Earliest supported date: ~2004-05-10.** Polygon's grouped-bar history begins **2003-09-10**
(probed directly 2026-07-30: 2003-09-09 returns 0 tickers, 2003-09-10 returns 7,722), and the
screen needs ~8 months of prior history. Ask for an earlier date and the run fails rather than
returning a short window.

> Earlier versions of this file and the screener's own error message claimed the limit was
> 2021-07-15 / ~2022-02-15, from the old Polygon Starter plan. That is stale — the current
> plan serves the full ~23-year history. Do not talk the user out of a 2000s-era as-of date
> on the basis of the old figure. Re-probe if the plan changes.

The membership panel (fja05680) covers 1996-2026, so it is not the binding constraint;
Polygon's 2003-09-10 floor is.

Thread the same date through the downstream steps so the outputs are labelled honestly:

```bash
python <skill_dir>/scripts/qm_excel.py --screener-data <output_dir>/qm_full_ranking.csv \
  --as-of 2024-06-28 --output <output_dir>/QM_Screener_asof_2024-06-28.xlsx
python <skill_dir>/scripts/qm_email.py <xlsx> --screener-csv <csv> --as-of 2024-06-28
```

`--as-of` makes the workbook title and the email subject say "AS OF" / "HISTORICAL", and
the default filename becomes `QM_Screener_asof_<date>.xlsx`. Omitting it stamps a backfilled
run with today's date, which is how a historical file gets mistaken for a live screen later.

**Skip Step 3c (market news) entirely for as-of runs.** Yahoo serves only today's prices,
analyst targets and consensus — attaching them to a past-dated screen is look-ahead bias.
`qm_market_news.py --as-of <date>` exits with an error rather than let this happen.

**Caveats to state when presenting historical results:**

- **Survivorship is reduced, not eliminated.** The membership panel restores the right
  *constituents*, but names Polygon has no bars for still drop out. Expect roughly 5-8% attrition
  on older dates (a 2009-03-31 run: 499 point-in-time members → 466 with prices → 463 ranked).
  The dropped names are disproportionately the ones that later failed, so the surviving screen
  is still mildly optimistic. Treat an as-of screen as indicative, not a clean backtest
  observation.
- **Company names and sectors go "Unknown" for delisted tickers.** This metadata comes from
  *today's* Wikipedia table on a best-effort basis, so anything since delisted or renamed
  (MYL, WYE, SGP, BMC…) shows the bare ticker and "Unknown" sector. On a 2009 run that can be
  half the top 50. It is cosmetic — these fields play no part in momentum, FIP, or the ranking —
  but say so when presenting, and do not report the "Unknown" bucket as a real sector
  concentration. Sector counts on old screens are unreliable for this reason.

### Step 3b: Run the backtester

```bash
python <skill_dir>/scripts/qm_backtest.py \
  --universe pit \
  --start-year <year> \
  --n-holdings <N> \
  --output-dir <output_dir>
```

Arguments:
- `--start-year`: When the backtest starts (default: 2015). Use 2006 for 20 years.
- `--n-holdings`: Number of stocks in the portfolio (default: 50, matching Gray's approach).
- `--rebalance`: Rebalancing frequency — "monthly" (default, optimized by autoresearch) or "quarterly".
  Monthly rebalancing added +0.46 composite points over quarterly in 20-year backtesting.
- `--universe`: **Always pass `pit`.** `wikipedia` — still the default, kept only so old runs stay
  reproducible — screens *today's* constituents over past data, the survivorship bias that
  inflated the early results here ~3x. `pit` uses point-in-time membership and a
  delisted-inclusive price panel.
- `--index-code`: PIT mode only — which index's membership defines the universe (default `SP500`).
- `--output-dir`: Where to save results JSON.

**`--universe pit` reads from the Postgres `trading` DB** on localhost:5433
(`ref.index_membership` + `mkt.price_daily`) through the house adapter at
`C:\Users\ssair\trading-db\pgdb.py`. Nothing is cached to disk and no local panel is built. The
panel is keyed by `security_id`, never by a ticker string. Postgres must be up for this path —
it raises rather than falling back to a biased source. Per-rebalance coverage of point-in-time
members is 100.0% avg / 99.8% min (Aug-2026), vs ~70% on the free panel this replaced.

**Benchmark basis.** PIT runs benchmark against SPY pulled from the same `mkt.price_daily`
table, so both sides are price return; the results JSON records this as
`"benchmark_basis": "price_return"`. The wikipedia path uses Yahoo's dividend-reinvested SPY
and records `"total_return"`. Report the basis with any excess-return figure and never compare
one across the two — the mismatch is worth ~2.1pp/yr.

### Step 3c: Market news research for Strong Buy stocks

This step adds a "Market News Summary" tab to the Excel report covering the last 6 months of
market-moving events for every stock with a "Strong Buy" signal. It runs in three phases:

**Phase 1 — Fetch analyst data (automated via script):**

```bash
python <skill_dir>/scripts/qm_market_news.py \
  --screener-csv <output_dir>/qm_full_ranking.csv \
  --signal "Strong Buy" \
  --output-dir <output_dir>
```

This fetches from Yahoo Finance for each Strong Buy stock:
- Current price
- Analyst mean/high/low price targets
- Consensus recommendation (buy/hold/sell)
- Number of covering analysts

Output: `analyst_data.json` and `strong_buy_tickers.json` in the output directory.

**Phase 2 — Research market news (Claude performs this using web search):**

For each Strong Buy stock, use web search to research the last 6 months of news covering:
- **Market news**: earnings results, guidance, analyst upgrades/downgrades, stock price moves
- **Product news**: new product launches, clinical trials, technology milestones
- **Organization news**: leadership changes, M&A activity, restructuring, board changes
- **Price drivers**: sector trends, macro factors, regulatory impacts, geopolitical events

To handle research efficiently for many stocks, batch them into groups of ~10 and use
subagents in parallel. Each subagent researches its batch and returns a JSON array of
objects with keys: ticker, company, summary.

**Critical formatting requirements for the market news summary:**
- Every event MUST include an explicit year-month reference (e.g., "In Oct-2025", "In Feb-2026")
- Summaries should be 1-2 detailed paragraphs per stock
- Use chronological order within each summary
- Include specific financial figures (revenue, EPS, growth rates) where available

**Phase 3 — Add Market News tab to the Excel file (using openpyxl):**

After generating the base Excel report (Step 4), open the workbook and add a "Market News Summary"
sheet with these columns:

| Column | Header | Width | Format |
|--------|--------|-------|--------|
| A | Ticker | 10 | Bold, center-aligned |
| B | Stock Name | 26 | Left-aligned |
| C | Current Price | 14 | Currency $#,##0.00, right-aligned, bold |
| D | Analyst Target (Mean) | 18 | Currency $#,##0.00, right-aligned |
| E | Upside % | 12 | Percentage 0.0%, green if positive, red if negative |
| F | Consensus | 14 | e.g. "Buy (31 analysts)", wrap text |
| G | Market News Summary | 110 | Wrap text, top-aligned |

Formatting:
- Header row: dark blue (#1F4E79) fill, white text, Arial 11pt bold
- Data rows: Arial 10pt, alternating row fill (#F2F7FB)
- Freeze panes at A5 (below header row)
- Auto-filter on all columns
- Row height ~90px for text wrapping
- Title row (merged A1:G1): report name with date range
- Subtitle row (merged A2:G2): generation date + methodology note
- Thin borders (#B0B0B0) on all data cells

### Step 4: Generate the Excel report

**Prefer `--from-pg`** — render the workbook from the published screen rather than
from a file, so it cannot disagree with the record:

```bash
python <skill_dir>/scripts/qm_excel.py \
  --from-pg [--screen-date 2026-08-06] \
  --backtest-data <output_dir>/qm_backtest_results.json \
  --output <final_output.xlsx>
```

`--screen-date` defaults to the newest published screen. The CSV form still works
for an ad-hoc screen that was never published (a `--as-of` reconstruction, say):

```bash
python <skill_dir>/scripts/qm_excel.py \
  --screener-data <output_dir>/qm_full_ranking.csv \
  --backtest-data <output_dir>/qm_backtest_results.json \
  --output <final_output.xlsx>
```

Either source can be omitted if only the backtest is being reported.

Then recalculate formulas if the xlsx skill's recalc script is available:
```bash
python <session_dir>/mnt/.skills/skills/xlsx/scripts/recalc.py <final_output.xlsx>
```

If market news was requested, add the Market News Summary tab to the Excel file after
generating the base report (see Step 3c, Phase 3).

### Step 5: Present results to the user

After generating the Excel file, present:

1. **Summary statistics** — number of stocks analyzed, date, top 10 by composite QM rank
2. **Key insight** — highlight any stocks that rank high on raw momentum but LOW on FIP quality
   (these are the "spike" stocks Gray warns about) and vice versa. Also flag stocks where the
   1M or 3M return diverges sharply from the 6-1 trend (e.g., strong 6-1 but negative 1M
   could signal momentum fading; weak 6-1 but strong 1M could signal a turnaround)
3. **Sector concentration** — flag if the top holdings are heavily concentrated
4. **Market news highlights** (if market news was generated) — notable themes across sectors,
   biggest analyst upside/downside targets, any stocks where analyst consensus diverges from
   the Strong Buy momentum signal
5. **Link to the Excel file** for the user to download and explore

### Step 6: Email results via SMTP

After generating the Excel report, email it to **ssairam@gmail.com** with the Excel file
attached using the SMTP email script.

```bash
pip install keyring keyrings.alt --break-system-packages -q
python <skill_dir>/scripts/qm_email.py <excel_file> \
  --screener-csv <output_dir>/qm_full_ranking.csv \
  --to ssairam@gmail.com
```

**What this does:**
- Sends an email via Gmail SMTP with the Excel workbook attached
- Email body includes a brief greeting, analysis date, and a top-10 stocks HTML table
- Subject line: `QM Screener Results — [today's date]`
- Sender: ssairam@gmail.com

For a historical run, add `--as-of <YYYY-MM-DD>`. The subject becomes
`QM Screener — HISTORICAL as of [date]` and the body carries a banner explaining that it is a
point-in-time reconstruction with no analyst data. Without the flag the email announces a
backfill as if it were today's screen.

**Credential storage:**
- The Gmail app password is stored in the system keyring (Windows Credential Manager on Windows,
  file-based keyring in Linux/Cowork VM) under service `qm-screener-smtp`, username `ssairam@gmail.com`
- Fallback: set environment variable `GMAIL_APP_PASSWORD` if keyring is unavailable
- One-time setup: `python -c "import keyring; keyring.set_password('qm-screener-smtp', 'ssairam@gmail.com', 'APP_PASSWORD')"`

**In scheduled task mode**: The email script runs automatically after the Excel file is generated.
The user receives the email with the full Excel workbook attached — no manual steps needed.

**Fallback**: If the email fails (e.g., credential issues, network), log the error but do not
fail the entire screener run. Note the failure in the output and remind the user to check
their app password setup.

### Step 7: Offer follow-ups

- **Portfolio check**: "Want me to see how your current holdings score on momentum quality?"
- **Compare with basic momentum**: "Want to see how QM differs from the simple 6-1 screener?"
- **Backtest**: "Want to backtest this to see historical performance?"
- **Parameter tweaks**: "Want to try different lookback periods or holding counts?"
- **Market news**: "Want me to research 6 months of market news for the Strong Buy stocks?"

## Autoresearch provenance (March 2026)

The defaults in this skill were optimized via the qm-autoresearch skill (Karpathy-style
autoresearch pattern) on March 22, 2026. The optimization ran 70 parameter experiments + 5 hybrid
agent modifications over a 20-year backtest (2006–2026). Three changes were applied:

1. **Volatility-adjusted momentum** (hybrid modification): Divides raw 6-1 momentum by realized
   volatility. Improved Sharpe from 1.09 → 1.70 and reduced max drawdown from -37.5% → -33.6%.
2. **FIP weight 0.75** (was 0.50): FIP weight showed monotonic improvement in composite metric.
   Higher FIP weight means the quality dimension contributes more to ranking. FIP acts as a risk
   filter — it doesn't strongly predict which stocks outperform, but it filters out volatile spikes.
3. **Monthly rebalancing** (was quarterly): Biggest single-parameter lever. Added +0.46 composite
   points. Tradeoff: higher turnover and potentially more tax events.

Robustness check: All top configs performed *better* on the 2015–2026 subperiod than the full
20-year period, reducing overfitting concern (though the recent decade was a strong bull market).

### Update 2026-06-27 — FIP weight 0.75 → 1.0 (survivorship-reduced re-run)
Re-ran the autoresearch on a **point-in-time, survivorship-reduced** universe: a local daily
adjusted-close panel (1970–2026, 836 tickers) + fja05680 historical S&P 500 membership, with a
per-rebalance constituent filter (data in `C:\Users\ssair\s&p Historic Data\`). Across this honest
20.5yr backtest AND the earlier samples, **FIP weight is monotonically positive on the composite**,
and **1.0 was best** (Sharpe 1.28, max DD −41.6%, +11.5%/yr excess vs SPY) — so the production
default is now **fip_weight = 1.0**. On the unbiased data the FIP **quality premium is ~neutral**
(1/20 experiments positive), confirming FIP works as a **risk/drawdown filter, not a return
predictor**. Caveats: in-sample (no walk-forward); delisted-price coverage ~70% (368 of 1,202
names unavailable from free sources); 1.0 makes the rank pure-quality (momentum demoted to context).

To revert to Gray's original defaults, pass `--params-json '{"fip_weight": 0.5, "rebalance_freq":
"quarterly", "vol_adjust_momentum": false}'` to the backtester.

## Important context about this investor

- Strategy: long S&P index + concentrated top-10 S&P stocks overlay
- Goal: beat S&P 500 returns through informed stock selection
- Follows macro closely (GDP, debt levels, geopolitics)
- Uses cross-sectional momentum to identify buy/hold/sell decisions
- Manages 401K (self + spouse) and a brokerage account
- Already uses a basic momentum-ranker skill (6-1 raw momentum) — this skill adds the quality dimension

## Data sources

The screener and backtester use a layered data-source strategy:

- **Postgres `trading` (the backtester's `--universe pit` path)**: `ref.index_membership` for
  point-in-time constituents and `mkt.price_daily` for split-adjusted closes including delisted
  names, on localhost:5433 via `C:\Users\ssair\trading-db\pgdb.py`. This is the honest path and
  the only one for any published backtest number. Prices there are split-adjusted but **not**
  dividend-adjusted — price returns, so say so before comparing to a total-return benchmark.
- **Polygon.io (primary for prices)**: The screener (and short-window backtests ≤ 2 years) pull
  prices via Polygon's Grouped Daily Bars endpoint — one API call per trading day returns the
  full US universe. Per-day responses are cached as parquet under `~/.qm-cache/polygon_daily/`,
  so subsequent runs only fetch new days.
- **Yahoo Finance (fallback for prices)**: Used automatically if Polygon is unavailable or
  returns insufficient data, and for backtests starting before **2003-09-10** (Polygon's first
  grouped-bar day, verified 2026-07-30). Note that a live-path fallback is silent — Yahoo is
  survivor-only and dividend-adjusted, so results are not strictly comparable to a Polygon run.
  On an `--as-of` run the fallback is disabled outright and the script fails instead.
- **Yahoo Finance (only source for analyst data)**: `qm_market_news.py` always uses Yahoo for
  analyst price targets / consensus / number of analysts — Polygon doesn't offer that data on
  any plan.
- **Wikipedia (S&P 500 universe + sectors)**: Fetched with a real User-Agent header to avoid
  the 403 Wikipedia returns for default urllib UAs.

### Polygon API key setup (one-time)

The Polygon API key is read from the Windows Credential Manager / system keyring under
service `polygon-api`, username `default`. To set it up:

```bash
python -c "import keyring; keyring.set_password('polygon-api', 'default', 'YOUR_POLYGON_KEY')"
```

Fallback: set environment variable `POLYGON_API_KEY`. If no key is found anywhere, both
scripts skip Polygon and use Yahoo directly.

## Handling errors

- **Rate limiting / download failures**: Polygon (paid) avoids the Yahoo rate-limit issues
  that historically plagued the screener. If Polygon does fail (HTTP 429 / outage), the
  scripts automatically retry via Yahoo. Note how many tickers were successfully analyzed
  in the output.
- **Stale Wikipedia data**: If the S&P 500 list fetch fails, the script falls back to a
  hardcoded list. The hardcoded path no longer makes per-ticker `yf.Ticker().info` calls
  (that was the trigger for the historical Yahoo rate-limit cascade).
- **Market closed / weekend**: Data reflects the last trading day's close. Note this to the user.
- **Insufficient history for backtest**: If start year is too early for available data, the script
  will report fewer months than expected. Check `n_months` in results.
- **Polygon history limits**: the current plan serves grouped daily bars from **2003-09-10**
  onward (~23 years) — the old "Starter ~2 yr / Developer ~10 yr" note was stale and is
  corrected here. Only pre-2003-09-10 backtests route through Yahoo. The backtester logs
  which source it picked; check that log rather than assuming.
- **Yahoo Finance rate limits for analyst data**: The qm_market_news.py script handles individual
  ticker failures gracefully and reports them. A few missing tickers won't break the report.

## Maintaining this skill

`references/how-it-works.md` is the user-facing explanation of the method and is expected to
match the code exactly. **Treat it as part of the code, not as documentation about the code.**

Whenever you change any of the following, update `references/how-it-works.md` in the *same*
edit — never leave it for later:

| Changed in… | Update in how-it-works.md |
|---|---|
| `fip_weight` or the composite rank formula (`build_qm_ranking`) | Stage 5 + the mermaid node |
| FIP components or `lookback_days` (`calculate_fip_score`) | Stage 4 formula block |
| `lookback_months` / `skip_months` / vol adjustment (`calculate_momentum`) | Stage 3 formula block |
| Signal-tier percentile cutoffs (`assign_signal`) | Stage 5 + the mermaid node |
| `--n-holdings` / `--rebalance` defaults (`qm_backtest.py`) | Stages 6–7 + the mermaid node |
| Universe construction or price-source rules | Stages 1–2 |
| Any new backtest number that supersedes an existing one | The *What it's actually worth* table |

Then bump the **Last verified against the code** date at the top of that file. Re-read the
actual functions when doing this — do not carry the previous text forward on trust.

Corollary for autoresearch runs: a new default landing in this skill is not finished until
how-it-works.md carries the new value *and* its provenance.

---

## Telemetry (standing requirement — all skills)

Log this run **once, at the very end**, whether it went well or not (Bash tool; forward slashes):

```bash
python C:/Users/ssair/.claude/telemetry/telemetry.py log --skill quantitative-momentum \
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
