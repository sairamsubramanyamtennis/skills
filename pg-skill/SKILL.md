---
name: pg-skill
description: Inventory and explain the local PostgreSQL `trading` database — the S&P 500 point-in-time membership panel, the 49M-row daily price spine, EDGAR earnings dates, and the Quantitative Momentum screen/backtest results. Use this skill whenever the user asks what is in their database, what tables or schemas exist, how much history a table covers, where some data lives, what a column means, how the pieces fit together, or wants help writing a query against it — and equally for casual phrasings like "what data do I have", "show me my tables", "explain my dataset", "how far back do prices go", "is the DB up to date", "where are the QM results stored", "how do I get the S&P members on a date", or a bare SQL question about trading/price/screen data. Also use it before writing any code that reads or writes this database, since it carries the identity rule (never join on a ticker string) that silently corrupts results when ignored.
---

# The `trading` database

One PostgreSQL 18 database on **localhost:5433** (PG 17 sits on 5432 — connecting
to the default port silently reaches the wrong server). It replaced eleven
separate SQLite files in July 2026. Password comes from
`%APPDATA%\postgresql\pgpass.conf`; never hardcode it or ask the user to type it.

```python
import sys; sys.path.insert(0, r"C:\Users\ssair\trading-db")
import pgdb                      # the house adapter: connect, resolve_bulk, upsert
with pgdb.connect() as pg: ...
```

```
psql -h localhost -p 5433 -U postgres -d trading
```

## Start by looking, not guessing

Run the bundled inventory before answering anything about scale, coverage or
freshness. It reports every object with row count, size and the date span it
covers, so the answer comes from the database rather than from memory of how it
looked last week:

```
python <skill>/scripts/inventory.py --checks
python <skill>/scripts/inventory.py --schema res --columns   # one schema, full columns
python <skill>/scripts/inventory.py --json                   # machine-readable
```

Counts are planner estimates by default (instant); `--exact` forces `count(*)`,
which is a seconds-long scan on the 49M-row price table. `--checks` runs six
integrity probes, each guarding an invariant this workspace has broken at least
once — orphan prices, results with no provenance row, and how many tickers
currently denote more than one company.

## What the data actually is

Two layers. The market layer is ground truth; the research layer is everything
computed on top of it, and it is only as good as its declared provenance.

### Layer 1 — the market

**Who was in the S&P 500, on every day, and what everything traded at.**

`ref.index_membership` holds membership as ~1,270 **intervals** (`security_id`,
`daterange`), not as millions of dense daily rows — so "who was in the index on
2015-06-15" is an interval containment query, and the answer is what was true
*then*, not what is true now. This is the point-in-time universe that keeps a
backtest honest; screening today's index members over 2006 data is the
survivorship bias that inflated this workspace's early QM results roughly 3x.
`ref.index_member_daily` is the dense view derived from those intervals, so it
can never drift out of sync with them.

`mkt.price_daily` is the price spine: ~49.3M split-adjusted daily closes and
volumes covering the whole US market from 2003-09-10 to today, **including
delisted names**. That last property is why it exists — the free survivor-only
panels it replaced were missing ~366 of 1,202 ever-members, and every backtest
run on them read too high.

`mkt.sp500_panel` is a materialized view of the same prices **filtered to actual
membership** — 2.77M member-days. Prefer it for anything index-related: it
cannot overstate coverage, because a row only exists where the security really
was in the index that day. Refresh it after any identity change with
`REFRESH MATERIALIZED VIEW CONCURRENTLY mkt.sp500_panel;`.

Prices are **split-adjusted only, not dividend-adjusted** — these are price
returns. `mkt.dividend` and `mkt.split` are there to reconstruct total return,
but nothing in the database does so yet, so never compare a figure from here to
a total-return benchmark without saying which basis you used.

`evt.earnings_filing` / `evt.earnings_event` add ~65k EDGAR announcement dates
back to 2004. Each event carries both `filed_date` (what actually happened) and
`expected_date` (what was projectable beforehand). Any strategy must trade off
`expected_date`; using `filed_date` is look-ahead.

### Layer 2 — the QM research

Quantitative Momentum (Wes Gray / Alpha Architect): rank S&P 500 members by 6-1
month momentum and by FIP, a "how smooth was that climb" quality score, then hold
the top names. `res` stores what those runs produced.

`res.run` is one row per screen or backtest, and it is the reason to trust or
distrust everything under it. `universe` and `data_asof` are **NOT NULL by
design**: a result cannot be stored without declaring whether it used
point-in-time membership and what its data cutoff was. Current runs:

| label | kind | what it is |
|---|---|---|
| `qm_panel_v2` | screen | the main panel — reconstructed 2004→2022 plus every live screen since. `res.latest_screen` and `res.top10_daily` are hardwired to it |
| `qm_panel_v1` | screen | an earlier 2016-2026 reconstruction, kept for comparison |
| `persistence` | backtest | rank by how long a name has *stayed* in the top decile |
| `qm_static` | backtest | plain QM rank, the comparison arm for persistence |
| `gated_n10/15/20` | backtest | QM + a 200-DMA risk-off gate, one run per holding count |

`res.screen_result` is every screen row ever produced (~396k). Its `obs_date`
crossing **2022-02-15** is a seam that matters: before it, rows are *replayed*
screener math over historical prices; after it, they are screens that actually
ran that morning. Rank correlation across the overlap is 0.995-1.0, but a claim
that straddles the seam should say so.

`res.backtest_period` holds per-rebalance returns with SPY and RSP alongside, so
excess return is computed on a matched basis. `res.backtest_selection` records
what was actually held on each date, and `res.holding_snapshot` the latest set.

The honest headline, so nobody re-derives an inflated one: raw QM underperforms
SPY by ~1.2pp/yr over 2004-2026, and the persistence variant by ~0.9pp. What
survives is a conditional risk-on selection tilt, not an index-beater.

### The other two schemas

`etl` is pipeline bookkeeping (watermarks, the staging manifest, scraped news).
`stg` holds **verbatim copies of the original SQLite tables**, kept only so the
migration can be re-verified; it is droppable (`DROP SCHEMA stg CASCADE`, ~3.3
GB). Never build anything on `stg` — read the modelled tables.

## The one rule: never join on a ticker string

213 tickers currently denote more than one company across time. `ABX` is Barrick
Gold until 2025 and Abacus Global after. `NOW` was a Morgan Stanley note, then an
AIG MITTS, then ServiceNow. `MS` before 2006 is a penny instrument, and joining
through it once produced a +4925% monthly return that looked like alpha.

Every fact table keys on `security_id`. Resolve a ticker **at a date**:

```sql
SELECT ref.resolve('ABX', DATE '2015-01-01');   -- Barrick
SELECT ref.resolve('ABX', DATE '2026-01-01');   -- Abacus
```

```sql
-- a ticker's price series, identity-correct
SELECT p.obs_date, p.close
FROM mkt.price_daily p
JOIN ref.ticker_span t ON t.security_id = p.security_id AND p.obs_date <@ t.valid
WHERE t.ticker = 'AAPL'
ORDER BY p.obs_date;
```

`ref.ticker_span` carries a gist `EXCLUDE` constraint, so the database will
*reject* an attempt to make one ticker mean two securities on one date. Two more
things it encodes: punctuation aliases (the screener writes `BRK-B`, canonical is
`BRK.B`; both resolve to the same security), and `confidence`, which says why a
boundary is where it is — `cik_verified`, `assumed`, `price_break`, `alias`.

Also worth holding onto: `ref.security` is per **listing**, not per issuer, so
GOOG and GOOGL are separate securities sharing an `issuer_cik`.

## Which table answers which question

| Question | Table |
|---|---|
| Who was in the S&P on date D? | `ref.index_membership` with `D <@ valid`, or `ref.index_member_daily` |
| What did X close at? | `mkt.price_daily` joined through `ref.ticker_span` |
| Index-only price work, survivorship-free | `mkt.sp500_panel` |
| Today's screen | `res.latest_screen` |
| A name's rank history | `res.screen_result` + `ref.resolve` |
| How a backtest performed | `res.backtest_period` |
| When does X report? | `evt.earnings_event.expected_date` |
| Was this result point-in-time? | `res.run.universe` / `data_asof` |

## Traps

- **`res.screen_result.price` is not a price series.** It is the screener's own
  unadjusted column, NULL across 2026-03-14→04-23 and carrying bad ticks (KLAC
  printed 1869.19 where the real close was ~184.52). Compute returns from
  `mkt.price_daily`, never from this.
- **`universe='unknown'` on all seven current runs** is deliberate — the flag was
  not recoverable for legacy imports. New runs should write `'pit'` (point-in-time
  membership) or `'current'` (today's index list). Do not backfill a guess.
- **Estimated vs exact counts.** `reltuples` drifts between vacuums; if a number
  is going into a report, use `--exact`.
- **Dates are real `date` columns**, not the text they were in SQLite. Compare
  with `DATE '2026-06-01'` or `CURRENT_DATE`, and use `<@` for ranges.
- **Freshness has two clocks.** `run_qm.py` publishes a screen each weekday
  morning; the price ingest runs separately. Prices being a day ahead of the
  newest screen is normal, not a fault.

## Deeper reference

`references/data-model.md` — table-by-table columns, the full run/provenance
model, the identity-break history (the 13 price-break splits), and a set of
worked query recipes (coverage by year, top-10 with next earnings date,
persistence vs static head to head). Read it when a question needs more than the
orientation above, or before writing a non-trivial query.

---

## Telemetry (standing requirement — all skills)

Log this run **once, at the very end**, whether it went well or not (Bash tool; forward slashes):

```bash
python C:/Users/ssair/.claude/telemetry/telemetry.py log --skill pg-skill \
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
