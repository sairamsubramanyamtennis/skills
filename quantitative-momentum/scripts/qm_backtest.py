"""
qm_backtest.py — Walk-forward backtester for the Quantitative Momentum strategy.

Runs a monthly or quarterly rebalanced portfolio that selects stocks using:
  1. Raw 6-1 month momentum for initial ranking
  2. FIP composite quality score as a quality filter
  3. Composite QM rank to pick the final portfolio

Compares against SPY benchmark and outputs full performance metrics.
"""

import argparse
import json
import sys
import os
import time
import warnings
from datetime import datetime, timedelta
from io import StringIO

import numpy as np
import pandas as pd
import requests
import yfinance as yf
from scipy import stats

warnings.filterwarnings("ignore")

# ============================================================================
# POINT-IN-TIME (SURVIVORSHIP-BIAS-FREE) UNIVERSE — Postgres `trading`
# ============================================================================
# Membership and prices both come from the Postgres `trading` database on
# localhost:5433 (`ref.index_membership` + `mkt.price_daily`), read through the
# house adapter in C:\Users\ssair\trading-db. Using this instead of the current
# Wikipedia list removes the survivorship bias that inflated the early results
# here roughly 3x, and mkt.price_daily carries delisted names the free panels
# were missing.
#
# The panel is keyed by `security_id`, never by ticker string: 213 tickers
# denote more than one company across time (ABX = Barrick then Abacus), and
# joining through the string silently merges them.

PG_ADAPTER_DIR = r"C:\Users\ssair\trading-db"
DEFAULT_INDEX_CODE = "SP500"


def _pgdb():
    """Import the house Postgres adapter. Lazy — the wikipedia path never needs it."""
    if PG_ADAPTER_DIR not in sys.path:
        sys.path.insert(0, PG_ADAPTER_DIR)
    import pgdb
    return pgdb


def build_membership(cur, index_code=DEFAULT_INDEX_CODE):
    """Point-in-time index membership as (dates, sets-of-security_id).

    `ref.index_membership` stores ~1,270 half-open intervals rather than dense
    daily rows, so sweep the interval boundaries into one snapshot per change
    date. That keeps members_asof() an O(log n) searchsorted.
    """
    cur.execute(
        """SELECT security_id, lower(valid), upper(valid)
             FROM ref.index_membership
            WHERE index_code = %s""", (index_code,))

    events = {}
    for sid, lo, hi in cur.fetchall():
        events.setdefault(lo, ([], []))[0].append(sid)
        if hi is not None:                       # upper bound is EXCLUSIVE
            events.setdefault(hi, ([], []))[1].append(sid)

    live, dates, sets = set(), [], []
    for d in sorted(events):
        adds, drops = events[d]
        live = (live - set(drops)) | set(adds)   # drops first: a same-day re-add wins
        dates.append(d)
        sets.append(frozenset(live))

    return pd.to_datetime(dates).values, sets    # datetime64[ns], sorted ascending


def members_asof(membership, date):
    """Return the frozenset of index members as of `date` (most recent snapshot
    with snapshot_date <= date). No lookahead."""
    dates, sets = membership
    i = np.searchsorted(dates, np.datetime64(pd.Timestamp(date)), side="right") - 1
    if i < 0:
        return frozenset()
    return sets[i]


def load_pit_universe(start_date=None, index_code=DEFAULT_INDEX_CODE):
    """Load the survivorship-bias-free universe from Postgres.

    Returns (prices, membership, sectors, labels):
      prices     — split-adjusted closes, index=date, columns=security_id, for every
                   security that was EVER in the index (delisted names included —
                   that is the whole reason to source it here rather than from a
                   current-constituents list).
      membership — (dates, sets) from build_membership(), same security_id keys.
      sectors    — {security_id: GICS sector}. A security with no sector on record
                   gets its OWN bucket so the sector cap never spuriously binds on it.
      labels     — {security_id: ticker}, for display only. Nothing joins on it.

    `start_date` trims the price pull; pass ~2 years before the backtest start so
    the momentum/FIP warmup has history. None loads everything (~2003-09-10 on).

    Prices are split-adjusted, NOT dividend-adjusted — these are price returns.
    """
    pgdb = _pgdb()
    with pgdb.connect() as pg:
        cur = pg.cursor()
        membership = build_membership(cur, index_code)

        sql = """SELECT p.security_id, p.obs_date, p.close
                   FROM mkt.price_daily p
                  WHERE p.security_id IN (SELECT security_id
                                            FROM ref.index_membership
                                           WHERE index_code = %s)
                    AND (%s::date IS NULL OR p.obs_date >= %s::date)"""
        # COPY beats read_sql by ~10x on the multi-million-row pull; mogrify does
        # the parameter binding COPY itself cannot.
        q = cur.mogrify(sql, (index_code, start_date, start_date)).decode()
        buf = StringIO()
        cur.copy_expert(f"COPY ({q}) TO STDOUT WITH CSV HEADER", buf)
        buf.seek(0)
        long = pd.read_csv(buf, parse_dates=["obs_date"])

        cur.execute(
            """SELECT s.security_id, s.primary_ticker, s.sector
                 FROM ref.security s
                WHERE s.security_id IN (SELECT security_id
                                          FROM ref.index_membership
                                         WHERE index_code = %s)""", (index_code,))
        meta = cur.fetchall()

    prices = long.pivot(index="obs_date", columns="security_id",
                        values="close").sort_index()
    prices.index.name = None
    prices.columns.name = None

    labels = {sid: (tkr or f"sec_{sid}") for sid, tkr, _ in meta}
    sectors = {sid: (sec if sec else f"_UNK_{sid}") for sid, _, sec in meta}

    return prices, membership, sectors, labels


def load_benchmark(ticker="SPY", start_date=None):
    """Benchmark closes from the SAME Postgres panel as the strategy.

    Basis matching is the whole point. mkt.price_daily is split-adjusted but not
    dividend-adjusted, so a portfolio priced from it earns price return only.
    Benchmarking that against Yahoo's auto_adjust=True SPY — which reinvests
    dividends — would charge the strategy ~1.8pp/yr of SPY yield it never had the
    chance to earn, and read as underperformance that is purely an artifact.
    """
    pgdb = _pgdb()
    with pgdb.connect() as pg:
        cur = pg.cursor()
        cur.execute("SELECT ref.resolve(%s, CURRENT_DATE)", (ticker,))
        row = cur.fetchone()
        sid = row[0] if row else None
        if sid is None:
            raise RuntimeError(f"Benchmark {ticker} not found in ref.ticker_span")
        cur.execute(
            """SELECT obs_date, close FROM mkt.price_daily
                WHERE security_id = %s AND (%s::date IS NULL OR obs_date >= %s::date)
                ORDER BY obs_date""", (sid, start_date, start_date))
        rows = cur.fetchall()

    s = pd.Series({pd.Timestamp(d): c for d, c in rows}).sort_index()
    s.name = ticker
    return s


# ============================================================================
# POLYGON.IO HELPERS (primary price source)
# ============================================================================

POLYGON_BASE = "https://api.polygon.io"
WIKI_UA = "QM-Screener/1.0 (educational; pandas)"


def get_polygon_api_key():
    """Fetch Polygon API key from keyring (preferred) or env var fallback."""
    try:
        import keyring
        key = keyring.get_password("polygon-api", "default")
        if key:
            return key
    except Exception:
        pass
    return os.environ.get("POLYGON_API_KEY")


def _fetch_polygon_grouped_day(date_str, api_key, session):
    """Fetch one trading day of grouped daily bars from Polygon."""
    url = f"{POLYGON_BASE}/v2/aggs/grouped/locale/us/market/stocks/{date_str}"
    try:
        r = session.get(url, params={"apiKey": api_key, "adjusted": "true"}, timeout=30)
    except requests.RequestException as e:
        print(f"  Polygon fetch error for {date_str}: {e}", file=sys.stderr)
        return None
    if r.status_code != 200:
        if r.status_code == 429:
            print(f"  Polygon 429 for {date_str} — sleeping 60s", file=sys.stderr)
            time.sleep(60)
        return None
    j = r.json()
    if j.get("status") != "OK" or not j.get("results"):
        return pd.DataFrame()
    return pd.DataFrame(j["results"])


def download_prices_polygon(tickers, start_date, end_date, cache_dir=None):
    """Build a price DataFrame via Polygon Grouped Daily Bars, with on-disk cache."""
    api_key = get_polygon_api_key()
    if not api_key:
        raise RuntimeError("No Polygon API key")

    if cache_dir is None:
        cache_dir = os.path.join(os.path.expanduser("~"), ".qm-cache", "polygon_daily")
    os.makedirs(cache_dir, exist_ok=True)

    bdates = pd.bdate_range(start_date, end_date)
    ticker_set = set(tickers)
    session = requests.Session()
    rows = []
    cached, fetched, skipped = 0, 0, 0

    print(f"Polygon: requesting {len(bdates)} business days "
          f"({start_date} to {end_date})...", file=sys.stderr)

    for d in bdates:
        date_str = d.strftime("%Y-%m-%d")
        cache_path = os.path.join(cache_dir, f"{date_str}.parquet")
        if os.path.exists(cache_path):
            df_day = pd.read_parquet(cache_path)
            cached += 1
        else:
            df_day = _fetch_polygon_grouped_day(date_str, api_key, session)
            if df_day is None:
                skipped += 1
                continue
            if not df_day.empty:
                df_day.to_parquet(cache_path)
            fetched += 1

        if df_day.empty:
            continue
        sub = df_day[df_day["T"].isin(ticker_set)][["T", "c"]]
        for t, c in zip(sub["T"].values, sub["c"].values):
            rows.append((date_str, t, c))

    print(f"  Polygon summary: {cached} cached, {fetched} fetched, {skipped} errors",
          file=sys.stderr)

    if not rows:
        return pd.DataFrame()

    long = pd.DataFrame(rows, columns=["date", "ticker", "close"])
    long["date"] = pd.to_datetime(long["date"])
    prices = long.pivot(index="date", columns="ticker", values="close").sort_index()
    print(f"Polygon: {prices.shape[0]} days x {prices.shape[1]} tickers", file=sys.stderr)
    return prices


# ============================================================================
# DEFAULTS
# ============================================================================

DEFAULT_PARAMS = {
    "lookback_months": 6,
    "skip_months": 1,
    "n_holdings": 50,
    "weighting": "equal",         # equal, momentum, inv_vol, qm_composite
    "rebalance_freq": "monthly",  # UPDATED: monthly outperforms quarterly by +0.46 composite (autoresearch)
    "sector_cap": 0.40,
    "fip_lookback_days": 126,     # ~6 months of trading days for FIP
    "fip_weight": 0.75,           # UPDATED: FIP 0.75 outperforms 0.50 (autoresearch: monotonic improvement)
    "min_qm_percentile": 80,      # minimum composite QM percentile to qualify
    "vol_adjust_momentum": True,  # NEW: divide momentum by realized vol (autoresearch hybrid finding)
}


# ============================================================================
# DATA HELPERS (shared with screener)
# ============================================================================

def get_sp500_tickers():
    """Fetch current S&P 500 constituents from Wikipedia (with User-Agent to avoid 403)."""
    try:
        r = requests.get(
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
            headers={"User-Agent": WIKI_UA},
            timeout=20,
        )
        r.raise_for_status()
        tables = pd.read_html(StringIO(r.text))
        df = tables[0]
        tickers = df["Symbol"].str.replace(".", "-", regex=False).tolist()
        sectors = dict(zip(
            df["Symbol"].str.replace(".", "-", regex=False),
            df["GICS Sector"]
        ))
        names = dict(zip(
            df["Symbol"].str.replace(".", "-", regex=False),
            df["Security"]
        ))
        return tickers, sectors, names
    except Exception:
        fallback = [
            "AAPL","MSFT","GOOGL","AMZN","NVDA","META","TSLA","BRK-B",
            "UNH","JNJ","V","XOM","JPM","PG","MA","HD","CVX","MRK",
            "ABBV","LLY","PEP","KO","COST","AVGO","TMO","MCD","WMT",
            "ACN","CSCO","ABT","DHR","CRM","TXN","NEE","PM","UPS",
            "MS","RTX","HON","LOW","INTC","QCOM","INTU","AMAT","CAT",
            "BA","GE","AMD","ISRG","SYK"
        ]
        return fallback, {}, {}


def download_prices_yahoo(tickers, start_date, end_date):
    """Download adjusted close prices for all tickers via yfinance."""
    print(f"Yahoo: downloading prices from {start_date} to {end_date}...", file=sys.stderr)
    data = yf.download(
        tickers, start=start_date, end=end_date,
        auto_adjust=True, progress=False, threads=True
    )

    if isinstance(data.columns, pd.MultiIndex):
        if "Close" in data.columns.get_level_values(0):
            prices = data["Close"]
        else:
            prices = data.iloc[:, :len(tickers)]
    else:
        prices = data

    print(f"Yahoo: {prices.shape[0]} days x {prices.shape[1]} tickers", file=sys.stderr)
    return prices


# Polygon Starter has ~2 years of history. Only use it for short backtests;
# Yahoo remains primary for long backtests.
POLYGON_HISTORY_DAYS = 730


def download_prices(tickers, start_date, end_date):
    """Route to Polygon for short backtests within Polygon's history window,
    otherwise Yahoo. Yahoo remains the only viable source for long backtests."""
    start = pd.Timestamp(start_date)
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=POLYGON_HISTORY_DAYS)

    if get_polygon_api_key() and start >= cutoff:
        try:
            prices = download_prices_polygon(tickers, start_date, end_date)
            if not prices.empty and prices.shape[0] > 20:
                return prices
            print("Polygon returned insufficient data — falling back to Yahoo", file=sys.stderr)
        except Exception as e:
            print(f"Polygon path failed ({e}) — falling back to Yahoo", file=sys.stderr)
    else:
        if not get_polygon_api_key():
            print("No Polygon API key — using Yahoo", file=sys.stderr)
        else:
            print(f"Backtest start {start.date()} predates Polygon Starter's "
                  f"~2yr history (cutoff {cutoff.date()}) — using Yahoo", file=sys.stderr)

    return download_prices_yahoo(tickers, start_date, end_date)


# ============================================================================
# FIP CALCULATION (point-in-time for backtesting)
# ============================================================================

def calculate_fip_at_date(daily_returns_up_to_date, lookback_days=126):
    """
    Calculate FIP composite for all tickers using data up to a specific date.
    Point-in-time: no lookahead bias.
    """
    fip_scores = {}
    for ticker in daily_returns_up_to_date.columns:
        try:
            rets = daily_returns_up_to_date[ticker].dropna().tail(lookback_days)
            if len(rets) < 20:
                fip_scores[ticker] = np.nan
                continue

            pct_positive = (rets > 0).sum() / len(rets)

            cum_rets = (1 + rets).cumprod()
            x = np.arange(len(cum_rets))
            slope, _, r_value, _, _ = stats.linregress(x, cum_rets.values)
            r_sq = r_value ** 2 if slope > 0 else 0.0

            fip_scores[ticker] = 0.5 * pct_positive + 0.5 * r_sq
        except Exception:
            fip_scores[ticker] = np.nan

    return pd.Series(fip_scores)


# ============================================================================
# MOMENTUM CALCULATION (point-in-time)
# ============================================================================

def calculate_momentum_at_date(monthly_prices, lookback_months, skip_months,
                               daily_returns=None, vol_adjust=True):
    """
    Calculate momentum using monthly prices up to a specific point,
    optionally volatility-adjusted.
    No lookahead bias — uses only data available at the time.
    """
    if len(monthly_prices) < lookback_months + skip_months + 1:
        return pd.Series(dtype=float)

    end_price = monthly_prices.iloc[-(skip_months + 1)]
    start_price = monthly_prices.iloc[-(lookback_months + skip_months + 1)]

    momentum = (end_price / start_price - 1) * 100

    # Volatility-adjusted momentum: divide by realized vol
    if vol_adjust and daily_returns is not None:
        vol_days = lookback_months * 21
        recent = daily_returns.tail(vol_days)
        realized_vol = recent.std() * np.sqrt(252) * 100
        realized_vol = realized_vol.clip(lower=5.0)
        common = momentum.index.intersection(realized_vol.index)
        momentum = momentum.loc[common] / realized_vol.loc[common]

    return momentum


# ============================================================================
# PORTFOLIO CONSTRUCTION
# ============================================================================

def select_and_weight(momentum, fip_scores, sectors, params):
    """
    Select stocks using composite QM rank and calculate weights.
    """
    # Drop NaNs — need both momentum and FIP
    common = momentum.dropna().index.intersection(fip_scores.dropna().index)
    mom = momentum.loc[common]
    fip = fip_scores.loc[common]

    if len(common) < 10:
        return pd.Series(dtype=float), []

    # Rank
    mom_rank = mom.rank(ascending=False)
    fip_rank = fip.rank(ascending=False)

    # Composite rank (weighted by fip_weight)
    fip_w = params.get("fip_weight", 0.5)
    composite_rank = ((1 - fip_w) * mom_rank + fip_w * fip_rank)
    composite_rank = composite_rank.rank(method="min")

    # Percentile filter
    n = len(composite_rank)
    percentile = (n - composite_rank + 1) / n * 100
    candidates = composite_rank[percentile >= params.get("min_qm_percentile", 80)]
    candidates = candidates.sort_values()

    # Sector cap
    sector_cap = params.get("sector_cap", 0.40)
    n_holdings = params.get("n_holdings", 50)

    if sector_cap > 0 and sectors:
        selected = []
        sector_counts = {}
        max_per_sector = max(1, int(n_holdings * sector_cap))

        for ticker in candidates.index:
            sec = sectors.get(ticker, "Unknown")
            if sector_counts.get(sec, 0) < max_per_sector:
                selected.append(ticker)
                sector_counts[sec] = sector_counts.get(sec, 0) + 1
            if len(selected) >= n_holdings:
                break
    else:
        selected = list(candidates.index[:n_holdings])

    if not selected:
        return pd.Series(dtype=float), []

    # Weighting
    weighting = params.get("weighting", "equal")
    n_sel = len(selected)

    if weighting == "equal":
        weights = pd.Series(1.0 / n_sel, index=selected)
    elif weighting == "momentum":
        mom_sel = mom.loc[selected]
        shifted = mom_sel - mom_sel.min() + 1
        weights = shifted / shifted.sum()
    elif weighting == "qm_composite":
        # Weight inversely proportional to composite rank (better rank = higher weight)
        cr = composite_rank.loc[selected]
        inv_rank = 1.0 / cr
        weights = inv_rank / inv_rank.sum()
    else:
        weights = pd.Series(1.0 / n_sel, index=selected)

    return weights, selected


# ============================================================================
# BACKTESTING ENGINE
# ============================================================================

def backtest(prices, sectors, params, start_year=2015, membership=None, labels=None,
             benchmark_prices=None):
    """
    Walk-forward backtest of the Quantitative Momentum strategy.

    At each rebalance date:
      1. Compute momentum using only data available at that time
      2. Compute FIP quality using only daily returns up to that time
      3. (If `membership` given) restrict candidates to the S&P 500 constituents
         as of that rebalance date — survivorship-bias-free selection
      4. Build composite QM rank → select portfolio
      5. Hold until next rebalance

    `membership`: optional (dates, sets) from build_membership(). When provided,
    the investable universe at each rebalance is the point-in-time index
    membership rather than the static price-panel columns.

    `labels`: optional {panel key: display name}. On the PIT path the panel is
    keyed by security_id, so this maps them back to tickers for the log.

    `benchmark_prices`: optional SPY close Series on the same return basis as
    `prices`. Omit it only when `prices` are themselves dividend-adjusted, since
    the fallback downloads a total-return SPY from Yahoo.

    Returns: dict with sharpe, annual return, max drawdown, etc.
    """
    def label(k):
        return str(labels.get(k, k)) if labels else str(k)

    cov_log = []  # per-rebalance member/price coverage diagnostics
    daily_returns = prices.pct_change()
    monthly = prices.resample("ME").last()
    monthly_ret = monthly.pct_change()

    # Data-hygiene guard (PIT panels of delisted names contain adjustment
    # glitches — zero-filled gaps, ticker reuse — that produce impossible
    # 1000%+ moves). Neutralize returns beyond a sane single-period bound so a
    # data artifact can't be selected or dominate a month. No-op on clean data.
    if params.get("clean_returns"):
        max_d = params.get("max_daily_return", 0.60)
        max_m = params.get("max_monthly_return", 1.00)
        daily_returns = daily_returns.mask(daily_returns.abs() > max_d)
        monthly_ret = monthly_ret.mask(monthly_ret.abs() > max_m)

    lookback = params.get("lookback_months", 6)
    skip = params.get("skip_months", 1)
    fip_days = params.get("fip_lookback_days", 126)

    warmup = lookback + skip + 2

    # Rebalance schedule
    if params.get("rebalance_freq", "quarterly") == "quarterly":
        rebal_months = [3, 6, 9, 12]
    else:
        rebal_months = list(range(1, 13))

    # SPY benchmark — on the SAME return basis as `prices`, or the excess-return
    # line is measuring the difference between two conventions, not two strategies.
    if benchmark_prices is not None:
        benchmark_basis = "price_return"
        spy_monthly_ret = benchmark_prices.resample("ME").last().pct_change()
    else:
        benchmark_basis = "total_return"
        try:
            spy_data = yf.download(
                "SPY", start=f"{start_year - 2}-01-01",
                end=datetime.now().strftime("%Y-%m-%d"),
                auto_adjust=True, progress=False
            )
            if isinstance(spy_data.columns, pd.MultiIndex):
                spy_close = spy_data["Close"]["SPY"]
            elif "Close" in spy_data.columns:
                spy_close = spy_data["Close"]
            else:
                spy_close = spy_data.iloc[:, 0]
            if isinstance(spy_close, pd.DataFrame):
                spy_close = spy_close.iloc[:, 0]
            spy_monthly_ret = spy_close.resample("ME").last().pct_change()
        except Exception:
            spy_monthly_ret = pd.Series(dtype=float)

    portfolio_returns = []
    benchmark_returns = []
    rebalance_log = []
    current_weights = pd.Series(dtype=float)

    for i in range(warmup, len(monthly)):
        date = monthly.index[i]
        if date.year < start_year:
            continue

        month = date.month
        should_rebalance = (month in rebal_months) or len(current_weights) == 0

        if should_rebalance:
            # Form the portfolio using ONLY data through the prior month-end,
            # then earn month i's return below. Using daily_returns.loc[:date]
            # (month i's last day) would leak month i's FIP/vol signal into a
            # portfolio that then earns month i — a one-month look-ahead that
            # inflated returns ~3x. hist_monthly.iloc[:i] is already lagged.
            prev_date = monthly.index[i - 1]
            hist_monthly = monthly.iloc[:i]
            hist_daily = daily_returns.loc[:prev_date]

            if len(hist_monthly) >= lookback + skip + 1:
                try:
                    mom = calculate_momentum_at_date(
                        hist_monthly, lookback, skip,
                        daily_returns=hist_daily,
                        vol_adjust=params.get("vol_adjust_momentum", True)
                    )
                    fip = calculate_fip_at_date(hist_daily, fip_days)

                    # Survivorship-bias-free: restrict to point-in-time members
                    if membership is not None:
                        mem = members_asof(membership, date)
                        priced = mem.intersection(prices.columns)
                        mom = mom[mom.index.isin(mem)]
                        fip = fip[fip.index.isin(mem)]
                        cov_log.append({
                            "date": date.strftime("%Y-%m-%d"),
                            "n_members": len(mem),
                            "n_priced": len(priced),
                            "pct_priced": round(100 * len(priced) / max(len(mem), 1), 1),
                        })

                    current_weights, selected = select_and_weight(
                        mom, fip, sectors, params
                    )
                    rebalance_log.append({
                        "date": date.strftime("%Y-%m-%d"),
                        "n_holdings": len(selected),
                        "top_5": [label(k) for k in selected[:5]],
                    })
                except Exception as e:
                    print(f"  Rebalance error at {date}: {e}", file=sys.stderr)

        # Calculate this month's portfolio return
        if len(current_weights) > 0 and i < len(monthly_ret):
            month_returns = monthly_ret.iloc[i]
            port_ret = 0.0
            for ticker in current_weights.index:
                try:
                    tr = month_returns[ticker] if ticker in month_returns.index else np.nan
                    if isinstance(tr, pd.Series):
                        tr = tr.iloc[0]
                    if not np.isnan(tr):
                        port_ret += current_weights[ticker] * tr
                except Exception:
                    pass

            portfolio_returns.append({"date": date.strftime("%Y-%m-%d"), "return": port_ret})

            # Benchmark
            try:
                spy_idx = spy_monthly_ret.index
                closest = spy_idx[spy_idx.get_indexer([date], method="nearest")[0]]
                bench_ret = spy_monthly_ret.iloc[spy_monthly_ret.index.get_loc(closest)]
                if isinstance(bench_ret, pd.Series):
                    bench_ret = bench_ret.iloc[0]
                if not np.isnan(bench_ret):
                    benchmark_returns.append({"date": date.strftime("%Y-%m-%d"), "return": bench_ret})
            except Exception:
                pass

    if not portfolio_returns:
        return {"sharpe_ratio": -999, "error": "No returns generated"}

    # ================================================================
    # PERFORMANCE METRICS
    # ================================================================
    rets = pd.Series([r["return"] for r in portfolio_returns])

    cumulative = (1 + rets).prod()
    n_years = len(rets) / 12
    annual_return = cumulative ** (1 / max(n_years, 0.01)) - 1
    annual_vol = rets.std() * np.sqrt(12)
    sharpe = (annual_return - 0.04) / max(annual_vol, 0.001)

    cum_returns = (1 + rets).cumprod()
    rolling_max = cum_returns.cummax()
    drawdown = (cum_returns - rolling_max) / rolling_max
    max_drawdown = drawdown.min()

    # Benchmark
    if benchmark_returns:
        bench_rets = pd.Series([r["return"] for r in benchmark_returns])
        bench_cum = (1 + bench_rets).prod()
        bench_annual = bench_cum ** (1 / max(len(bench_rets) / 12, 0.01)) - 1
        excess_return = annual_return - bench_annual
    else:
        bench_annual = 0
        excess_return = annual_return

    result = {
        "sharpe_ratio": round(sharpe, 4),
        "annual_return": round(annual_return * 100, 2),
        "annual_vol": round(annual_vol * 100, 2),
        "max_drawdown": round(max_drawdown * 100, 2),
        "total_return": round((cumulative - 1) * 100, 2),
        "n_months": len(rets),
        "n_years": round(n_years, 1),
        "benchmark_annual": round(bench_annual * 100, 2),
        "excess_return": round(excess_return * 100, 2),
        # Which convention BOTH sides are on. 'price_return' = no dividends
        # anywhere; 'total_return' = dividends reinvested on both sides. Never
        # compare an excess_return figure across the two.
        "benchmark_basis": benchmark_basis,
        "n_rebalances": len(rebalance_log),
        "params": params,
        "monthly_returns": portfolio_returns,
        "benchmark_monthly_returns": benchmark_returns,
    }

    if cov_log:
        pct = [c["pct_priced"] for c in cov_log]
        result["pit_universe"] = True
        result["pit_avg_pct_priced"] = round(float(np.mean(pct)), 1)
        result["pit_min_pct_priced"] = round(float(np.min(pct)), 1)
        result["pit_coverage_log"] = cov_log

    return result


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Quantitative Momentum Backtester")
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--n-holdings", type=int, default=50)
    parser.add_argument("--rebalance", choices=["monthly", "quarterly"], default="monthly")
    parser.add_argument("--output-dir", type=str, default=".")
    parser.add_argument("--params-json", type=str, default=None,
                        help="JSON string of full param overrides")
    parser.add_argument("--universe", choices=["wikipedia", "pit"],
                        default="wikipedia",
                        help="'wikipedia' = current S&P 500 list (survivorship-"
                             "biased, default); 'pit' = point-in-time membership "
                             "+ delisted-inclusive Postgres panel (honest)")
    parser.add_argument("--index-code", type=str, default=DEFAULT_INDEX_CODE,
                        help="PIT mode: which index's membership defines the universe")

    args = parser.parse_args()

    params = DEFAULT_PARAMS.copy()
    params["n_holdings"] = args.n_holdings
    params["rebalance_freq"] = args.rebalance

    if args.params_json:
        overrides = json.loads(args.params_json)
        params.update(overrides)

    os.makedirs(args.output_dir, exist_ok=True)

    print("=" * 60, file=sys.stderr)
    print("  Quantitative Momentum Backtester", file=sys.stderr)
    print(f"  Start: {args.start_year} | Holdings: {params['n_holdings']} | "
          f"Rebalance: {params['rebalance_freq']}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    params["universe"] = args.universe

    labels = None
    bench = None
    if args.universe == "pit":
        params["clean_returns"] = True
        pit_start = f"{args.start_year - 2}-01-01"
        print(f"Universe: POINT-IN-TIME (survivorship-bias-free)\n"
              f"  source: Postgres trading @ localhost:5433 "
              f"(mkt.price_daily + ref.index_membership)\n"
              f"  index: {args.index_code} | prices from {pit_start}", file=sys.stderr)
        prices, membership, sectors, labels = load_pit_universe(
            start_date=pit_start, index_code=args.index_code)
        print(f"  panel: {prices.shape[0]} days x {prices.shape[1]} securities "
              f"({prices.index.min().date()} .. {prices.index.max().date()})",
              file=sys.stderr)
        bench = load_benchmark("SPY", start_date=pit_start)
        print("  benchmark: SPY from the same panel - price return on both sides",
              file=sys.stderr)
    else:
        tickers, sectors, names = get_sp500_tickers()
        start_date = f"{args.start_year - 2}-01-01"
        end_date = datetime.now().strftime("%Y-%m-%d")
        prices = download_prices(tickers, start_date, end_date)
        membership = None

    print("Running backtest...", file=sys.stderr)
    result = backtest(prices, sectors, params, start_year=args.start_year,
                      membership=membership, labels=labels, benchmark_prices=bench)

    if result.get("pit_universe"):
        print(f"  PIT price coverage: avg {result['pit_avg_pct_priced']}% "
              f"(min {result['pit_min_pct_priced']}%) of members had prices",
              file=sys.stderr)

    # Output metric line for autoresearch compatibility
    print(f"METRIC:sharpe_ratio={result['sharpe_ratio']}")

    # Save results
    output_file = os.path.join(args.output_dir, "qm_backtest_results.json")
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2, default=str)

    print(f"\nResults saved to: {output_file}", file=sys.stderr)
    print(json.dumps({k: v for k, v in result.items()
                       if k not in ("monthly_returns", "benchmark_monthly_returns",
                                    "pit_coverage_log")},
                      indent=2, default=str))
