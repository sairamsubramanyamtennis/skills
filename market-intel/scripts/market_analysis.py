#!/usr/bin/env python3
"""
Market Intel — Technical Analysis & Data Gathering Script

Fetches price data, computes technical indicators, checks macro signals,
and performs sector/correlation analysis for a watchlist of stocks.

Usage:
    python market_analysis.py --tickers AAPL MSFT GOOG --output /tmp/market_intel_data.json
"""

import argparse
import json
import sys
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import yfinance as yf


# Sector ETF mapping for the most common stocks
SECTOR_ETFS = {
    "Technology": "XLK",
    "Communication Services": "XLC",
    "Consumer Cyclical": "XLY",
    "Consumer Defensive": "XLP",
    "Energy": "XLE",
    "Financial Services": "XLF",
    "Healthcare": "XLV",
    "Industrials": "XLI",
    "Basic Materials": "XLB",
    "Real Estate": "XLRE",
    "Utilities": "XLU",
}


def compute_rsi(series: pd.Series, period: int = 14) -> float:
    """Compute RSI for the most recent value."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(float(rsi.iloc[-1]), 2) if not rsi.empty else None


def compute_macd(series: pd.Series) -> dict:
    """Compute MACD line, signal line, and histogram."""
    ema12 = series.ewm(span=12, adjust=False).mean()
    ema26 = series.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    histogram = macd_line - signal_line
    return {
        "macd_line": round(float(macd_line.iloc[-1]), 4),
        "signal_line": round(float(signal_line.iloc[-1]), 4),
        "histogram": round(float(histogram.iloc[-1]), 4),
        "signal": "Bullish" if histogram.iloc[-1] > 0 else "Bearish",
    }


def compute_volume_zscore(volume: pd.Series, window: int = 30) -> float:
    """How unusual today's volume is relative to the trailing window."""
    mean_vol = volume.rolling(window).mean()
    std_vol = volume.rolling(window).std()
    if std_vol.iloc[-1] == 0:
        return 0.0
    z = (volume.iloc[-1] - mean_vol.iloc[-1]) / std_vol.iloc[-1]
    return round(float(z), 2)


def compute_volatility_alert(returns: pd.Series, window: int = 30) -> dict:
    """Check if today's return is >2σ from trailing mean."""
    mean_ret = returns.rolling(window).mean().iloc[-1]
    std_ret = returns.rolling(window).std().iloc[-1]
    today_ret = returns.iloc[-1]
    if std_ret == 0:
        return {"alert": False, "z_score": 0.0}
    z = (today_ret - mean_ret) / std_ret
    return {
        "alert": abs(z) > 2.0,
        "z_score": round(float(z), 2),
        "today_return_pct": round(float(today_ret * 100), 2),
        "threshold_2sigma_pct": round(float(std_ret * 2 * 100), 2),
    }


def compute_correlation(stock_returns: pd.Series, benchmark_returns: pd.Series, window: int = 30) -> dict:
    """Rolling correlation and recent shift detection."""
    rolling_corr = stock_returns.rolling(window).corr(benchmark_returns)
    current_corr = float(rolling_corr.iloc[-1]) if not np.isnan(rolling_corr.iloc[-1]) else None
    prev_corr = float(rolling_corr.iloc[-window]) if len(rolling_corr) > window and not np.isnan(rolling_corr.iloc[-window]) else None
    shift = None
    if current_corr is not None and prev_corr is not None:
        shift = round(current_corr - prev_corr, 3)
    return {
        "current_30d_corr": round(current_corr, 3) if current_corr else None,
        "prev_30d_corr": round(prev_corr, 3) if prev_corr else None,
        "shift": shift,
        "significant_shift": abs(shift) > 0.3 if shift else False,
    }


def get_sector_for_ticker(ticker_obj) -> str:
    """Get sector from yfinance info, with fallback."""
    try:
        info = ticker_obj.info
        return info.get("sector", "Unknown")
    except Exception:
        return "Unknown"


def analyze_ticker(symbol: str, hist: pd.DataFrame, spy_returns: pd.Series, sector_etf_data: dict) -> dict:
    """Run full analysis for a single ticker."""
    result = {"symbol": symbol}

    if hist.empty or len(hist) < 30:
        result["error"] = f"Insufficient data for {symbol} (got {len(hist)} days, need 30+)"
        return result

    close = hist["Close"]
    volume = hist["Volume"]
    returns = close.pct_change().dropna()

    # Current price and daily change
    result["price"] = round(float(close.iloc[-1]), 2)
    result["prev_close"] = round(float(close.iloc[-2]), 2) if len(close) > 1 else None
    result["change_pct"] = round(float(returns.iloc[-1] * 100), 2) if len(returns) > 0 else None
    result["volume"] = int(volume.iloc[-1])
    result["avg_volume_30d"] = int(volume.tail(30).mean())

    # Technical indicators
    result["rsi_14"] = compute_rsi(close)
    rsi = result["rsi_14"]
    result["rsi_signal"] = "Overbought" if rsi and rsi > 70 else ("Oversold" if rsi and rsi < 30 else "Neutral")

    result["ma_50"] = round(float(close.tail(50).mean()), 2) if len(close) >= 50 else None
    result["ma_200"] = round(float(close.tail(200).mean()), 2) if len(close) >= 200 else None
    result["above_ma50"] = bool(close.iloc[-1] > result["ma_50"]) if result["ma_50"] else None
    result["above_ma200"] = bool(close.iloc[-1] > result["ma_200"]) if result["ma_200"] else None

    result["macd"] = compute_macd(close)

    # Volume analysis
    result["volume_zscore"] = compute_volume_zscore(volume)
    vz = result["volume_zscore"]
    result["volume_signal"] = "Spike" if vz > 2 else ("Elevated" if vz > 1 else ("Low" if vz < -1 else "Normal"))

    # Volatility alert
    result["volatility_alert"] = compute_volatility_alert(returns)

    # Sector comparison
    ticker_obj = yf.Ticker(symbol)
    sector = get_sector_for_ticker(ticker_obj)
    result["sector"] = sector
    sector_etf_symbol = SECTOR_ETFS.get(sector)
    result["sector_etf"] = sector_etf_symbol

    if sector_etf_symbol and sector_etf_symbol in sector_etf_data:
        sec_close = sector_etf_data[sector_etf_symbol]
        sec_returns = sec_close.pct_change().dropna()

        # 1-week and 1-month relative performance
        if len(close) >= 5 and len(sec_close) >= 5:
            stock_1w = float((close.iloc[-1] / close.iloc[-5] - 1) * 100)
            sector_1w = float((sec_close.iloc[-1] / sec_close.iloc[-5] - 1) * 100)
            result["rel_perf_1w"] = round(stock_1w - sector_1w, 2)
        if len(close) >= 21 and len(sec_close) >= 21:
            stock_1m = float((close.iloc[-1] / close.iloc[-21] - 1) * 100)
            sector_1m = float((sec_close.iloc[-1] / sec_close.iloc[-21] - 1) * 100)
            result["rel_perf_1m"] = round(stock_1m - sector_1m, 2)

        # Correlation with sector
        aligned = pd.concat([returns, sec_returns], axis=1, join="inner")
        if len(aligned) >= 30:
            aligned.columns = ["stock", "sector"]
            result["sector_correlation"] = compute_correlation(aligned["stock"], aligned["sector"])

    # Correlation with SPY
    aligned_spy = pd.concat([returns, spy_returns], axis=1, join="inner")
    if len(aligned_spy) >= 30:
        aligned_spy.columns = ["stock", "spy"]
        result["spy_correlation"] = compute_correlation(aligned_spy["stock"], aligned_spy["spy"])

    # Earnings and dividends (from yfinance)
    try:
        cal = ticker_obj.calendar
        if cal is not None and not (isinstance(cal, pd.DataFrame) and cal.empty):
            if isinstance(cal, dict):
                result["next_earnings"] = str(cal.get("Earnings Date", [None])[0]) if cal.get("Earnings Date") else None
                result["ex_dividend_date"] = str(cal.get("Ex-Dividend Date", None))
            elif isinstance(cal, pd.DataFrame):
                if "Earnings Date" in cal.index:
                    result["next_earnings"] = str(cal.loc["Earnings Date"].iloc[0])
                if "Ex-Dividend Date" in cal.index:
                    result["ex_dividend_date"] = str(cal.loc["Ex-Dividend Date"].iloc[0])
    except Exception:
        result["next_earnings"] = None
        result["ex_dividend_date"] = None

    return result


def get_macro_snapshot() -> dict:
    """Fetch macro indicators: 10Y yield, VIX, DXY."""
    macro = {}
    end = datetime.now()
    start = end - timedelta(days=30)

    for symbol, name in [("^TNX", "treasury_10y"), ("^VIX", "vix"), ("DX-Y.NYB", "dxy")]:
        try:
            data = yf.download(symbol, start=start, end=end, progress=False)
            if not data.empty:
                close = data["Close"]
                if hasattr(close, "columns"):
                    close = close.iloc[:, 0]
                macro[name] = {
                    "value": round(float(close.iloc[-1]), 2),
                    "change_1w": round(float((close.iloc[-1] / close.iloc[-5] - 1) * 100), 2) if len(close) >= 5 else None,
                }
        except Exception as e:
            macro[name] = {"error": str(e)}

    # VIX interpretation
    if "vix" in macro and "value" in macro["vix"]:
        v = macro["vix"]["value"]
        macro["vix"]["level"] = "Low" if v < 15 else ("Moderate" if v < 20 else ("Elevated" if v < 30 else "High"))

    return macro


def main():
    parser = argparse.ArgumentParser(description="Market Intel Analysis")
    parser.add_argument("--tickers", nargs="+", required=True, help="Stock tickers to analyze")
    parser.add_argument("--output", required=True, help="Output JSON file path")
    args = parser.parse_args()

    tickers = [t.upper() for t in args.tickers]
    end = datetime.now()
    start = end - timedelta(days=250)  # ~1 year for 200-day MA

    print(f"Fetching data for: {', '.join(tickers)}")

    # Fetch all stock data
    all_data = yf.download(tickers + ["SPY"], start=start, end=end, progress=False, group_by="ticker")

    # Extract SPY returns
    if len(tickers) == 1 and "SPY" not in tickers:
        # When downloading 2 tickers, data is grouped by ticker
        spy_close = all_data["SPY"]["Close"]
    elif len(tickers) > 1:
        spy_close = all_data["SPY"]["Close"]
    else:
        # Single ticker that happens to be SPY
        spy_close = all_data["Close"]

    if hasattr(spy_close, "columns"):
        spy_close = spy_close.iloc[:, 0]
    spy_returns = spy_close.pct_change().dropna()

    # Determine needed sector ETFs
    needed_sectors = set()
    for t in tickers:
        try:
            sector = yf.Ticker(t).info.get("sector", "Unknown")
            etf = SECTOR_ETFS.get(sector)
            if etf:
                needed_sectors.add(etf)
        except Exception:
            pass

    # Fetch sector ETF data
    sector_etf_data = {}
    if needed_sectors:
        sector_list = list(needed_sectors)
        try:
            sec_data = yf.download(sector_list, start=start, end=end, progress=False, group_by="ticker")
            for etf in sector_list:
                try:
                    if len(sector_list) == 1:
                        sec_close = sec_data["Close"]
                    else:
                        sec_close = sec_data[etf]["Close"]
                    if hasattr(sec_close, "columns"):
                        sec_close = sec_close.iloc[:, 0]
                    sector_etf_data[etf] = sec_close
                except Exception:
                    pass
        except Exception:
            pass

    # Analyze each ticker
    results = {"date": end.strftime("%Y-%m-%d"), "tickers": {}}

    for t in tickers:
        print(f"Analyzing {t}...")
        try:
            if len(tickers + ["SPY"]) == 2:
                # 2-ticker download: columns are MultiIndex (metric, ticker)
                hist = all_data[t] if t != "SPY" else all_data
            else:
                hist = all_data[t]
            if isinstance(hist, pd.DataFrame) and hist.empty:
                results["tickers"][t] = {"error": "No data returned"}
                continue
        except (KeyError, Exception):
            results["tickers"][t] = {"error": "Failed to extract data"}
            continue

        results["tickers"][t] = analyze_ticker(t, hist, spy_returns, sector_etf_data)

    # Macro snapshot
    print("Fetching macro data...")
    results["macro"] = get_macro_snapshot()

    # Write output
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"Analysis complete. Output written to {args.output}")


if __name__ == "__main__":
    main()
