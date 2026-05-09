---
name: market-intel
description: |
  Daily market intelligence dashboard for a personal stock watchlist. Delivers news sentiment,
  Reddit buzz, technical signals, earnings/events, volatility alerts, options flow hints, macro
  overlay, sector heatmap, and correlation monitoring — all in one on-demand briefing with
  actionable takeaways. Use this skill whenever the user asks about their stock watchlist,
  daily market update, stock news, market briefing, "what's happening with my stocks",
  "how is AAPL doing", "market intel", "morning briefing", "stock dashboard", "market pulse",
  "any news on my portfolio", or mentions wanting a market summary, stock sentiment, or
  investment update. Also trigger for casual phrasing like "anything interesting in the market
  today?", "check on my stocks", "give me the rundown on AAPL", or "what should I know
  before market open?". Trigger even if only one ticker is mentioned — the skill handles
  single stocks and full watchlists alike.
---

# Market Intel — Daily Stock Intelligence Briefing

## What this skill does

Generates a comprehensive, actionable market intelligence briefing for the user's stock
watchlist. Think of it as a personal analyst who reads every headline, scans Reddit threads,
checks the technicals, monitors options flow, and watches the macro picture — then distills
it all into a concise briefing with clear takeaways.

The briefing covers eight modules, each adding a different lens on the same positions:

1. **News Sentiment** — recent headlines with an AI-scored bullish/bearish sentiment reading
2. **Reddit Buzz** — community sentiment from r/stocks, r/wallstreetbets, and similar subs
3. **Technical Dashboard** — RSI, key moving averages (50/200-day), MACD, volume anomalies,
   and support/resistance levels
4. **Earnings & Events** — upcoming earnings dates, ex-dividend dates, analyst rating changes
5. **Volatility Alert** — flags any stock moving >2 standard deviations from its 30-day mean
6. **Options Flow Hints** — put/call ratio, unusual volume spikes, implied volatility rank
7. **Macro Overlay** — relevant macro signals (Treasury yields, VIX, DXY, Fed/CPI context)
   that could ripple into the watchlist
8. **Sector Heatmap & Correlation** — how each stock is performing vs. its sector, and whether
   any unusual correlation shifts are occurring (e.g., a stock suddenly decorrelating from its
   usual peers)

The output ends with a **"What This Means For You"** section — plain-language, actionable
takeaways that tie the data together rather than just dumping raw numbers.

## Watchlist Configuration

The default watchlist is: **AAPL**

If the user mentions other tickers, add them to the run. If they say "add MSFT to my
watchlist" or similar, include it going forward. The skill works with 1 ticker or 20 — it
adapts the depth of coverage based on how many stocks are in play (more stocks = more
concise per-stock summaries, fewer stocks = deeper dives).

## How to run

### Step 1: Install dependencies

```bash
pip install yfinance pandas numpy scipy --break-system-packages -q
```

### Step 2: Determine the watchlist

Check what the user asked for:
- If they mention specific tickers, use those
- If they say "my stocks" or "my watchlist" without specifying, use the default: `["AAPL"]`
- If they've previously mentioned adding tickers in this conversation, include those too

### Step 3: Gather data — run modules in parallel where possible

The briefing has two data-gathering phases. Phase 1 uses MCP tools (news + Reddit), and
Phase 2 uses the Python analysis script for everything else.

#### Phase 1: MCP-powered modules (run for each ticker)

Use these MCP tools for each ticker in the watchlist:

- `mcp__market_news_sentiment__summarize_market_news` — call with `ticker` and `months: 1`
  for the most recent news and sentiment
- `mcp__market_news_sentiment__summarize_reddit_sentiment` — call with `ticker` and `months: 1`
  for Reddit community sentiment

Collect the results. These give you the News Sentiment and Reddit Buzz modules.

#### Phase 2: Technical analysis script

Run the bundled Python script for the quantitative modules:

```bash
python /path/to/this/skill/scripts/market_analysis.py --tickers AAPL MSFT --output /tmp/market_intel_data.json
```

Replace `/path/to/this/skill` with the actual skill directory path, and adjust tickers to
match the watchlist. The script outputs a JSON file with:

- Technical indicators (RSI, MAs, MACD, volume z-score)
- Volatility alert flags
- Options-relevant data (put/call proxy via volume patterns)
- Macro snapshot (^TNX for yields, ^VIX, DX-Y.NYB for dollar)
- Sector comparison (stock vs. sector ETF performance)
- Correlation data (rolling correlation with SPY and sector ETF)
- Upcoming earnings/dividend dates (from yfinance calendar)

### Step 4: Synthesize the briefing

Now combine MCP results + script output into a structured briefing. Use this template:

---

# Market Intel Briefing — [Date]

## Watchlist: [TICKER1, TICKER2, ...]

---

### [TICKER] — [Company Name]

**Price:** $XXX.XX ([+/-]X.X% today) | **Volume:** X.XM (X.Xx avg)

#### News & Sentiment
[Summarize the key headlines from the MCP news tool. Lead with the most market-moving story.
Include the overall sentiment score — e.g., "Sentiment: Moderately Bullish (7/10)"]

#### Reddit Buzz
[Summarize the Reddit sentiment. Note the dominant narrative and any contrarian takes.
Flag if retail sentiment diverges sharply from institutional news sentiment — that's
often interesting.]

#### Technical Dashboard
| Indicator | Value | Signal |
|-----------|-------|--------|
| RSI (14)  | XX.X  | [Overbought/Neutral/Oversold] |
| 50-day MA | $XXX  | [Above/Below price] |
| 200-day MA| $XXX  | [Above/Below price] |
| MACD      | X.XX  | [Bullish/Bearish crossover] |
| Volume    | X.XM  | [X.Xx average — Normal/Elevated/Spike] |

[One-sentence summary: "Technicals are [bullish/neutral/bearish] — RSI suggests..., price
is trading [above/below] both MAs..."]

#### Volatility Alert
[If the stock moved >2σ from its 30-day mean, flag it prominently. Otherwise note
"No unusual volatility detected."]

#### Options Flow Hints
[Put/call ratio, IV rank if available, any unusual volume patterns. If data is limited,
say so honestly rather than speculating.]

#### Earnings & Events
[Next earnings date, ex-dividend date, any recent analyst upgrades/downgrades. If nothing
upcoming in the next 30 days, note "No major events on the calendar."]

---

### Macro Overlay
[This section is shared across all tickers — don't repeat per stock]

| Indicator | Value | Context |
|-----------|-------|---------|
| 10Y Yield | X.XX% | [Rising/Falling — hawkish/dovish signal] |
| VIX       | XX.X  | [Low/Elevated/High fear] |
| DXY       | XXX.X | [Strong/Weak dollar — impact on multinationals] |

[Brief macro narrative: "Markets are pricing in...", "The Fed's recent...", etc.
Use web search if needed to add context about recent Fed/CPI/macro events.]

### Sector Heatmap
[For each stock, show how it's performing relative to its sector ETF over 1-week and 1-month
windows. Flag any notable outperformance or underperformance.]

### Correlation Monitor
[Flag any stocks whose rolling 30-day correlation with SPY or their sector ETF has shifted
significantly (>0.3 change). This can signal regime changes or idiosyncratic events.]

---

## What This Means For You

[This is the most important section. Write 2-4 bullet points that synthesize the entire
briefing into actionable insights. Examples:

- "AAPL is showing strong momentum with bullish technicals, but RSI is approaching
  overbought territory. Consider tightening stops if you're sitting on gains."
- "Reddit sentiment on TSLA is extremely bullish while institutional news is cautious —
  this divergence has historically preceded volatile moves. Watch the options flow."
- "The rising 10Y yield is creating headwinds for growth stocks in your watchlist.
  MSFT and GOOG may face pressure until yields stabilize."

Be specific, reference the data, and frame it in terms of what the user might want to DO
(or watch for), not just what happened.]

---

### Step 5: Output format

By default, present the briefing as formatted text in the conversation. This is the fastest
and most readable format for a daily check-in.

If the user asks for an Excel file, use the xlsx skill to create a formatted spreadsheet
with each module as a separate tab. If they ask for a PDF or document, use the appropriate
skill.

### Important notes

- **Honesty about data limitations**: yfinance doesn't provide real options chain data.
  The "options flow hints" are approximations based on volume patterns and IV estimates.
  Always disclose this — say "based on available volume data" rather than implying you
  have Level 2 options flow data.

- **Not financial advice**: End every briefing with a brief disclaimer:
  *"This briefing is for informational purposes only and does not constitute financial
  advice. Always do your own research before making investment decisions."*

- **Web search for macro context**: Use WebSearch to check for breaking macro news
  (Fed announcements, CPI releases, geopolitical events) that could affect the watchlist.
  This adds real-time context the MCP tools might not capture.

- **Timeliness**: Market data from yfinance may be delayed 15-20 minutes for some tickers.
  Note this in the briefing header if running during market hours.
