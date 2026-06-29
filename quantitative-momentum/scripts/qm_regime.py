"""
qm_regime.py — SPY 200-day moving-average regime filter (#3, momentum-crash guard).

Cross-sectional momentum gets hurt in regime flips (2009, 2022). A simple absolute-
momentum overlay — only go long when SPY > its 200-day SMA, else raise cash — is the
best-documented drawdown reducer for this strategy.

Returns a regime dict: risk-on (SPY >= 200DMA) or risk-off (SPY < 200DMA).
Price source: Polygon per-ticker daily aggs (primary), yfinance (fallback).

CLI:  python qm_regime.py            # prints JSON regime
"""
import json
import sys
import os
from datetime import datetime, timedelta

import pandas as pd
import requests

# Reuse the screener's Polygon key resolver (keyring -> env)
try:
    from qm_screener import get_polygon_api_key
except Exception:
    def get_polygon_api_key():
        try:
            import keyring
            k = keyring.get_password("polygon-api", "default")
            if k:
                return k
        except Exception:
            pass
        return os.environ.get("POLYGON_API_KEY")

POLYGON_BASE = "https://api.polygon.io"


def _fetch_polygon_daily(ticker, days, api_key):
    """Daily adjusted closes for one ticker via Polygon aggs. Returns a pd.Series or None."""
    end = datetime.now()
    start = end - timedelta(days=days)
    url = (f"{POLYGON_BASE}/v2/aggs/ticker/{ticker}/range/1/day/"
           f"{start.strftime('%Y-%m-%d')}/{end.strftime('%Y-%m-%d')}")
    try:
        r = requests.get(url, params={"adjusted": "true", "sort": "asc",
                                      "limit": 50000, "apiKey": api_key}, timeout=30)
        if r.status_code != 200:
            print(f"  Polygon HTTP {r.status_code} for {ticker}", file=sys.stderr)
            return None
        results = r.json().get("results") or []
        if not results:
            return None
        # Polygon stamps daily bars at midnight ET (04:00/05:00 UTC). Normalize to the
        # calendar date so .asof(run_date) matches the same trading day's bar.
        idx = pd.to_datetime([row["t"] for row in results], unit="ms").normalize()
        return pd.Series([row["c"] for row in results], index=idx, name=ticker)
    except requests.RequestException as e:
        print(f"  Polygon error for {ticker}: {e}", file=sys.stderr)
        return None


def _fetch_yahoo_daily(ticker, days):
    """Fallback: daily closes via yfinance."""
    try:
        import yfinance as yf
        end = datetime.now()
        start = end - timedelta(days=days)
        data = yf.download(ticker, start=start.strftime("%Y-%m-%d"),
                           end=end.strftime("%Y-%m-%d"), auto_adjust=True,
                           progress=False)
        if data is None or data.empty:
            return None
        col = data["Close"]
        if isinstance(col, pd.DataFrame):
            col = col.iloc[:, 0]
        return col.dropna()
    except Exception as e:
        print(f"  Yahoo error for {ticker}: {e}", file=sys.stderr)
        return None


def fetch_daily_closes(ticker, days=420, min_points=2):
    """Daily closes for a ticker; Polygon primary, Yahoo fallback.

    min_points: minimum Polygon rows required to accept the Polygon result before
    falling back to Yahoo. Use ~sma_window for the regime; the default (2) suits the
    short spans the scorecard needs.
    """
    key = get_polygon_api_key()
    if key:
        s = _fetch_polygon_daily(ticker, days, key)
        if s is not None and len(s) >= min_points:
            return s
    return _fetch_yahoo_daily(ticker, days)


def get_regime(benchmark="SPY", sma_window=200):
    """Compute the SPY-vs-200DMA regime.

    Returns dict: regime ('risk-on'|'risk-off'|'unknown'), spy_close, sma200,
    pct_vs_sma, asof, source.
    """
    closes = fetch_daily_closes(benchmark, days=int(sma_window * 1.6) + 60,
                                min_points=sma_window)
    if closes is None or len(closes) < sma_window:
        return {"regime": "unknown", "benchmark": benchmark,
                "reason": f"insufficient {benchmark} history",
                "spy_close": None, "sma200": None, "pct_vs_sma": None,
                "asof": None}
    closes = closes.sort_index()
    sma = float(closes.tail(sma_window).mean())
    last = float(closes.iloc[-1])
    regime = "risk-on" if last >= sma else "risk-off"
    return {
        "regime": regime,
        "benchmark": benchmark,
        "spy_close": round(last, 2),
        "sma200": round(sma, 2),
        "pct_vs_sma": round((last / sma - 1) * 100, 2),
        "asof": str(pd.Timestamp(closes.index[-1]).date()),
    }


if __name__ == "__main__":
    print(json.dumps(get_regime(), indent=2))
