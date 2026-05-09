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
---

# Quantitative Momentum Screener & Backtester

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

Stocks are ranked using a **75/25 FIP-to-momentum weighted composite** (FIP weight = 0.75).
Autoresearch found that FIP weight has a monotonically positive effect on the composite metric —
higher FIP weight means quality/smoothness contributes more to the final rank. FIP acts primarily
as a risk filter (filtering out volatile spikes) rather than a return enhancer.

The 3M Ret% and 1M Ret% columns are included as auxiliary context columns (not used in ranking)
to help the investor assess recent price trajectory.

**Three modes:**
- **Live screener**: Rank today's S&P 500 and output the top 50 stocks with scores and signals
- **Backtester**: Walk-forward backtest of the QM strategy over a user-specified period
- **Market news research**: For Strong Buy stocks, gather 6 months of market news with current
  prices and analyst forecasts, added as a dedicated tab in the Excel report

Output is always an Excel spreadsheet (.xlsx) with formatted tables, conditional formatting, and
summary statistics.

## How to run

### Step 1: Install dependencies (if needed)

```bash
pip install yfinance pandas numpy openpyxl lxml scipy --break-system-packages -q
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

### Step 3b: Run the backtester

```bash
python <skill_dir>/scripts/qm_backtest.py \
  --start-year <year> \
  --n-holdings <N> \
  --output-dir <output_dir>
```

Arguments:
- `--start-year`: When the backtest starts (default: 2015). Use 2006 for 20 years.
- `--n-holdings`: Number of stocks in the portfolio (default: 50, matching Gray's approach).
- `--rebalance`: Rebalancing frequency — "monthly" (default, optimized by autoresearch) or "quarterly".
  Monthly rebalancing added +0.46 composite points over quarterly in 20-year backtesting.
- `--output-dir`: Where to save results JSON.

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

After running the screener and/or backtester, generate the Excel output:

```bash
python <skill_dir>/scripts/qm_excel.py \
  --screener-data <output_dir>/qm_full_ranking.csv \
  --backtest-data <output_dir>/qm_backtest_results.json \
  --output <final_output.xlsx>
```

Either `--screener-data` or `--backtest-data` can be omitted if only one mode was run.

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

To revert to Gray's original defaults, pass `--params-json '{"fip_weight": 0.5, "rebalance_freq":
"quarterly", "vol_adjust_momentum": false}'` to the backtester.

## Important context about this investor

- Strategy: long S&P index + concentrated top-10 S&P stocks overlay
- Goal: beat S&P 500 returns through informed stock selection
- Follows macro closely (GDP, debt levels, geopolitics)
- Uses cross-sectional momentum to identify buy/hold/sell decisions
- Manages 401K (self + spouse) and a brokerage account
- Already uses a basic momentum-ranker skill (6-1 raw momentum) — this skill adds the quality dimension

## Handling errors

- **Rate limiting / download failures**: yfinance occasionally fails on a few tickers. The scripts
  handle this gracefully — note how many were successfully analyzed.
- **Stale Wikipedia data**: If the S&P 500 list fetch fails, the script falls back to a hardcoded list.
- **Market closed / weekend**: Data reflects the last trading day's close. Note this to the user.
- **Insufficient history for backtest**: If start year is too early for available data, the script
  will report fewer months than expected. Check `n_months` in results.
- **Yahoo Finance rate limits for analyst data**: The qm_market_news.py script handles individual
  ticker failures gracefully and reports them. A few missing tickers won't break the report.
