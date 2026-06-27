"""
qm_screener.py — Quantitative Momentum live screener for S&P 500 stocks.

Implements Wes Gray & Jack Vogel's Quantitative Momentum methodology:
  1. Raw 6-1 month momentum (skip most recent month to avoid reversal)
  2. FIP (Frog-in-the-Pan) composite quality score:
     - Percent positive days (consistency)
     - Path smoothness / R-squared (linearity of cumulative returns)
  3. Composite QM rank = intersection of high raw momentum AND high FIP quality

Output: JSON to stdout + CSV files in the output directory.
"""

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
    """Fetch one trading day of grouped daily bars (~12k US tickers) from Polygon.

    Returns a DataFrame with Polygon's raw columns (T, c, o, h, l, v, ...) on
    a trading day, or an empty DataFrame on a closed day. Returns None on HTTP error."""
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
        else:
            print(f"  Polygon HTTP {r.status_code} for {date_str}", file=sys.stderr)
        return None
    j = r.json()
    if j.get("status") != "OK" or not j.get("results"):
        return pd.DataFrame()  # closed day or empty
    return pd.DataFrame(j["results"])


def download_prices_polygon(tickers, months_needed=8, cache_dir=None):
    """Build a price DataFrame (date × ticker, adjusted close) via Polygon Grouped Daily Bars.

    One API call per trading day fetches the entire US stock universe; we filter
    to the requested tickers and pivot to a wide DataFrame. Per-day responses are
    cached as parquet so subsequent runs only fetch the new days.
    """
    api_key = get_polygon_api_key()
    if not api_key:
        raise RuntimeError("No Polygon API key in keyring (polygon-api/default) or POLYGON_API_KEY env var")

    if cache_dir is None:
        cache_dir = os.path.join(os.path.expanduser("~"), ".qm-cache", "polygon_daily")
    os.makedirs(cache_dir, exist_ok=True)

    end = datetime.now()
    start = end - timedelta(days=months_needed * 31 + 30)
    bdates = pd.bdate_range(start, end)
    ticker_set = set(tickers)

    session = requests.Session()
    rows = []
    cached, fetched, skipped = 0, 0, 0
    print(f"Polygon: requesting {len(bdates)} business days "
          f"({start.date()} to {end.date()})...", file=sys.stderr)

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
# S&P 500 UNIVERSE
# ============================================================================

def get_sp500_tickers():
    """Fetch current S&P 500 constituents from Wikipedia, with full fallback list.

    Wikipedia blocks the default urllib User-Agent (HTTP 403), so we fetch with
    requests using a real UA, then hand the HTML to pandas.
    """
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
    except Exception as e:
        print(f"Warning: Wikipedia fetch failed ({e}), using fallback list", file=sys.stderr)
        fallback = [
            "NVDA","GOOGL","AAPL","GOOG","MSFT","AMZN","META","AVGO","TSLA","BRK-B",
            "WMT","LLY","JPM","XOM","V","JNJ","MU","MA","COST","ORCL","CVX","NFLX",
            "ABBV","PLTR","BAC","PG","AMD","KO","HD","CAT","CSCO","GE","LRCX","AMAT",
            "MRK","RTX","MS","PM","UNH","GS","WFC","TMUS","GEV","IBM","LIN","MCD",
            "INTC","VZ","PEP","AXP","T","KLAC","C","AMGN","NEE","ABT","CRM","DIS",
            "TMO","TJX","GILD","TXN","ISRG","SCHW","ANET","APH","COP","PFE","BA",
            "UBER","DE","ADI","APP","BLK","LMT","HON","UNP","QCOM","ETN","BKNG",
            "WELL","DHR","PANW","SYK","SPGI","LOW","INTU","CB","ACN","PGR","PLD",
            "BMY","NOW","VRTX","PH","COF","MDT","HCA","CME","MCK","MO","GLW","SBUX",
            "SO","CMCSA","NEM","CRWD","BSX","CEG","ADBE","DELL","NOC","WDC","DUK",
            "EQIX","GD","WM","HWM","NRG","CVS","TT","ICE","STX","WMB","FDX","MAR",
            "ADP","PWR","AMT","BX","UPS","PNC","SNPS","KKR","USB","JCI","BK","ABNB",
            "NKE","REGN","CDNS","MCO","SHW","MSI","FCX","EOG","MMM","ITW","CMI",
            "ORLY","KMI","ECL","MNST","MDLZ","EMR","VLO","CTAS","RCL","CSX","PSX",
            "AON","SLB","CI","ROST","MPC","CL","DASH","WBD","RSG","AEP","CRH","HLT",
            "TDG","LHX","GM","APO","ELV","TRV","HOOD","COR","NSC","APD","FTNT","SPG",
            "SRE","OXY","BKR","DLR","PCAR","TEL","O","OKE","AJG","TFC","AFL","FANG",
            "CIEN","AZO","ALL","MPWR","ADSK","D","COIN","CTVA","TGT","TRGP","FAST",
            "EA","GWW","VST","NDAQ","CAH","ZTS","CARR","NXPI","AME","EW","XEL","FIX",
            "KEYS","EXC","PSA","IDXX","F","TER","ETR","KR","URI","GRMN","MET","DDOG",
            "BDX","CMG","YUM","HSY","DAL","MSCI","PYPL","EQT","WAB","CVNA","AMP",
            "AIG","ROK","EBAY","FITB","PEG","ED","VTR","AXON","CBRE","SYY","DHI",
            "ODFL","TTWO","HIG","WEC","ROP","NUE","KDP","CCI","TPL","LVS","LYV",
            "WDAY","MCHP","STT","MLM","VMC","KVUE","PAYX","RMD","ACGL","KMB","PRU",
            "EME","IR","ADM","GEHC","CPRT","A","EL","OTIS","HAL","FISV","DVN","ATO",
            "CCL","CBOE","CTSH","MTB","IRM","DTE","WAT","AEE","XYL","IBKR","UAL",
            "EXPE","HPE","VICI","TDY","TPR","RJF","DOV","IQV","FE","VRSK","WTW",
            "EXR","PPL","CNP","DG","CHTR","EIX","FICO","JBL","BIIB","AWK","DOW",
            "STZ","CTRA","DXCM","ROL","FIS","KHC","HUBB","NTRS","ES","CINF","WRB",
            "FOXA","MTD","CFG","TSCO","ARES","STLD","LYB","ULTA","DRI","ON","OMC",
            "SYF","BG","BRO","CMS","AVB","CHD","LEN","FOX","VRSN","PHM","VLTO",
            "RF","EQR","L","PPG","LH","STE","NI","DGX","EFX","WSM","KEY","LDOS",
            "DLTR","FSLR","HUM","TSN","BR","MRNA","CHRW","RL","NTAP","GIS","CPAY",
            "EXPD","LUV","CF","GPN","SW","JBHT","TROW","SNA","ALB","PFG","SBAC",
            "EVRG","PKG","INCY","CSGP","LULU","IP","PTC","NVR","AMCR","LNT","ZBH",
            "DD","WST","IFF","FTV","CNC","HOLX","HPQ","LII","WY","FFIV","HII","AKAM",
            "PODD","CDW","ESS","TXT","TRMB","VTRS","BALL","J","KIM","TYL","INVH",
            "TKO","NDSN","APTV","MKC","DECK","MAA","PNR","APA","REG","IEX","COO",
            "GPC","NWSA","BBY","CLX","HAS","HST","EG","GEN","ERIE","DPZ","AVY",
            "ALGN","SMCI","ALLE","BEN","HRL","MAS","JKHY","DOC","PNW","GNRC","TTD",
            "GDDY","SOLV","IT","UHS","UDR","GL","SJM","AIZ","BF-B","SWK","WYNN",
            "IVZ","CPT","AES","ZBRA","DVA","RVTY","MGM","BLDR","FRT","AOS","NCLH",
            "BAX","HSIC","BXP","ARE","SWKS","TECH","FDS","CRL","MOS","EPAM","TAP",
            "POOL","CAG","MTCH","MOH","PAYC","CPB","LW","PCG","NWS","HBAN",
        ]
        # Fallback list: don't fetch per-ticker info from yfinance — it triggers
        # rate-limit bans that cascade into the price download. Display fields
        # default to ticker / "Unknown"; users can re-run later for live names.
        sectors = {t: "Unknown" for t in fallback}
        names = {t: t for t in fallback}
        print("  Using ticker symbols as company names (skipping per-ticker info to avoid rate limits)",
              file=sys.stderr)
        return fallback, sectors, names


def download_prices_yahoo(tickers, months_needed=8):
    """Download adjusted close prices for all tickers via yfinance (fallback path)."""
    end = datetime.now()
    start = end - timedelta(days=months_needed * 31 + 30)

    print(f"Yahoo: downloading price data for {len(tickers)} tickers...", file=sys.stderr)
    data = yf.download(
        tickers, start=start.strftime("%Y-%m-%d"),
        end=end.strftime("%Y-%m-%d"), auto_adjust=True,
        progress=False, threads=True
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


def download_prices(tickers, months_needed=8):
    """Get adjusted close prices for all tickers.

    Tries Polygon Grouped Daily Bars first (paid plan, no rate-limit issues,
    cached per-day so subsequent runs are fast). Falls back to yfinance if
    Polygon is unavailable or returns insufficient data.
    """
    if get_polygon_api_key():
        try:
            prices = download_prices_polygon(tickers, months_needed=months_needed)
            if not prices.empty and prices.shape[0] >= months_needed * 18:
                return prices
            print(f"Polygon returned only {prices.shape[0]} days "
                  f"(need ~{months_needed * 21}) — falling back to Yahoo", file=sys.stderr)
        except Exception as e:
            print(f"Polygon path failed ({e}) — falling back to Yahoo", file=sys.stderr)
    else:
        print("No Polygon API key found — using Yahoo only", file=sys.stderr)

    return download_prices_yahoo(tickers, months_needed=months_needed)


# ============================================================================
# FIP (FROG-IN-THE-PAN) QUALITY SCORE
# ============================================================================

def calculate_fip_score(daily_returns, lookback_days=126):
    """
    Calculate composite FIP quality score for a single stock.

    Components (equally weighted):
      1. Percent positive days — fraction of trading days with positive returns
      2. Path smoothness (R²) — R² of cumulative returns regressed on time

    Higher FIP = smoother, more consistent momentum path.

    Args:
        daily_returns: Series of daily returns for one stock
        lookback_days: number of trading days to look back (126 ≈ 6 months)

    Returns:
        dict with pct_positive, r_squared, composite_fip
    """
    rets = daily_returns.dropna().tail(lookback_days)

    if len(rets) < 20:
        return {"pct_positive": np.nan, "r_squared": np.nan, "composite_fip": np.nan}

    # Component 1: Percent positive days
    pct_positive = (rets > 0).sum() / len(rets)

    # Component 2: Path smoothness (R-squared)
    cum_rets = (1 + rets).cumprod()
    x = np.arange(len(cum_rets))
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, cum_rets.values)
    r_squared = r_value ** 2

    # Only count R² as quality if the slope is positive (uptrend)
    # A perfectly linear downtrend also has high R² but isn't quality momentum
    if slope < 0:
        r_squared = 0.0

    # Composite FIP = equal weight of both components
    composite_fip = 0.5 * pct_positive + 0.5 * r_squared

    return {
        "pct_positive": round(pct_positive, 4),
        "r_squared": round(r_squared, 4),
        "composite_fip": round(composite_fip, 4),
    }


def calculate_fip_scores_bulk(prices, lookback_days=126):
    """Calculate FIP scores for all tickers in the price DataFrame."""
    daily_returns = prices.pct_change()
    fip_data = {}

    for ticker in prices.columns:
        try:
            rets = daily_returns[ticker].dropna()
            if len(rets) >= 20:
                fip_data[ticker] = calculate_fip_score(rets, lookback_days)
            else:
                fip_data[ticker] = {
                    "pct_positive": np.nan,
                    "r_squared": np.nan,
                    "composite_fip": np.nan,
                }
        except Exception:
            fip_data[ticker] = {
                "pct_positive": np.nan,
                "r_squared": np.nan,
                "composite_fip": np.nan,
            }

    return fip_data


# ============================================================================
# MOMENTUM CALCULATION
# ============================================================================

def calculate_momentum(prices, lookback_months=6, skip_months=1, vol_adjust=True):
    """
    Calculate 6-1 month momentum (or custom lookback-skip combo),
    optionally volatility-adjusted.

    Volatility adjustment (enabled by default based on autoresearch findings):
    Divides raw momentum by annualized realized volatility, so that stocks
    with steady uptrends rank higher than those with volatile spikes.
    This improved Sharpe by ~0.1-0.4 and reduced max drawdown by 5-15pp
    across 20 years of backtesting (2006-2026).

    Returns:
        momentum: Series of percentage returns (or vol-adjusted ratios) for each ticker
        ret_1m: 1-month trailing return
        ret_3m: 3-month trailing return
    """
    daily_returns = prices.pct_change()
    monthly = prices.resample("ME").last()

    if len(monthly) < lookback_months + skip_months + 1:
        raise ValueError(
            f"Not enough monthly data: need {lookback_months + skip_months + 1}, "
            f"have {len(monthly)}"
        )

    # lookback-skip return
    end_price = monthly.iloc[-(skip_months + 1)]
    start_price = monthly.iloc[-(lookback_months + skip_months + 1)]
    momentum = (end_price / start_price - 1) * 100

    # Volatility-adjusted momentum: divide by realized vol so low-vol
    # grinders rank higher than high-vol spikes
    if vol_adjust:
        vol_days = lookback_months * 21  # approx trading days
        recent = daily_returns.tail(vol_days)
        realized_vol = recent.std() * np.sqrt(252) * 100  # annualized %
        realized_vol = realized_vol.clip(lower=5.0)  # floor to avoid tiny-vol distortion
        common = momentum.index.intersection(realized_vol.index)
        momentum = momentum.loc[common] / realized_vol.loc[common]

    # Auxiliary: 1-month and 3-month trailing returns (no skip)
    price_now = monthly.iloc[-1]
    price_1m = monthly.iloc[-2] if len(monthly) >= 2 else price_now
    price_3m = monthly.iloc[-4] if len(monthly) >= 4 else price_now

    ret_1m = (price_now / price_1m - 1) * 100
    ret_3m = (price_now / price_3m - 1) * 100

    return momentum, ret_1m, ret_3m


# ============================================================================
# COMPOSITE QM RANKING
# ============================================================================

def build_qm_ranking(momentum, fip_data, ret_1m, ret_3m, sectors, names, last_close=None):
    """
    Build the full Quantitative Momentum ranking table.

    Ranking methodology:
      1. Rank all stocks by raw 6-1 momentum (descending)
      2. Rank all stocks by composite FIP quality (descending)
      3. Composite QM Rank = average of momentum rank + FIP rank (lower = better)
      4. Assign signals: Strong Buy / Buy / Hold / Sell based on percentile

    Returns:
        DataFrame with full ranking
    """
    # Drop NaNs
    mom_clean = momentum.dropna()
    fip_series = pd.Series({t: fip_data[t]["composite_fip"] for t in mom_clean.index
                            if t in fip_data and not np.isnan(fip_data[t]["composite_fip"])})

    # Only keep tickers that have both momentum and FIP
    common = mom_clean.index.intersection(fip_series.index)
    mom_clean = mom_clean.loc[common]
    fip_series = fip_series.loc[common]

    # Ranks (1 = best)
    mom_rank = mom_clean.rank(ascending=False).astype(int)
    fip_rank = fip_series.rank(ascending=False).astype(int)

    # Composite QM rank = weighted combination (FIP weight 0.75 based on autoresearch)
    # Higher FIP weight means quality/smoothness matters more than raw momentum magnitude.
    # Autoresearch showed FIP weight monotonically improves composite metric (Sharpe + quality).
    fip_weight = 0.75
    composite_rank = ((1 - fip_weight) * mom_rank + fip_weight * fip_rank).rank(method="min").astype(int)

    # Percentile (100 = best)
    n = len(composite_rank)
    percentile = ((n - composite_rank + 1) / n * 100).round(1)

    # Signal assignment
    def assign_signal(pct):
        if pct >= 90:
            return "Strong Buy"
        elif pct >= 70:
            return "Buy"
        elif pct >= 30:
            return "Hold"
        else:
            return "Sell"

    signals = percentile.map(assign_signal)

    # Build DataFrame
    rows = []
    for ticker in composite_rank.sort_values().index:
        fip_info = fip_data.get(ticker, {})
        price_val = None
        if last_close is not None:
            try:
                p = last_close.get(ticker)
                if p is not None and not (isinstance(p, float) and np.isnan(p)):
                    price_val = round(float(p), 2)
            except Exception:
                price_val = None
        rows.append({
            "Rank": composite_rank[ticker],
            "Ticker": ticker,
            "Company": names.get(ticker, ""),
            "Sector": sectors.get(ticker, "Unknown"),
            "Price": price_val,
            "6-1M VolAdj": round(mom_clean[ticker], 2),
            "3M Ret%": round(ret_3m.get(ticker, 0), 2),
            "1M Ret%": round(ret_1m.get(ticker, 0), 2),
            "FIP Score": fip_info.get("composite_fip", np.nan),
            "Pct Positive Days": fip_info.get("pct_positive", np.nan),
            "R-Squared": fip_info.get("r_squared", np.nan),
            "Mom Rank": mom_rank.get(ticker, np.nan),
            "FIP Rank": fip_rank.get(ticker, np.nan),
            "Composite QM Rank": composite_rank[ticker],
            "Percentile": percentile[ticker],
            "Signal": signals[ticker],
        })

    df = pd.DataFrame(rows)
    df = df.sort_values("Rank").reset_index(drop=True)
    return df


# ============================================================================
# MAIN
# ============================================================================

def run_screener(output_dir="."):
    """Run the full QM screener and save results."""
    print("=" * 60, file=sys.stderr)
    print("  Quantitative Momentum Screener", file=sys.stderr)
    print("  Methodology: Wes Gray / Alpha Architect", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    # Step 1: Get universe
    tickers, sectors, names = get_sp500_tickers()
    print(f"Universe: {len(tickers)} S&P 500 stocks", file=sys.stderr)

    # Step 2: Download prices (need ~8 months for 6-1 momentum + FIP lookback)
    prices = download_prices(tickers, months_needed=8)

    # Step 3: Calculate raw momentum
    print("Calculating 6-1 month momentum...", file=sys.stderr)
    momentum, ret_1m, ret_3m = calculate_momentum(prices, lookback_months=6, skip_months=1)

    # Step 4: Calculate FIP quality scores
    print("Calculating FIP quality scores (path smoothness + consistency)...", file=sys.stderr)
    fip_data = calculate_fip_scores_bulk(prices, lookback_days=126)

    # Step 5: Build composite ranking
    print("Building composite QM ranking...", file=sys.stderr)
    last_close = prices.ffill().iloc[-1] if not prices.empty else None
    df = build_qm_ranking(momentum, fip_data, ret_1m, ret_3m, sectors, names, last_close=last_close)

    # Step 6: Save outputs
    csv_full = os.path.join(output_dir, "qm_full_ranking.csv")
    csv_top50 = os.path.join(output_dir, "qm_top50.csv")

    df.to_csv(csv_full, index=False)
    df.head(50).to_csv(csv_top50, index=False)

    print(f"\nSaved full ranking: {csv_full}", file=sys.stderr)
    print(f"Saved top 50: {csv_top50}", file=sys.stderr)

    # Summary stats
    n_analyzed = len(df)
    n_strong_buy = len(df[df["Signal"] == "Strong Buy"])
    n_buy = len(df[df["Signal"] == "Buy"])
    n_hold = len(df[df["Signal"] == "Hold"])
    n_sell = len(df[df["Signal"] == "Sell"])

    summary = {
        "run_date": datetime.now().strftime("%Y-%m-%d"),
        "n_analyzed": n_analyzed,
        "signals": {
            "Strong Buy": n_strong_buy,
            "Buy": n_buy,
            "Hold": n_hold,
            "Sell": n_sell,
        },
        "top_10": df.head(10).to_dict(orient="records"),
    }

    # Print JSON summary to stdout for downstream consumption
    print(json.dumps(summary, indent=2, default=str))

    return df, summary


if __name__ == "__main__":
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(output_dir, exist_ok=True)
    run_screener(output_dir)
