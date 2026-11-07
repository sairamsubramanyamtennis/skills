---
name: smarket-intel
description: |
  Daily market intelligence briefing, in two modes. With no ticker it covers THE MARKET —
  the day's index moves, sector rotation, breadth, risk appetite, volatility, the Fed/macro
  calendar and the news driving it. With one or more tickers it adds per-stock coverage:
  news sentiment, technical signals, earnings/events, volatility alerts, options
  flow hints, sector-relative performance, and correlation monitoring. Both end with
  actionable takeaways. Use this skill whenever the user asks for a daily market update,
  market briefing, "how did the market do today", "what moved the market", "market intel",
  "morning briefing", "market pulse", "what should I know before the open", "how are futures",
  sector rotation, market breadth, or what the Fed/CPI print means for stocks. It also covers
  the month's macro event calendar — "what did the Fed do", "when is the next CPI", "what
  happened on the jobs report", "what's on the calendar this week", "how did the market react
  to the last FOMC" — and equally
  when they ask about specific holdings: "how is NVDA doing", "any news on my portfolio",
  "check on my stocks", "give me the rundown on TSLA". Trigger with zero tickers, one ticker,
  or twenty — the skill picks the right mode. Also runs for a PAST date — "market intel for
  March 13", "how did the market look on 2026-03-13", "what was the tape doing last Friday",
  "NVDA briefing as of the day before earnings" — via --as-of, which rebuilds the whole
  briefing point-in-time with no look-ahead.
---

# Market Intel — Daily Stock Intelligence Briefing

## What this skill does

Generates a comprehensive, actionable market intelligence briefing for the user's stock
watchlist. Think of it as a personal analyst who reads every headline, checks the technicals,
monitors options flow, and watches the macro picture — then distills it all into a concise
briefing with clear takeaways.

The briefing covers eight modules, each adding a different lens on the same positions:

1. **News Sentiment** — recent headlines with an AI-scored bullish/bearish sentiment reading
2. **Technical Dashboard** — RSI, key moving averages (50/200-day), MACD, volume anomalies,
   and support/resistance levels
3. **Earnings & Events** — upcoming earnings dates, ex-dividend dates, analyst rating changes
4. **Volatility Alert** — flags any stock moving >2 standard deviations from its 30-day mean
5. **Options Flow Hints** — put/call ratio, unusual volume spikes, implied volatility rank
6. **Macro Overlay** — relevant macro signals (Treasury yields, VIX, DXY, Fed/CPI context)
   that could ripple into the watchlist
7. **Macro Event Calendar** — the month's scheduled events (FOMC, jobs, CPI, PPI, PCE), what
   the market actually did on each one, and what is coming in the next three weeks
8. **Sector Heatmap & Correlation** — how each stock is performing vs. its sector, and whether
   any unusual correlation shifts are occurring (e.g., a stock suddenly decorrelating from its
   usual peers)

The output ends with a **"What This Means For You"** section — plain-language, actionable
takeaways that tie the data together rather than just dumping raw numbers.

## Two modes — pick by whether a ticker was named

**There is no default ticker.** Never invent one, and never fall back to a sample ticker
from this file. What the user named (or didn't) selects the mode:

### Market mode — no ticker mentioned

This is the default for a bare `/smarket-intel`, "morning briefing", "how did the market do",
or any request with no ticker in it. The subject is **the market itself**:

- **Index scoreboard** — S&P 500 (SPY), Nasdaq 100 (QQQ), Dow (DIA), Russell 2000 (IWM),
  and equal-weight S&P (RSP): today's move plus 1w / 1m / 3m / YTD, RSI, and 50/200-day MA position
- **Sector rotation** — all 11 SPDR sectors ranked by today's move, each measured against SPY
  over 1d / 1w / 1m. This is where the day's real story usually is
- **Breadth** — the advance/decline line across the ~500 point-in-time index constituents,
  the share above their 50/200-day MAs, and the new 52-week high/low tally. Plus the coarser
  sector-participation count (how many of the 11 SPDRs advanced)
- **Risk appetite** — the ratio pairs (XLY/XLP, IWM/SPY, RSP/SPY, HYG/IEF, SMH/SPY).
  Rising = risk-on for every pair
- **Safe havens** — TLT, GLD, UUP
- **Volatility & macro** — VIX level and 1-week change, 10Y yield, dollar
- **The news and the calendar** — what actually drove the tape, plus the Fed / CPI / jobs
  / earnings events in the window. Get this with WebSearch (see Phase 1)

Do **not** silently substitute a stock briefing for a market briefing. If the user asks how
the market did, the answer is about indices, sectors and macro — not about any one company.

### Watchlist mode — one or more tickers mentioned

Cover each named ticker with the full per-stock module set. Tickers mentioned earlier in the
conversation stay in scope; if the user says "add MSFT", include it going forward. Works with
1 ticker or 20, adapting depth — more stocks means more concise per-stock summaries, fewer
means deeper dives. Add the Macro Overlay once at the end, never per stock.

In watchlist mode you may also pass `--market` to get the market block alongside the stocks;
do that when the user asks for both ("how's the market and my positions"), or when a name is
moving and the market context is needed to tell stock-specific news from a broad tape move.

## Running for a past date

Both modes accept `--as-of YYYY-MM-DD` (alias `--date`) and rebuild the entire briefing as it
would have read at that day's close. Use it whenever the request names a day that isn't today:
"how did the market look on March 13", "what was the tape doing the day before the Fed",
"NVDA briefing as of last Friday". Resolve relative dates ("last Friday", "the day CPI landed")
to a calendar date yourself before calling the script — it only takes ISO dates.

**It is genuinely point-in-time, not a filter on today's answer.** Series are truncated at the
date, MAs/RSI/MACD/correlations are computed from bars ending there, the news window is bounded
on the right, and — the part that is easy to get wrong — **ticker→company identity is resolved
at that date, not today**. A 2008 run correctly finds no `QQQ` (it traded as QQQQ until 2011)
rather than splicing today's fund onto a 2008 price series.

Pass the same date to **all three** scripts, or the tables, the headlines and the calendar
will describe different days:

```bash
python /path/to/this/skill/scripts/market_analysis.py --as-of 2026-03-13 --output /tmp/data.json
python /path/to/this/skill/scripts/massive_news.py --market --as-of 2026-03-13 --output /tmp/news.json
python /path/to/this/skill/scripts/macro_calendar.py --as-of 2026-03-13 --output /tmp/cal.json
```

The calendar is the one module that gets *better* on a historical run: because the schedule
is static and the reactions come from bars, an as-of run knows exactly which events had
landed by that date and what the market did on each, with no look-ahead. Events after the
date come back as `upcoming` with no outcome attached — which is precisely the "what was the
setup going in" framing a historical briefing wants.

**And search for that date, not for today.** WebSearch defaults to recent results, so a
historical run needs the date in the query: "stock market March 13 2026", "why did stocks fall
March 13 2026", "Fed CPI news week of March 9 2026". A briefing whose tables are from March but
whose narrative is this week's news is worse than no narrative — check the datelines on what
comes back and drop anything published after the as-of date.

**What is unavailable on a historical run**, to be reported as missing rather than filled in:

- **The live quote overlay.** Prices are that day's close, full stop. `live_overlay` is absent
  and the header should say "close" not "intraday".
- **The earnings calendar.** yfinance only knows the *next* earnings date as of now; there is no
  way to ask what was upcoming back then. The script sets `earnings_calendar_note` and leaves
  `next_earnings` null. Do not substitute the earnings date you can look up today — that is
  look-ahead. Getting the actual then-upcoming date needs the EDGAR panel
  (`evt.earnings_event.expected_date`, see the `earnings-drift` skill), not this script.
- **Ex-dividend dates** are capped at the as-of date, so what you get is the most recent past
  one, not an upcoming one.
- **Deep-history coverage.** Several funds postdate the early bars — RSP (2003), SMH (2000),
  XLRE (2015), XLC (2018). They appear in `unavailable_symbols`, `breadth.basis` reports the
  real denominator (e.g. "9 of 11 SPDR sector ETFs"), and `coverage_warning` fires when more
  than a third are missing. Quote breadth against the count that actually loaded.
- **News depth.** Massive's news archive is far shorter than its bar history and `insights`
  sentiment only rides on more recent articles, so an as-of run a few years back can return
  zero scored articles. That is a real "unavailable", not a bug to work around.

Postgres covers **2003→present**. Earlier dates fail the coverage check; under `--source auto`
the script then falls back to yfinance, which serves the big ETFs deep but not funds that had
not launched — read `unavailable_symbols` before trusting anything from that path. A future
date is rejected outright; today's date collapses to a normal live run.

## How to run

### Step 1: Install dependencies

```bash
pip install "yfinance>=1.5" pandas numpy scipy --break-system-packages -q
```

**Pin `yfinance>=1.5`.** Older versions (0.2.x) fail against Yahoo's current API with a
misleading `JSONDecodeError`/429 and return empty frames for every ticker.

### Step 2: Determine the mode and the date

Mode:

- Tickers named in this message, or carried over from earlier in the conversation → **watchlist mode**
- No ticker anywhere → **market mode**
- "My stocks" / "my portfolio" / "my watchlist" with no ticker ever named → you do **not** know
  what they hold. Run market mode and ask which tickers they want tracked, rather than
  guessing or using an example ticker.

Date — independent of mode, so any combination is valid:

- No date mentioned → today, no `--as-of`. This is the overwhelmingly common case.
- A specific past day named ("on March 13", "last Friday", "the day of the Fed decision") →
  resolve it to `YYYY-MM-DD` and pass `--as-of` to **both** scripts. If resolving it needs a
  fact you don't have (which day a print landed on), search for the date first.
- A range or "over the last month" → **not** a date argument. The script reports one day; the
  1w/1m/3m/YTD columns already carry the trend. Answer from those rather than running the
  script repeatedly, unless the user actually wants specific separate days compared.
- An ambiguous date ("the 13th", no month; a day that could be either of two years) → pick the
  most recent reading, state which date you used in the briefing header, and move on.

### Step 3: Gather data — run modules in parallel where possible

Three phases: Phase 1 is news/sentiment, Phase 1b is the macro event calendar, Phase 2 is the
technical analysis script. **Launch all four in the same message** — `massive_news.py`,
`macro_calendar.py`, `market_analysis.py`, and the WebSearch calls — so they run
concurrently. WebSearch is still needed even with the scripts: it supplies the *why* behind
the day's move and the detail behind each event (what the Fed actually said, whether a print
beat or missed), which the calendar script deliberately does not guess at.

#### Phase 1: News & sentiment

**Preferred source: the bundled `massive_news.py` script.** The user's Massive (ex-Polygon)
plan covers `/v2/reference/news`, and every article carries an `insights` array of
`{ticker, sentiment, sentiment_reasoning}` — a real per-ticker scored aggregate, not a
qualitative read. Run it alongside the analysis script:

```bash
python /path/to/this/skill/scripts/massive_news.py --tickers NVDA MSFT --days 30 --output /tmp/news.json
python /path/to/this/skill/scripts/massive_news.py --market --output /tmp/news.json   # market mode
python /path/to/this/skill/scripts/massive_news.py --market --as-of 2026-03-13 --output /tmp/news.json
```

Per ticker it returns `score_10`, a `label` (Bullish … Bearish), positive/neutral/negative
counts, and the top headlines each with its `sentiment_reasoning`. Market mode returns the
unfiltered wire feed aggregated across all insights.

**Respect the `confidence` field.** Coverage density is wildly uneven: mega-cap tech gets
scored articles daily, while XOM or SPY can go a week with none. The script marks
`confidence: low` when fewer than 5 articles scored or the newest is >5 days old, and sets
`coverage_note`. When confidence is low, report the score as indicative and say how many
articles it rests on — never present a 2-article score as a sentiment reading. Do **not**
query the feed with an index ETF ticker in market mode; use `--market` instead, since
SPY-tagged coverage is thin and lags.

*There is no retail/social sentiment source.* Massive carries no social feed. Do not
substitute WebSearch and present it as community sentiment — if a briefing section would
need it, say the module is unavailable.

#### Phase 1b: Macro event calendar

**Source: the bundled `macro_calendar.py` script.** It carries the published FOMC/BLS/BEA
schedules as static tables and joins each past event to what the market actually did, from
`mkt.price_daily`.

```bash
python /path/to/this/skill/scripts/macro_calendar.py --output /tmp/cal.json
python /path/to/this/skill/scripts/macro_calendar.py --back-days 60 --forward-days 30 --output /tmp/cal.json
python /path/to/this/skill/scripts/macro_calendar.py --as-of 2026-03-13 --output /tmp/cal.json
```

Default window is 35 days back and 21 forward — "the month" plus the next three weeks.
Run it in **both** modes: in market mode the calendar often *is* the story, and in watchlist
mode it belongs in the shared Macro Overlay, never repeated per stock.

**Do not web-search for these dates.** They are published a year ahead and live in the
script. A search returns today's calendar regardless of `--as-of`, which silently breaks
every historical run. Search for what an event *said* (the vote split, whether a print beat),
never for when it happened.

**How to read the output:**

- **`events[]`** each carry `status` (`released` / `upcoming`), `covers` (the reference
  period — the Aug 12 CPI reports *July* data), `tier`, and for released events a `reaction`
  block with same-day SPY/QQQ/IWM/TLT/GLD/XLU/XLF moves plus `reaction_next_day`.
- **`rate_path`** is the derived read: did the market reprice the rate path. It leads on
  duration (TLT) and confirms with the XLF−XLU sector spread, and it reports when the two
  disagree rather than averaging them. Quote `rate_path.read` — it is written to be quoted.
- **`summary.rate_path_days`** counts hawkish vs dovish vs mixed days across the window;
  `summary.last_fomc_in_window` isolates the FOMC, which is the event that actually sets the
  path. `summary.next_high_importance` is what to lead the forward-looking section with.
- **A reaction is not a surprise.** There is no consensus/expectations data anywhere in this
  skill, so a small move may mean an in-line print *or* an offsetting news flow. Never write
  "the print was unremarkable" from a small reaction — say the market's response was muted,
  which is the thing actually measured. If you need beat/miss, that comes from WebSearch.
- **Respect `tier`.** `high` = official or two independent sources agreeing; `medium` =
  single secondary source (PPI, PCE — believe the month, confirm the day); `derived` = a rule,
  not a transcription (FOMC minutes at decision + 21 days). Say "scheduled" for high-tier and
  "scheduled, unconfirmed" for the other two.
- **`coverage_gaps`** means the window ran past what the tables verify. That is "the schedule
  is not known that far out", **not** "no events are scheduled" — never imply a quiet calendar
  from it. `reaction_note` distinguishes a session that has not settled yet (an event released
  today, before the close) from a genuine hole in the bar store; those must read differently.

The schedule was verified 2026-08-07 and covers FOMC through Dec 2027, the rest through Dec
2026. **Re-transcribe it each December** when the agencies publish the following year — the
dates are irregular (2026 jobs reports land on Wednesdays, Fridays and Thursdays; PPI skips
May), so they cannot be regenerated from a rule.

The legacy `mcp__market_news_sentiment__summarize_market_news` server, if it happens to be
connected, still works (`ticker` + `months: 1`). If neither it nor the news script is usable,
fall back to WebSearch and label the module web-search-derived and qualitative.

WebSearch queries that work well:

- *Market mode:* "stock market today [date]", "why did stocks fall today", "S&P 500 close
  today", "Fed decision [month year]", "CPI report reaction", "sector rotation this week".
  Always check for a Fed meeting, CPI/PCE/jobs print, or a major earnings reaction in the
  last 48 hours — these are usually the cause of whatever the tape did.
- *Watchlist mode:* "[TICKER] stock news [month year]", "[TICKER] earnings date",
  "[TICKER] analyst price target".

#### Phase 2: Technical analysis script

Run the bundled Python script for the quantitative modules:

```bash
# Market mode — omit --tickers entirely
python /path/to/this/skill/scripts/market_analysis.py --output /tmp/market_intel_data.json

# Watchlist mode
python /path/to/this/skill/scripts/market_analysis.py --tickers NVDA MSFT --output /tmp/market_intel_data.json

# Both — per-stock modules plus the market-wide block
python /path/to/this/skill/scripts/market_analysis.py --tickers NVDA --market --output /tmp/market_intel_data.json

# Any of the above, as of a past date's close
python /path/to/this/skill/scripts/market_analysis.py --as-of 2026-03-13 --output /tmp/market_intel_data.json
```

Replace `/path/to/this/skill` with the actual skill directory path. Pass the tickers the user
named — there is no default list to fall back on.

`--tickers` is optional. With it omitted the script sets `mode: "market"` and emits a
`market` block (indices, sectors, breadth, risk_ratios, safe_havens) instead of per-ticker
analysis. With tickers it sets `mode: "watchlist"`. `--market` forces the market block on in
watchlist mode.

**Data source (`--source auto|pg|yf`, default `auto`).** History comes from
**Postgres `trading` → `mkt.price_daily`** on `localhost:5433` — 49M+ bars, ~36k tickers,
2003→present, full OHLC + vwap + volume, plus `mkt.dividend`. Far faster than yfinance and carries enough
history that the **200-day MA and sector relative performance actually populate** (the
yfinance path often leaves them null on a 250-day window).

- `auto` (default) — Postgres for history, plus 1–2 small yfinance calls for today's quote,
  the earnings date, and the macro indices. Falls back to full yfinance if Postgres is
  unreachable or stale.
- `pg` (alias `db`) — same, but hard-fails instead of falling back.
- `yf` — original all-yfinance behaviour.
- `--no-live` — zero network calls; macro degrades to ETF proxies.

There is no local-file source any more. The legacy `massive_daily.db` cache was removed in the
Aug-2026 cutover; Postgres is the only bar store, and `massive_ingest.py` writes only there.

**If the bars are stale, refill them — don't just fall back.** The script prints the fix:
`python "C:\Users\ssair\s&p Historic Data\massive_ingest.py" pull`. It is resumable and takes
about ten seconds per trading day. Two guards fire:
- **Staleness** — refuses bars older than 7 days rather than computing a 50-day MA on stale data.
- **Breadth** — refuses a latest day carrying under 5,000 tickers. A real grouped-daily pull
  lands ~12,400; a few hundred means some other job wrote a partial S&P-only day, and **every
  ETF the market module needs will be missing**. `db_status.last_bar_breadth` records it.

**Identity, not ticker strings.** The Postgres loader resolves each ticker to a `security_id`
as of the latest bar date and queries by that id. 173 tickers denote more than one company
across time; joining on the ticker string splices two companies together and manufactures a
price discontinuity. Do not "simplify" that query.

**Schema — the column names are not the obvious ones.** Writing a query from the names you'd
guess (`ticker`, `date`) fails with `UndefinedColumn`. The actual columns:

```
mkt.price_daily   security_id (int), obs_date (date), close (float8), volume (float8)
mkt.dividend      dividend_id (int8), security_id (int), ex_date (date),
                  cash_amount (float8), pay_date (date), freq (int)
ref.security      security_id (int), primary_ticker (text), issuer_cik (text),
                  name (text), sector (text), first_seen (date), last_seen (date),
                  confidence (text)
```

Note `obs_date` **not** `date`, and `primary_ticker` **not** `ticker`. Historical ticker→id
mapping lives in `ref.ticker_span` (`ticker`, `valid` daterange, `security_id`, `confidence`),
reached through the `ref.resolve` accessor:

```sql
-- ticker -> security_id (NULL only if the ticker is unknown to ref.security)
SELECT ref.resolve('QQQ', DATE '2026-08-06');

-- a clean single-identity price series
SELECT p.obs_date, p.close, p.volume
FROM   mkt.price_daily p
WHERE  p.security_id = ref.resolve(%s, %s)
  AND  p.obs_date BETWEEN %s AND %s
ORDER  BY p.obs_date;
```

`ref.security.primary_ticker` is the *current* ticker for that id — fine for labelling output,
wrong for looking a security up on a past date. Use `ref.resolve` for that. (`ref.split_identity`
is the companion function that records where one ticker's history splits into two ids.)

**A null price series can come from either of two layers — know which.** `ref.resolve` is
date-gated only where the span has real boundaries: the ~1,280 `cik_verified` and 13
`price_break` spans in `ref.ticker_span`. The ~35,145 `assumed` spans are unbounded, so resolve
returns an id for *any* date and the time-partitioning falls to `mkt.price_daily` instead.

QQQ is the worked example of the second case. Both spans are unbounded/`assumed`, yet the bars
partition cleanly: id `69376` (QQQ) holds 2003-09-10→2004-11-30 and 2011-03-23→present, while
id `66826` (QQQQ) holds exactly the gap, 2004-12-01→2011-03-22. Zero overlap. So an
`--as-of 2008-06-30` run resolves QQQ fine, gets **no bars back**, and reports it in
`unavailable_symbols` — the correct outcome, reached one layer later than you'd guess.

Either way the fix is never a ticker-string join. An empty series means the security wasn't
trading under that ticker then; splicing is exactly what the design prevents. For the full
identity model — span `confidence` values, the GiST overlap constraint, the 13 reused tickers —
see the `pg-skill` reference at `.claude/skills/pg-skill/references/data-model.md`, which is
the authority on this schema. Prefer reading it over re-deriving the model here.

**Store limits, which the briefing must respect:**
- **Prices are split-adjusted only, not total-return.** yfinance's `auto_adjust=True` series
  is dividend-adjusted too, so long MAs differ slightly between sources (SPY 200-day: 699.5
  from Postgres vs 696.5 from yfinance, ~0.4%). Both are correct on their own basis — just
  don't mix the two in one table or attribute the gap to a data error.
- **T-1, or T-0 after the close.** Bars land once the grouped-daily pull runs for that day.
  In `auto` mode the script overlays today's quote from yfinance and sets `live_overlay: true`;
  check the `as_of` field and say which day the price is from.
- **Full daily OHLC since 2026-08-06**, backfilled to 2003 — `mkt.price_daily` carries
  `open/high/low/close/vwap/volume/trades`, so ATR, true range, overnight gaps and
  wick-based levels are all computable from daily bars. Two limits stand: the loader only
  attaches `Open`/`High`/`Low` when **every** bar in the window has them (a partly-filled
  window comes back Close-only, so check before reaching for a range), and daily bars still
  say nothing about the intraday *path* — no opening range, no sequence within the session.
- **No index symbols.** `^VIX`/`^TNX`/`DXY` are absent, and this is an **entitlement limit,
  not a gap in the ingest**: `/v3/snapshot/indices` and `I:VIX` aggregates return
  `403 NOT_AUTHORIZED` on the current plan (Indices is a paid add-on). Macro comes from
  yfinance, which serves them reliably. If that fails the script substitutes ETF proxies
  (`IEF`/`VIXY`/`UUP`) and sets `macro_is_proxy: true` — when that flag is set, report
  **direction only** and state that the actual index level is unavailable.

The script outputs a JSON file with:

- `mode` — `"market"` or `"watchlist"`
- `date` — the day the report describes; equals `as_of_requested` on a historical run
- `historical` / `as_of_requested` / `historical_note` — present only with `--as-of`. When
  `historical` is set, the briefing header must name the date and say the prices are that
  day's close, and no module may report a live quote or an earnings date.
- `macro` — snapshot (^TNX for yields, ^VIX, DX-Y.NYB for dollar)
- `market` (market mode, or `--market`) — `indices`, `sectors` (each with `vs_spy_1d/1w/1m`),
  `constituent_breadth`, `breadth`, `risk_ratios`, `safe_havens`, and `unavailable_symbols`
  for anything that failed to load
- `tickers` (watchlist mode) — per stock: technical indicators (RSI, MAs, MACD, volume
  z-score), volatility alert flags, sector comparison (`rel_perf_1w`/`rel_perf_1m`),
  correlation with SPY and sector ETF, upcoming earnings/dividend dates

Two breadth blocks, measuring different things — quote both and never conflate them:

- `constituent_breadth` is the **real advance/decline line**, computed over the ~500
  point-in-time index members straight from Postgres: `advancing`/`declining`,
  `advance_decline_ratio`, `pct_above_50dma`, `pct_above_200dma`, `new_52w_highs`/`lows`,
  and `median_member_return` vs `mean_member_return`. Lead with this one. Membership is
  point-in-time, so a `--as-of` run counts the names in the index *then*.
- `breadth` is **sector participation** — how many of the 11 SPDRs advanced. Coarse by
  construction. Never call it an advance/decline line.

Where they disagree, the gap is the story: 7-of-11 sectors green while only 40% of members
advance is a narrow tape wearing an index-wide costume. `median_member_return` below the
index return says the same thing in one number — cap-weighted strength the typical stock
is not sharing. And mean below median means the decliners are the bigger movers.

`constituent_breadth` is absent (not zeroed) if Postgres is unreachable — say it is
unavailable rather than falling back to the sector count and calling it breadth.

### Step 4: Synthesize the briefing

Combine the Phase 1 news and the script output into a structured briefing. Use the market
template or the watchlist template below, depending on mode. In both, lead with what changed
and why — not with a table.

---

## Market-mode template

# Market Intel — [Date]

[On an `--as-of` run, retitle: "# Market Intel — [Date] (historical)" and add one line under
it: "Point-in-time briefing for [date]'s close. Nothing after that date is used." Then write
the whole thing in the past tense.]

**S&P 500 [+/-]X.X% · Nasdaq 100 [+/-]X.X% · Dow [+/-]X.X% · Russell 2000 [+/-]X.X% · VIX XX.X**

[Two or three sentences on what actually happened and the reason, from the Phase 1 searches.
Name the driver — a Fed decision, a CPI print, a mega-cap earnings reaction, a yield move.
If the cause is genuinely unclear from the sources, say that instead of inventing a narrative.]

### Index Scoreboard
| Index | Close | Today | 1W | 1M | YTD | RSI | vs 50/200 MA |
|-------|-------|-------|----|----|-----|-----|--------------|

### Sector Rotation
[All 11 sectors ranked by today's move, with the `vs_spy_1w` / `vs_spy_1m` columns. Then one
or two sentences naming the rotation: what is being bought, what is being sold, and whether
that is consistent with the macro backdrop.]

### Breadth & Risk Appetite
[Lead with the constituent advance/decline line: N advancing / N declining, share above the
50- and 200-day MAs, new 52-week highs vs lows. Then the sector-participation count, then the
risk ratios. Flag the important case explicitly: a headline index fall with breadth holding up
is a narrow-leadership unwind, not broad de-risking — and the reverse is far more bearish than
the index level suggests. If the index is up while the median member is down, say so plainly;
that divergence is the single most useful number in this section.]

### Macro & Volatility
| Indicator | Value | 1W change | Read |
|-----------|-------|-----------|------|
| 10Y Yield | X.XX% | [+/-]X.X% | [hawkish/dovish] |
| VIX       | XX.X  | [+/-]X.X% | [Low/Moderate/Elevated/High] |
| DXY       | XXX.X | [+/-]X.X% | [strong/weak dollar] |
[Plus safe havens (TLT/GLD/UUP).]

### Macro Event Calendar
[From macro_calendar.py. Two halves — what landed, then what's next.

**What landed** — a table of released events in the window with the realized reaction:

| Date | Event | Covers | SPY | TLT | Rate-path read |
|---|---|---|---|---|---|

Lead the prose with the FOMC if one is in the window; it sets the path and everything else
is data feeding into it. Then connect the events to the sector table above — if utilities
and REITs are the month's worst and the last FOMC read hawkish on duration, that is one
story, not two, and saying so is the single most valuable sentence in the briefing.

**What's next** — the upcoming events with `days_away`, leading with
`summary.next_high_importance`. Say what each one could resolve, not just when it lands.
Mark medium/derived-tier dates as unconfirmed.

If `coverage_gaps` is set, say the schedule is unverified past that date — never that the
calendar is empty.]

---

## Watchlist-mode template

# Market Intel Briefing — [Date]

[Same as market mode on an `--as-of` run: mark the title "(historical)", state that prices are
that date's close, and drop the Earnings & Events module to a single line saying the calendar
is unavailable for a past date.]

## Watchlist: [TICKER1, TICKER2, ...]

---

### [TICKER] — [Company Name]

**Price:** $XXX.XX ([+/-]X.X% today) | **Volume:** X.XM (X.Xx avg)

#### News & Sentiment
[Summarize the key headlines from the MCP news tool. Lead with the most market-moving story.
Include the overall sentiment score — e.g., "Sentiment: Moderately Bullish (7/10)"]

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

[Brief macro narrative: "Markets are pricing in...", "The Fed's recent...", etc.]

**Macro event calendar** (from macro_calendar.py — once, here, never per stock):
[The month's released events with their realized reactions, then what's upcoming with
`days_away`. In watchlist mode keep this tight — two or three lines plus the next event —
and make it earn its place by tying it to the holdings: a rate-sensitive book cares that
the last FOMC read hawkish on duration in a way a semis book does not. Flag any upcoming
high-importance event that lands before the next earnings date for a name in the watchlist,
since that is the one that can overwrite a single-stock thesis.]

### Sector Heatmap
[For each stock, show how it's performing relative to its sector ETF over 1-week and 1-month
windows. Flag any notable outperformance or underperformance.]

### Correlation Monitor
[Flag any stocks whose rolling 30-day correlation with SPY or their sector ETF has shifted
significantly (>0.3 change). This can signal regime changes or idiosyncratic events.]

---

## What This Means For You

[Both modes end here, and it is the most important section. Write 2-4 bullets that synthesize
the briefing into something actionable. Be specific, cite the number you are reasoning from,
and frame it as what to DO or WATCH — not a restatement of what happened.

*Market mode* — talk about the tape, positioning and the calendar:
- "The index fall is narrow: QQQ -6% on the week while equal-weight RSP is *up* 1.4% and 9 of
  11 sectors are above their 200-day. This is a mega-cap/semis unwind, not broad de-risking —
  index-level shorts are fighting decent breadth."
- "VIX at 20.7 and up 10% on the week, with the 10Y falling — that combination is growth-scare
  pricing rather than an inflation scare. The next CPI print is the thing that resolves it."

*Watchlist mode* — tie the stock to its sector and the macro:
- "NVDA is +9% vs XLK over the month but its 30-day correlation to the sector has dropped 0.5 —
  it is trading on its own news now, so sector hedges will track it poorly."
- "News sentiment is moderately bullish but rests on only three scored articles, the newest
  four days old — that is not a read on today. The technicals are the better guide here."

Do not manufacture an insight when the data is unremarkable. "Quiet tape, nothing actionable"
is a legitimate and useful conclusion.]

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
  (Fed announcements, CPI releases, geopolitical events). In market mode this is not optional —
  the "why" of the day's move comes from here, and a briefing that reports moves without the
  driver is half a briefing. Always check whether a Fed meeting, CPI/PCE/jobs print, or major
  earnings reaction landed in the last 48 hours.

- **Timeliness**: Market data from yfinance may be delayed 15-20 minutes for some tickers.
  Note this in the briefing header if running during market hours. A `change_pct` pulled
  mid-session is an intraday snapshot, not a close — label it as such. On an `--as-of` run
  the opposite applies: every number is a settled close for that date, so say "close" and
  drop the delay caveat.

- **Write a historical briefing in the past tense, and don't leak the present into it.**
  The reader wants to know what that day looked like *then*. Everything you know about what
  happened afterwards — how the move resolved, what the stock did since — is look-ahead and
  does not belong in the briefing body. If it is genuinely useful, put it in one clearly
  separated line at the end ("For reference, since that date: …"), never woven into the
  analysis. "What This Means For You" is the one section that legitimately changes shape on a
  historical run: there is no position to take on a past day, so use it to draw out what the
  setup was and what it went on to teach, rather than issuing stale advice.

- **This is a daily-bar tool, not an intraday one.** Everything is computed from daily bars.
  Those bars now carry OHLC, so ATR, true range and overnight gaps are fair game — but there
  are still no intraday bars and no futures, so the opening range and anything about the
  *path* within a session remain invisible. If asked for an intraday or day-trading read, say
  what the tool can't see rather than approximating it from daily data.

- **Report missing data as missing.** If `unavailable_symbols` is non-empty, a module's inputs
  failed to load, or the MCP sentiment server is absent, say so in that section. Never fill
  a gap with a related symbol, a stale value, or an estimate.

- **A failed fetch is not a zero.** "The source returned nothing for this ticker" and "the
  source refused the request" must read differently in the briefing. Silence about a name is
  a finding; an outage is not. The same discipline the daily job applies to stale bars
  applies to every module here.

---

## Telemetry (standing requirement — all skills)

Log this run **once, at the very end**, whether it went well or not (Bash tool; forward slashes):

```bash
python C:/Users/ssair/.claude/telemetry/telemetry.py log --skill smarket-intel \
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
