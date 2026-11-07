# `trading` — table-by-table reference

Read this when the orientation in SKILL.md is not enough: before writing a
non-trivial query, when a column's meaning is unclear, or when a result looks
wrong and the cause might be identity or provenance rather than arithmetic.

Contents:
1. [ref — identity and the universe](#1-ref--identity-and-the-universe)
2. [mkt — prices and corporate actions](#2-mkt--prices-and-corporate-actions)
3. [evt — earnings](#3-evt--earnings)
4. [res — research results](#4-res--research-results)
5. [etl and stg](#5-etl-and-stg)
6. [Identity breaks: the history](#6-identity-breaks-the-history)
7. [Query recipes](#7-query-recipes)
8. [Writing to this database](#8-writing-to-this-database)

---

## 1. `ref` — identity and the universe

### `ref.issuer`
`cik`, `name`. One row per EDGAR filer — the company, not the listing.

### `ref.security`
`security_id` (identity, the key every fact table uses), `primary_ticker`,
`issuer_cik`, `name`, `sector`, `first_seen`, `last_seen`, `confidence`.

One row per **listing**. Dual-class lines (GOOG/GOOGL, BRK.A/BRK.B) share an
`issuer_cik` but are separate securities, which is correct: they have different
prices and can enter the index independently.

`sector` and `name` are populated for the securities that have appeared in a
screen and are NULL for much of the 36k-row long tail. `qm_pg.py` fills them in
(COALESCE only, never overwriting) as new screens are published, so coverage
improves over time. Do not assume a NULL sector means anything about the security.

### `ref.ticker_span`
`ticker`, `valid` (daterange), `security_id`, `confidence`.

The identity table. A ticker string means a security **only within a date range**.
`EXCLUDE USING gist (ticker WITH =, valid WITH &&)` makes an overlap physically
unstorable, so the database itself refuses to let one ticker mean two things at
once.

`confidence` tells you why a boundary sits where it does:

| value | meaning |
|---|---|
| `cik_verified` | boundary proven by a CIK change in EDGAR (~1,280 spans) |
| `assumed` | no evidence; one lifetime assumed (~35,145 spans) |
| `price_break` | boundary proven by a price discontinuity + data gap (13 spans) |
| `alias` | punctuation variant, e.g. `BRK-B` -> `BRK.B` (2 spans) |

`ref.resolve(ticker, date) -> security_id` is the accessor. It is a plain SQL
function over this table, so it is cheap and inlinable.

### `ref.index_membership`
`index_code`, `security_id`, `valid` (daterange). ~1,270 interval rows.

`index_code` is `'SP500'` today; adding Russell needs rows, not a schema change.
Intervals rather than dense rows means membership questions are containment
queries:

```sql
SELECT s.primary_ticker
FROM ref.index_membership m
JOIN ref.security s USING (security_id)
WHERE m.index_code = 'SP500' AND DATE '2015-06-15' <@ m.valid;
```

### `ref.index_member_daily`
Dense view derived from the intervals, expanded over trading days:
`index_code`, `obs_date`, `security_id`, `ticker`. Convenient for joins; it can
never disagree with the intervals because it is computed from them.

Note it expands over **trading days only**. A membership interval covering a
Saturday yields no row for that Saturday — that is expected, not a gap.

### `ref.trading_day`
The market calendar (~6,144 rows). Use it to align rebalance dates and to roll a
date back to the prior session.

---

## 2. `mkt` — prices and corporate actions

### `mkt.price_daily`
`security_id`, `obs_date`, `close`, `volume`. ~49.3M rows, 2003-09-10 → today.

Split-adjusted, **not** dividend-adjusted: price return only. Whole US market
(~36k securities), delisted names included — the property that makes
survivorship-free work possible.

Indexed on `(security_id, obs_date)`. Filter by security and it is instant; a
bare date-only filter scans.

A handful of rows (3,525) were recovered from secondary panels where the primary
source had no bar. That is intentional, not duplication.

### `mkt.sp500_panel` (materialized view)
`security_id`, `ticker`, `obs_date`, `close`, `volume`. 2.77M rows.

`price_daily` ∩ actual index membership on that day. Use this for anything
index-scoped: because a row exists only where the security really was a member,
a coverage statistic computed on it cannot overstate. The predecessor SQLite
panel kept full history for every *ever*-member (4.51M rows), which was fine as a
source and dangerous when queried unfiltered.

Refresh after any identity change:
`REFRESH MATERIALIZED VIEW CONCURRENTLY mkt.sp500_panel;`

### `mkt.dividend`
`dividend_id` (surrogate PK), `security_id`, `ex_date`, `cash_amount`,
`pay_date`, `freq`.

Uniqueness is `(security_id, ex_date, cash_amount, freq)` — **not**
`(security_id, ex_date)` — because a regular and a special distribution routinely
share an ex-date (ADT on 2019-12-12: 0.035 quarterly + 0.70 special). `freq = 0`
means special/one-time. Upsert on the four-column key, never on the pair.

Coverage is partial (~849 of the 1,202-name S&P union), so total return is
reconstructible for those and no others.

### `mkt.split`
`security_id`, `ex_date`, `split_from`, `split_to`.

Note the bars are already split-adjusted; this table is for reasoning about
events, and for detecting **split-vintage mixing** — two price series adjusted as
of different dates, which produces impossible returns. `res.split_vintage_check`
holds the current findings; re-run it after a rebuild.

---

## 3. `evt` — earnings

### `evt.earnings_filing`
`filing_id`, `security_id`, `cik`, `filed_date`, `accepted_utc`, `accepted_et`,
`session`, `items`, `accession`. ~76k 8-K filings.

### `evt.earnings_event`
`event_id`, `security_id`, `cik`, `seq`, `filed_date`, `expected_date`,
`gap_days`, `session`, `accession`. ~65k announcements, 2004 → today.

`expected_date` is projected from each firm's **own prior cadence**, so it is
knowable in advance; `filed_date` is what happened. `gap_days` is the difference
— the Chambers-Penman "did they report late" signal (mean ≈ −1.85 days).

Any backtest must key on `expected_date`. Vendor calendars silently revise
historical dates; this panel is EDGAR's own filing record, which does not.

---

## 4. `res` — research results

### `res.run`
`run_id`, `kind` (`screen`|`backtest`), `strategy`, `label`, `params` (jsonb,
GIN-indexed), `universe` (`pit`|`current`|`unknown`), `data_asof`, `code_version`,
`source_note`, `created_at`.

`universe` and `data_asof` are NOT NULL on purpose: a result cannot enter this
database without declaring whether it used point-in-time membership and where its
data stopped. Legacy imports are marked `'unknown'` deliberately — that is an
honest missing value, not an oversight, and should not be backfilled with a guess.

`params` holds the modelling parameters at the top level and the descriptive
metadata (built_at, span, headline CAGR/Sharpe, the analyst note) under
`params->'meta'`, copied from the original SQLite `*_meta` tables by
`qm-results/qm_pg_meta.py`.

```sql
-- every run with fip_weight > 0.3 that used point-in-time membership
SELECT label, params, data_asof FROM res.run
WHERE (params->>'fip_weight')::float > 0.3 AND universe = 'pit';
```

### `res.screen_result`
`run_id`, `obs_date`, `security_id`, `rank`, `percentile`, `mom`, `ret1m`,
`ret3m`, `fip`, `fip_pctpos`, `fip_r2`, `momrank`, `fiprank`, `qmscore`,
`mompctile`, `price`, `signal`. PK `(run_id, obs_date, security_id)`.

Column meanings:

| column | meaning |
|---|---|
| `mom` | 6-1 month return, volatility-adjusted |
| `fip` | Frog-in-the-Pan quality: how *smoothly* the gain was earned |
| `fip_pctpos` | share of positive days |
| `fip_r2` | R² of the cumulative return path (trend smoothness) |
| `qmscore` | composite rank; at the production FIP weight of 1.0 this *is* the FIP rank |
| `percentile` | 100 = best |
| `signal` | ≥90 Strong Buy, ≥70 Buy, ≥30 Hold, else Sell |
| `price` | the screener's own unadjusted column — **do not compute returns from it** |

The `qm_panel_v2` run spans 2004-04-01 → today. Rows before **2022-02-15** are
reconstructed (the screener's math replayed over historical prices); rows from
that date are live screens that ran that morning. Both are legitimate; a claim
straddling the seam should say which side it rests on.

### `res.backtest_period`
`run_id`, `d0`, `d1`, `ret`, `spy_ret`, `rsp_ret`, `n_holdings`, `in_cash`,
`reason`. One row per rebalance period.

SPY and RSP are stored alongside so excess return is computed on a matched basis.
Costs are already netted into `ret` by the script that produced the run — do not
subtract them again.

### `res.backtest_selection`
`run_id`, `obs_date`, `slot`, `security_id`, `persist`, `percentile`, `ret3m`,
`fip`, `fwd_ret`, `spy_ret`. What was actually held, per date and slot, with the
realised forward return.

### `res.holding_snapshot`
`run_id`, `slot`, `security_id`, `persist`, `percentile`, `ret3m`, `fip`. The
latest holdings for a run.

### Views
- `res.latest_screen` — newest `qm_panel_v2` screen, joined to ticker/name/sector.
- `res.top10_daily` — top 10 of every screen date.
- `res.split_vintage_check` — rows where two price vintages appear to be mixed.

Both of the first two are hardwired to the `qm_panel_v2` run, which is why new
screens must be published under that label to keep them current.

---

## 5. `etl` and `stg`

`etl.watermark` (ingest progress), `etl.source_file` (which SQLite file each
staged table came from, with source row counts), `etl.news` (market-news lines
lifted from screener workbooks), plus CIK/entity maps used during the earnings
harvest.

`stg.*` are **verbatim copies of the original SQLite tables**, retained so the
migration can be re-verified by exact set and value equality. They are droppable
(`DROP SCHEMA stg CASCADE`, frees ~3.3 GB). Never build analysis on `stg` — it
has no identity resolution, so it carries exactly the ticker-string traps the
modelled tables were built to remove.

---

## 6. Identity breaks: the history

Thirteen tickers were reused across a bankruptcy or reorganisation **with no CIK
change in EDGAR to reveal it**. They were found in the price series instead: an
unexplained >3x jump *plus* a data gap ≥30 days.

The gap is the discriminator. A real collapse has continuous data and must NOT be
split — Wachovia (10.00 → 0.01 in three days), WaMu, Bear Stearns and Signature
Bank are all correctly left intact. 45 such continuous events were excluded; only
the 13 gapped ones were split.

Examples: `CHTR` 2010-09-14 (0.02 → 35.50, 526-day gap), `DAL` 2007-05-03,
`META` 2022-06-09 (12.31 → 184.00 — the ticker's previous owner), `MS`
2006-01-17 (1.25 → 58.81).

To record a new one:

```sql
CALL ref.split_identity('TICK', DATE '2024-01-15', 'why this is a break');
REFRESH MATERIALIZED VIEW mkt.sp500_panel;
```

It re-points prices, dividends, splits, screen results, earnings and membership
intervals at the new security, and refuses a break at a span start.

---

## 7. Query recipes

**S&P members on a date, with their closes**

```sql
SELECT s.primary_ticker, p.close
FROM ref.index_membership m
JOIN ref.security s USING (security_id)
LEFT JOIN mkt.price_daily p
       ON p.security_id = m.security_id AND p.obs_date = DATE '2015-06-15'
WHERE m.index_code = 'SP500' AND DATE '2015-06-15' <@ m.valid
ORDER BY s.primary_ticker;
```

**Survivorship-free coverage by year**

```sql
SELECT extract(year FROM obs_date)::int AS yr,
       count(DISTINCT security_id) AS members_priced,
       count(*) AS member_days
FROM mkt.sp500_panel
GROUP BY 1 ORDER BY 1;
```

**One name's rank history, identity-correct**

```sql
SELECT s.obs_date, s.rank, s.percentile, s.mom, s.fip, s.signal
FROM res.screen_result s
JOIN res.run r USING (run_id)
WHERE r.label = 'qm_panel_v2'
  AND s.security_id = ref.resolve('AAPL', CURRENT_DATE)
ORDER BY s.obs_date;
```

**Today's top 20 with each name's next expected report** — the join no single
SQLite file could do. Note the panel is a *record of what was filed*, so it only
runs a few weeks past the last harvest (17 events sit in the future right now);
most rows will come back NULL:

```sql
SELECT l.rank, l.ticker, l.signal, min(e.expected_date) AS next_expected
FROM res.latest_screen l
LEFT JOIN evt.earnings_event e
       ON e.security_id = l.security_id AND e.expected_date >= CURRENT_DATE
WHERE l.rank <= 20
GROUP BY 1, 2, 3
ORDER BY l.rank;
```

For a date on every name, project each firm's next report from **its own**
cadence instead — no vendor calendar, no revision risk, and knowable in advance:

```sql
WITH last AS (
    SELECT DISTINCT ON (security_id) security_id, filed_date
    FROM evt.earnings_event
    ORDER BY security_id, filed_date DESC)
SELECT l.rank, l.ticker, last.filed_date AS last_report,
       last.filed_date + 91 AS approx_next
FROM res.latest_screen l
JOIN last USING (security_id)
WHERE l.rank <= 20
ORDER BY l.rank;
```

**Persistence vs static QM, head to head**

```sql
SELECT p.d0,
       round(p.ret * 100, 2)     AS persist_pct,
       round(q.ret * 100, 2)     AS qm_static_pct,
       round(p.spy_ret * 100, 2) AS spy_pct
FROM res.backtest_period p
JOIN res.run rp ON rp.run_id = p.run_id AND rp.label = 'persistence'
JOIN res.run rq ON rq.label = 'qm_static'
JOIN res.backtest_period q ON q.run_id = rq.run_id AND q.d0 = p.d0
ORDER BY p.d0 DESC;
```

**Tickers that mean more than one company**

```sql
SELECT t.ticker, count(*) AS companies,
       string_agg(coalesce(s.name, s.primary_ticker), ' | '
                  ORDER BY lower(t.valid)) AS who
FROM ref.ticker_span t
JOIN ref.security s USING (security_id)
GROUP BY t.ticker HAVING count(*) > 1
ORDER BY companies DESC;
```

**Is the database current?**

```sql
SELECT (SELECT max(obs_date) FROM mkt.price_daily)    AS last_price,
       (SELECT max(obs_date) FROM res.screen_result)  AS last_screen,
       (SELECT max(data_asof) FROM res.run)           AS last_run_asof;
```

---

## 8. Writing to this database

Use `pgdb` (`C:\Users\ssair\trading-db\pgdb.py`): `connect`, `resolve_bulk`,
`upsert`, `watermark_set`. It owns the DSN and the identity resolution, so a
writer cannot accidentally key on a ticker string.

Three habits worth keeping:

1. **Resolve every ticker at its date** before inserting anything into `mkt`,
   `evt` or `res`. A new listing needs a `ref.security` plus an open-ended
   `ref.ticker_span` first.
2. **Declare provenance.** Insert the `res.run` row with a real `universe` and
   `data_asof`, then the results under its `run_id`.
3. **Wrap a publish in one transaction and guard it.** `qm-results/qm_pg.py` is
   the worked example: a row-count floor, a cap on unresolvable tickers (a large
   batch means the source's ticker format broke, not that the index turned over),
   and `ON CONFLICT DO UPDATE` so re-running a date is idempotent.

The original `.db` files remain the untouched backup of record, and
`C:\Users\ssair\trading-db\migration\` replays the whole build in order, ending
with `verify.sql` — exact set and value equality against the staged copies, not
sampling.
