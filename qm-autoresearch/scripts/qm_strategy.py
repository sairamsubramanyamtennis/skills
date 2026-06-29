"""
qm_strategy.py — The "train.py" equivalent for QM autoresearch.

This is the ONLY file the agent modifies during hybrid experiments.
It defines the full Quantitative Momentum strategy and runs a backtest
that outputs two metrics:
  1. sharpe_ratio — risk-adjusted returns (the primary objective)
  2. quality_premium — whether high-FIP stocks outperform low-FIP stocks
     (the quality filter: penalize if quality doesn't "work")

The composite metric is: sharpe_ratio - penalty if quality_premium <= 0.

Usage:
    python qm_strategy.py --backtest --start-year 2015
    python qm_strategy.py --backtest --params-json '{"lookback_months": 6, ...}'
    python qm_strategy.py --live
"""

import argparse
import json
import sys
import warnings
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import yfinance as yf
from scipy import stats

warnings.filterwarnings("ignore")

# Windows consoles default to cp1252 and choke on the harness's Unicode output.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import os
import requests

# ============================================================================
# POLYGON PRICE SOURCE (primary; yfinance is the fallback)
# yfinance rate-limits hard on ~500-ticker multi-year pulls, so backtests use
# Polygon per-ticker daily aggs, cached as one wide parquet panel per date range.
# ============================================================================

_POLY_BASE = "https://api.polygon.io"


def _poly_key():
    try:
        import keyring
        k = keyring.get_password("polygon-api", "default")
        if k:
            return k
    except Exception:
        pass
    return os.environ.get("POLYGON_API_KEY")


def _poly_ticker_closes(ticker, start, end, key, session):
    """Adjusted daily closes for one ticker via Polygon aggs. pd.Series or None."""
    # Polygon uses the dotted class-share form (BRK.B); screener stores BRK-B.
    poly_tkr = ticker.replace("-", ".")
    url = f"{_POLY_BASE}/v2/aggs/ticker/{poly_tkr}/range/1/day/{start}/{end}"
    try:
        r = session.get(url, params={"adjusted": "true", "sort": "asc",
                                     "limit": 50000, "apiKey": key}, timeout=30)
        if r.status_code != 200:
            return None
        res = r.json().get("results") or []
        if not res:
            return None
        idx = pd.to_datetime([x["t"] for x in res], unit="ms").normalize()
        return pd.Series([x["c"] for x in res], index=idx, name=ticker)
    except requests.RequestException:
        return None


def _poly_panel(tickers, start_date, end_date):
    """Wide date x ticker adjusted-close panel via Polygon, cached per date range."""
    key = _poly_key()
    if not key:
        return None
    cache_dir = os.path.join(os.path.expanduser("~"), ".qm-cache", "autoresearch_panels")
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, f"panel_{start_date}_{end_date}.parquet")
    if os.path.exists(cache_path):
        try:
            return pd.read_parquet(cache_path)
        except Exception:
            pass
    session = requests.Session()
    cols = {}
    for t in tickers:
        s = _poly_ticker_closes(t, start_date, end_date, key, session)
        if s is not None and len(s):
            cols[t] = s
    if not cols:
        return None
    panel = pd.DataFrame(cols).sort_index()
    try:
        panel.to_parquet(cache_path)
    except Exception:
        pass
    return panel


# ============================================================================
# YAHOO v8 CHART SOURCE (primary for DEEP history — ~20y daily adjusted closes)
# Polygon's tier caps history at ~4y; the Yahoo v8 chart endpoint is a different API
# than yfinance's rate-limited .info/.download path and reliably serves 20y.
# ============================================================================

_YHOSTS = ("query1", "query2")
_YUA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def _yahoo_v8_closes(ticker, start_date, end_date, session):
    """Adjusted daily closes for one ticker via the Yahoo v8 chart API. pd.Series or None."""
    p1 = int(pd.Timestamp(start_date).timestamp())
    p2 = int(pd.Timestamp(end_date).timestamp())
    for host in _YHOSTS:
        url = f"https://{host}.finance.yahoo.com/v8/finance/chart/{ticker}"
        try:
            r = session.get(url, params={"period1": p1, "period2": p2,
                                         "interval": "1d", "events": "div,splits"},
                            headers={"User-Agent": _YUA}, timeout=30)
            if r.status_code != 200:
                continue
            res = r.json()["chart"]["result"][0]
            ts = res.get("timestamp")
            if not ts:
                continue
            ind = res["indicators"]
            vals = (ind.get("adjclose", [{}])[0].get("adjclose")
                    or ind["quote"][0].get("close"))
            idx = pd.to_datetime(ts, unit="s").normalize()
            s = pd.Series(vals, index=idx, name=ticker).dropna()
            if len(s):
                return s
        except (requests.RequestException, KeyError, IndexError, ValueError):
            continue
    return None


def _yahoo_v8_panel(tickers, start_date, end_date):
    """Wide date x ticker adjusted-close panel via Yahoo v8, cached per date range."""
    cache_dir = os.path.join(os.path.expanduser("~"), ".qm-cache", "autoresearch_panels")
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, f"panel_v8_{start_date}_{end_date}.parquet")
    if os.path.exists(cache_path):
        try:
            return pd.read_parquet(cache_path)
        except Exception:
            pass
    session = requests.Session()
    cols = {}
    for t in tickers:
        s = _yahoo_v8_closes(t, start_date, end_date, session)
        if s is not None and len(s):
            cols[t] = s
    if not cols:
        return None
    panel = pd.DataFrame(cols).sort_index()
    try:
        panel.to_parquet(cache_path)
    except Exception:
        pass
    return panel


# ============================================================================
# STRATEGY PARAMETERS — The autoresearch agent experiments with these
# ============================================================================

PARAMS = {
    # Lookback & skip
    "lookback_months": 6,        # How far back to measure momentum
    "skip_months": 1,            # Recent months to skip (short-term reversal)

    # FIP quality calculation
    "fip_lookback_days": 126,    # Trading days for FIP calculation (~6 months)
    "fip_weight": 0.50,          # Weight of FIP in composite rank (0.0 = pure momentum, 1.0 = pure quality)
    "fip_pct_positive_weight": 0.50,  # Weight of pct-positive-days in FIP (rest goes to R²)

    # Portfolio construction
    "n_holdings": 50,            # Number of stocks to hold
    "weighting": "equal",        # "equal", "momentum", "qm_composite", "inv_vol"

    # Rebalancing
    "rebalance_freq": "quarterly",  # "monthly", "quarterly"

    # Filters
    "sector_cap": 0.40,          # Max fraction in any single sector (0.0 = no cap)
    "min_qm_percentile": 80,     # Minimum composite QM percentile to qualify
    "exclude_negative_1m": False, # Exclude stocks with negative 1-month return

    # Risk management
    "stop_loss_pct": 0.0,        # 0.0 = disabled; e.g. 0.20 = sell if down 20%
}


# ============================================================================
# S&P 500 UNIVERSE
# ============================================================================

def get_sp500_tickers():
    """Fetch current S&P 500 constituents from Wikipedia."""
    try:
        tables = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
        df = tables[0]
        tickers = df["Symbol"].str.replace(".", "-", regex=False).tolist()
        sectors = dict(zip(
            df["Symbol"].str.replace(".", "-", regex=False),
            df["GICS Sector"]
        ))
        return tickers, sectors
    except Exception:
        fallback = [
            "AAPL","MSFT","GOOGL","AMZN","NVDA","META","TSLA","BRK-B",
            "UNH","JNJ","V","XOM","JPM","PG","MA","HD","CVX","MRK",
            "ABBV","LLY","PEP","KO","COST","AVGO","TMO","MCD","WMT",
            "ACN","CSCO","ABT","DHR","CRM","TXN","NEE","PM","UPS",
            "MS","RTX","HON","LOW","INTC","QCOM","INTU","AMAT","CAT",
            "BA","GE","AMD","ISRG","SYK"
        ]
        return fallback, {}


def download_prices(tickers, start_date, end_date):
    """Adjusted close prices (date x ticker).

    Order: Yahoo v8 chart (deep ~20y history) -> Polygon (recent, tier-capped) ->
    yfinance.download (legacy fallback, rate-limit prone).
    """
    panel = _yahoo_v8_panel(tickers, start_date, end_date)
    if panel is not None and panel.shape[1] >= max(20, len(tickers) // 2):
        return panel
    panel = _poly_panel(tickers, start_date, end_date)
    if panel is not None and panel.shape[1] >= max(20, len(tickers) // 2):
        return panel
    # Fallback: yfinance (rate-limit prone for large pulls)
    data = yf.download(
        tickers, start=start_date, end=end_date,
        auto_adjust=True, progress=False, threads=True
    )
    if isinstance(data.columns, pd.MultiIndex):
        if "Close" in data.columns.get_level_values(0):
            return data["Close"]
    return data


# ============================================================================
# FIP QUALITY SCORE
# ============================================================================

def calculate_fip(daily_returns, lookback_days, pct_pos_weight=0.5):
    """
    Calculate FIP composite quality score for all tickers.

    Components:
      - Percent positive days (consistency)
      - R-squared of cumulative returns vs time (path smoothness)

    Weighted by pct_pos_weight / (1 - pct_pos_weight).
    """
    fip_scores = {}
    for ticker in daily_returns.columns:
        try:
            rets = daily_returns[ticker].dropna().tail(lookback_days)
            if len(rets) < 20:
                fip_scores[ticker] = np.nan
                continue

            pct_pos = (rets > 0).sum() / len(rets)
            cum = (1 + rets).cumprod()
            x = np.arange(len(cum))
            slope, _, r_val, _, _ = stats.linregress(x, cum.values)
            r_sq = r_val ** 2 if slope > 0 else 0.0

            fip_scores[ticker] = pct_pos_weight * pct_pos + (1 - pct_pos_weight) * r_sq
        except Exception:
            fip_scores[ticker] = np.nan

    return pd.Series(fip_scores)


# ============================================================================
# MOMENTUM CALCULATION
# ============================================================================

def calculate_momentum(monthly_prices, lookback, skip):
    """Calculate lookback-skip momentum returns."""
    if len(monthly_prices) < lookback + skip + 1:
        return pd.Series(dtype=float), pd.Series(dtype=float)

    end = monthly_prices.iloc[-(skip + 1)]
    start = monthly_prices.iloc[-(lookback + skip + 1)]
    momentum = (end / start - 1) * 100

    # 1-month return for optional filter
    now = monthly_prices.iloc[-1]
    prev = monthly_prices.iloc[-2] if len(monthly_prices) >= 2 else now
    ret_1m = (now / prev - 1) * 100

    return momentum, ret_1m


# ============================================================================
# LOCAL DATA (check the user's local cache FIRST — survivorship-reduced backtest)
#   C:\Users\ssair\s&p Historic Data\
#     sp500_prices_daily.parquet              daily adj-close panel (1970-2026, 836 tkrs)
#     sp500_historical_components_changes.csv point-in-time membership (1996-2026)
# ============================================================================

LOCAL_DATA_DIR = r"C:\Users\ssair\s&p Historic Data"
LOCAL_PRICES = os.path.join(LOCAL_DATA_DIR, "sp500_prices_daily.parquet")
LOCAL_PIT = os.path.join(LOCAL_DATA_DIR, "sp500_historical_components_changes.csv")


def load_local_prices():
    """Local daily adjusted-close panel if present (checked FIRST), else None."""
    if os.path.exists(LOCAL_PRICES):
        try:
            df = pd.read_parquet(LOCAL_PRICES)
            df.index = pd.to_datetime(df.index)
            return df.sort_index()
        except Exception as e:
            print(f"  Local prices load failed: {e}", file=sys.stderr)
    return None


def load_pit_membership():
    """Point-in-time membership as sorted [(Timestamp, frozenset(tickers))], or None."""
    if not os.path.exists(LOCAL_PIT):
        return None
    try:
        df = pd.read_csv(LOCAL_PIT)
        rows = []
        for _, r in df.iterrows():
            d = pd.Timestamp(r["date"])
            ts = frozenset(t.strip() for t in str(r["tickers"]).split(",") if t.strip())
            rows.append((d, ts))
        rows.sort(key=lambda x: x[0])
        return rows
    except Exception as e:
        print(f"  PIT membership load failed: {e}", file=sys.stderr)
        return None


def members_on(membership, date):
    """Constituents as of `date` (forward-filled from the last change on/before it)."""
    if not membership:
        return None
    import bisect
    dates = [d for d, _ in membership]
    i = bisect.bisect_right(dates, pd.Timestamp(date)) - 1
    return membership[max(i, 0)][1]


# ============================================================================
# PORTFOLIO CONSTRUCTION
# ============================================================================

def select_portfolio(momentum, fip, ret_1m, sectors, params, allowed=None):
    """
    Select and weight the portfolio using composite QM rank.
    Returns: (weights Series, selected tickers list)
    """
    common = momentum.dropna().index.intersection(fip.dropna().index)
    # Point-in-time universe filter: only names that were S&P members on this date.
    if allowed is not None:
        common = common.intersection(pd.Index(list(allowed)))
    mom = momentum.loc[common]
    fip_s = fip.loc[common]

    if len(common) < 10:
        return pd.Series(dtype=float), []

    # Ranks (1 = best)
    mom_rank = mom.rank(ascending=False)
    fip_rank = fip_s.rank(ascending=False)

    fw = params["fip_weight"]
    composite = ((1 - fw) * mom_rank + fw * fip_rank).rank(method="min")

    # Percentile filter
    n = len(composite)
    pct = (n - composite + 1) / n * 100
    candidates = composite[pct >= params["min_qm_percentile"]].sort_values()

    # Exclude negative 1-month
    if params["exclude_negative_1m"]:
        neg = ret_1m[ret_1m < 0].index
        candidates = candidates.drop(neg, errors="ignore")

    # Sector cap
    n_hold = params["n_holdings"]
    cap = params["sector_cap"]
    if cap > 0 and sectors:
        selected = []
        sec_counts = {}
        max_sec = max(1, int(n_hold * cap))
        for t in candidates.index:
            s = sectors.get(t, "Unknown")
            if sec_counts.get(s, 0) < max_sec:
                selected.append(t)
                sec_counts[s] = sec_counts.get(s, 0) + 1
            if len(selected) >= n_hold:
                break
    else:
        selected = list(candidates.index[:n_hold])

    if not selected:
        return pd.Series(dtype=float), []

    # Weighting
    ns = len(selected)
    w = params["weighting"]
    if w == "equal":
        weights = pd.Series(1.0 / ns, index=selected)
    elif w == "momentum":
        ms = mom.loc[selected]
        shifted = ms - ms.min() + 1
        weights = shifted / shifted.sum()
    elif w == "qm_composite":
        cr = composite.loc[selected]
        inv = 1.0 / cr
        weights = inv / inv.sum()
    else:
        weights = pd.Series(1.0 / ns, index=selected)

    return weights, selected


# ============================================================================
# QUALITY PREMIUM MEASUREMENT
# ============================================================================

def measure_quality_premium(monthly_ret, monthly_prices, daily_returns,
                            sectors, params, date_idx, n_forward=3, allowed=None):
    """
    At a given rebalance date, measure whether high-FIP stocks outperform
    low-FIP stocks over the next n_forward months.

    This is the quality filter metric: if high-FIP consistently beats low-FIP,
    the FIP quality dimension is "working."

    Returns: quality_premium (high FIP return - low FIP return, annualized %)
             or None if not enough data.
    """
    if date_idx + n_forward >= len(monthly_prices):
        return None

    hist_daily = daily_returns.iloc[:date_idx * 21]  # approximate
    if len(hist_daily) < 40:
        return None

    fip = calculate_fip(hist_daily, params["fip_lookback_days"],
                        params["fip_pct_positive_weight"])
    fip_clean = fip.dropna()
    # Restrict to point-in-time members (same universe the strategy can trade) so the
    # diagnostic isn't polluted by noisy non-member / illiquid series.
    if allowed is not None:
        fip_clean = fip_clean[fip_clean.index.isin(list(allowed))]

    if len(fip_clean) < 20:
        return None

    # Split into top and bottom quintile by FIP
    q80 = fip_clean.quantile(0.8)
    q20 = fip_clean.quantile(0.2)
    high_fip = fip_clean[fip_clean >= q80].index
    low_fip = fip_clean[fip_clean <= q20].index

    # Forward returns (clip absurd single-month glitches from sparse old data)
    forward_rets = monthly_ret.iloc[date_idx + 1: date_idx + 1 + n_forward].clip(-0.95, 2.0)
    if len(forward_rets) == 0:
        return None

    high_ret = forward_rets[high_fip.intersection(forward_rets.columns)].mean(axis=1).sum()
    low_ret = forward_rets[low_fip.intersection(forward_rets.columns)].mean(axis=1).sum()

    return (high_ret - low_ret) * 100  # percentage


# ============================================================================
# BACKTESTING ENGINE
# ============================================================================

def backtest(prices, sectors, params, start_year=2015, membership=None,
             return_series=False, regime_filter=False):
    """
    Walk-forward backtest of the QM strategy.

    Returns dict with:
      - sharpe_ratio: risk-adjusted returns
      - quality_premium: avg outperformance of high-FIP vs low-FIP stocks
      - composite_metric: sharpe - penalty if quality doesn't work
      - standard performance metrics
    """
    daily_returns = prices.pct_change()
    monthly = prices.resample("ME").last()
    monthly_ret = monthly.pct_change()

    lookback = params["lookback_months"]
    skip = params["skip_months"]
    warmup = lookback + skip + 2

    # Rebalance schedule
    if params["rebalance_freq"] == "quarterly":
        rebal_months = [3, 6, 9, 12]
    else:
        rebal_months = list(range(1, 13))

    # SPY benchmark — Polygon primary, yfinance fallback
    spy_start = f"{start_year-2}-01-01"
    spy_end = datetime.now().strftime("%Y-%m-%d")
    spy_close = None
    s = _yahoo_v8_closes("SPY", spy_start, spy_end, requests.Session())
    if s is not None and len(s):
        spy_close = s
    if spy_close is None:
        key = _poly_key()
        if key:
            s = _poly_ticker_closes("SPY", spy_start, spy_end, key, requests.Session())
            if s is not None and len(s):
                spy_close = s
    if spy_close is None:
        try:
            spy = yf.download("SPY", start=spy_start, end=spy_end,
                              auto_adjust=True, progress=False)
            if isinstance(spy.columns, pd.MultiIndex):
                spy_close = spy["Close"]["SPY"]
            elif "Close" in spy.columns:
                spy_close = spy["Close"]
            else:
                spy_close = spy.iloc[:, 0]
            if isinstance(spy_close, pd.DataFrame):
                spy_close = spy_close.iloc[:, 0]
        except Exception:
            spy_close = None
    if spy_close is not None and len(spy_close):
        spy_mret = spy_close.resample("ME").last().pct_change()
    else:
        spy_mret = pd.Series(dtype=float)

    # Regime filter: SPY vs its 200-day MA, assessed at the PRIOR month-end (no lookahead).
    # When risk-off (SPY < 200DMA) the portfolio sits in cash (0% that month).
    spy_ma200 = (spy_close.rolling(200).mean()
                 if spy_close is not None and len(spy_close) else None)

    def regime_on_at(d):
        if not regime_filter or spy_ma200 is None:
            return True
        px = spy_close.asof(d)
        ma = spy_ma200.asof(d)
        if pd.isna(px) or pd.isna(ma):
            return True
        return px >= ma

    port_returns = []
    port_dates = []
    bench_returns = []
    quality_premiums = []
    current_weights = pd.Series(dtype=float)

    for i in range(warmup, len(monthly)):
        date = monthly.index[i]
        if date.year < start_year:
            continue

        should_rebal = (date.month in rebal_months) or len(current_weights) == 0

        if should_rebal:
            hist_m = monthly.iloc[:i]
            # Use daily data only THROUGH THE PRIOR MONTH-END — never the current month
            # we're about to earn (the current-month leak inflated FIP/Sharpe massively,
            # especially with monthly rebalance + fip_weight=1.0).
            prior_month_end = monthly.index[i - 1]
            hist_d = daily_returns.loc[:prior_month_end]

            if len(hist_m) >= lookback + skip + 1:
                try:
                    mom, ret_1m = calculate_momentum(hist_m, lookback, skip)
                    fip = calculate_fip(hist_d, params["fip_lookback_days"],
                                        params["fip_pct_positive_weight"])
                    allowed = members_on(membership, date) if membership else None
                    current_weights, _ = select_portfolio(
                        mom, fip, ret_1m, sectors, params, allowed=allowed
                    )

                    # Measure quality premium at this rebalance point
                    qp = measure_quality_premium(
                        monthly_ret, monthly, daily_returns,
                        sectors, params, i, allowed=allowed
                    )
                    if qp is not None:
                        quality_premiums.append(qp)

                except Exception as e:
                    print(f"  Rebalance error at {date}: {e}", file=sys.stderr)

        # Monthly portfolio return
        if len(current_weights) > 0 and i < len(monthly_ret):
            mr = monthly_ret.iloc[i]
            pr = 0.0
            for t in current_weights.index:
                try:
                    tr = mr[t] if t in mr.index else np.nan
                    if isinstance(tr, pd.Series):
                        tr = tr.iloc[0]
                    if not np.isnan(tr):
                        pr += current_weights[t] * tr
                except Exception:
                    pass

            # Stop loss
            if params["stop_loss_pct"] > 0 and pr < -params["stop_loss_pct"]:
                pr = -params["stop_loss_pct"]

            # Regime filter: if SPY was below its 200DMA at the prior month-end, hold cash.
            if regime_filter and i >= 1 and not regime_on_at(monthly.index[i - 1]):
                pr = 0.0

            port_returns.append(pr)
            port_dates.append(date)

            # Benchmark
            try:
                si = spy_mret.index
                cl = si[si.get_indexer([date], method="nearest")[0]]
                br = spy_mret.iloc[spy_mret.index.get_loc(cl)]
                if isinstance(br, pd.Series):
                    br = br.iloc[0]
                if not np.isnan(br):
                    bench_returns.append(br)
            except Exception:
                pass

    if not port_returns:
        return {"sharpe_ratio": -999, "quality_premium": 0, "composite_metric": -999,
                "error": "No returns generated"}

    # ================================================================
    # METRICS
    # ================================================================
    rets = pd.Series(port_returns)
    cumulative = (1 + rets).prod()
    n_years = len(rets) / 12
    annual_return = cumulative ** (1 / max(n_years, 0.01)) - 1
    annual_vol = rets.std() * np.sqrt(12)
    sharpe = (annual_return - 0.04) / max(annual_vol, 0.001)

    cum_rets = (1 + rets).cumprod()
    max_dd = ((cum_rets - cum_rets.cummax()) / cum_rets.cummax()).min()

    # Benchmark
    if bench_returns:
        br = pd.Series(bench_returns)
        ba = (1 + br).prod() ** (1 / max(len(br) / 12, 0.01)) - 1
        excess = annual_return - ba
    else:
        ba = 0
        excess = annual_return

    # Quality premium: average high-FIP minus low-FIP forward returns
    avg_qp = np.mean(quality_premiums) if quality_premiums else 0.0

    # COMPOSITE METRIC: Sharpe with quality penalty
    # If quality premium is negative (FIP doesn't help), penalize the Sharpe
    # Penalty = 0.5 * abs(quality_premium) when negative, 0 when positive
    quality_penalty = 0.5 * abs(avg_qp) if avg_qp < 0 else 0.0
    composite_metric = sharpe - quality_penalty

    result = {
        "sharpe_ratio": round(sharpe, 4),
        "annual_return": round(annual_return * 100, 2),
        "annual_vol": round(annual_vol * 100, 2),
        "max_drawdown": round(max_dd * 100, 2),
        "total_return": round((cumulative - 1) * 100, 2),
        "excess_return": round(excess * 100, 2),
        "benchmark_annual": round(ba * 100, 2),
        "n_months": len(rets),
        "n_years": round(n_years, 1),
        "quality_premium": round(avg_qp, 4),
        "quality_penalty": round(quality_penalty, 4),
        "composite_metric": round(composite_metric, 4),
        "n_quality_observations": len(quality_premiums),
        "params": params,
    }

    if return_series:
        result["_returns"] = port_returns
        result["_dates"] = [str(pd.Timestamp(d).date()) for d in port_dates]

    return result


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--backtest", action="store_true")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--out", type=str, default=None)
    parser.add_argument("--params-json", type=str, default=None)
    parser.add_argument("--start-year", type=int, default=2015)
    args = parser.parse_args()

    params = PARAMS.copy()
    if args.params_json:
        params.update(json.loads(args.params_json))

    if args.backtest:
        # Sectors (best-effort, current GICS) for the optional sector cap.
        try:
            _, sectors = get_sp500_tickers()
        except Exception:
            sectors = {}

        # LOCAL-FIRST: use the cached daily panel + point-in-time membership if present.
        prices = load_local_prices()
        membership = load_pit_membership()
        if prices is not None:
            print(f"Using LOCAL panel: {prices.shape[1]} tickers, "
                  f"{prices.index.min().date()}..{prices.index.max().date()}", file=sys.stderr)
        else:
            tickers, sectors = get_sp500_tickers()
            start_dt = f"{args.start_year - 2}-01-01"
            end_dt = datetime.now().strftime("%Y-%m-%d")
            print(f"No local panel; downloading ({start_dt} to {end_dt})...", file=sys.stderr)
            prices = download_prices(tickers, start_dt, end_dt)

        if membership:
            print(f"PIT membership: {len(membership)} change-dates "
                  f"({membership[0][0].date()}..{membership[-1][0].date()}) "
                  f"-> per-rebalance universe filter ON", file=sys.stderr)
        else:
            print("No PIT membership file -> using full panel as universe", file=sys.stderr)

        print(f"Running QM backtest (start={args.start_year})...", file=sys.stderr)
        result = backtest(prices, sectors, params, start_year=args.start_year,
                          membership=membership)

        # Metric lines for autoresearch harness
        print(f"METRIC:sharpe_ratio={result['sharpe_ratio']}")
        print(f"METRIC:quality_premium={result['quality_premium']}")
        print(f"METRIC:composite_metric={result['composite_metric']}")

        print(json.dumps(result, indent=2))

        if args.out:
            with open(args.out, "w") as f:
                json.dump(result, f, indent=2)

    elif args.live:
        print("Live mode not yet wired — use qm_screener.py for live screening.", file=sys.stderr)
        sys.exit(1)
    else:
        print("Usage: python qm_strategy.py --backtest or --live")
