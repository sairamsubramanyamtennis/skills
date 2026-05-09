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
    """Download adjusted close prices."""
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
# PORTFOLIO CONSTRUCTION
# ============================================================================

def select_portfolio(momentum, fip, ret_1m, sectors, params):
    """
    Select and weight the portfolio using composite QM rank.
    Returns: (weights Series, selected tickers list)
    """
    common = momentum.dropna().index.intersection(fip.dropna().index)
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
                            sectors, params, date_idx, n_forward=3):
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

    if len(fip_clean) < 20:
        return None

    # Split into top and bottom quintile by FIP
    q80 = fip_clean.quantile(0.8)
    q20 = fip_clean.quantile(0.2)
    high_fip = fip_clean[fip_clean >= q80].index
    low_fip = fip_clean[fip_clean <= q20].index

    # Forward returns
    forward_rets = monthly_ret.iloc[date_idx + 1: date_idx + 1 + n_forward]
    if len(forward_rets) == 0:
        return None

    high_ret = forward_rets[high_fip.intersection(forward_rets.columns)].mean(axis=1).sum()
    low_ret = forward_rets[low_fip.intersection(forward_rets.columns)].mean(axis=1).sum()

    return (high_ret - low_ret) * 100  # percentage


# ============================================================================
# BACKTESTING ENGINE
# ============================================================================

def backtest(prices, sectors, params, start_year=2015):
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

    # SPY benchmark
    try:
        spy = yf.download("SPY", start=f"{start_year-2}-01-01",
                           end=datetime.now().strftime("%Y-%m-%d"),
                           auto_adjust=True, progress=False)
        if isinstance(spy.columns, pd.MultiIndex):
            spy_close = spy["Close"]["SPY"]
        elif "Close" in spy.columns:
            spy_close = spy["Close"]
        else:
            spy_close = spy.iloc[:, 0]
        if isinstance(spy_close, pd.DataFrame):
            spy_close = spy_close.iloc[:, 0]
        spy_mret = spy_close.resample("ME").last().pct_change()
    except Exception:
        spy_mret = pd.Series(dtype=float)

    port_returns = []
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
            hist_d = daily_returns.loc[:date]

            if len(hist_m) >= lookback + skip + 1:
                try:
                    mom, ret_1m = calculate_momentum(hist_m, lookback, skip)
                    fip = calculate_fip(hist_d, params["fip_lookback_days"],
                                        params["fip_pct_positive_weight"])
                    current_weights, _ = select_portfolio(
                        mom, fip, ret_1m, sectors, params
                    )

                    # Measure quality premium at this rebalance point
                    qp = measure_quality_premium(
                        monthly_ret, monthly, daily_returns,
                        sectors, params, i
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

            port_returns.append(pr)

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
        tickers, sectors = get_sp500_tickers()
        months_needed = max(params["lookback_months"] + 2, 14) + (2026 - args.start_year) * 12 + 24
        start_dt = f"{args.start_year - 2}-01-01"
        end_dt = datetime.now().strftime("%Y-%m-%d")

        print(f"Downloading S&P 500 data ({start_dt} to {end_dt})...", file=sys.stderr)
        prices = download_prices(tickers, start_dt, end_dt)

        print(f"Running QM backtest (start={args.start_year})...", file=sys.stderr)
        result = backtest(prices, sectors, params, start_year=args.start_year)

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
