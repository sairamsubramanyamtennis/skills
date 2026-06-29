"""
qm_market_news.py — Fetch analyst/price data for Strong Buy stocks from the QM screener.

Phase 1 of the market-news pipeline:
  1. This script: current price from google.com/finance (primary); analyst targets/
     consensus from Yahoo (best-effort fallback — Google does not publish them).
  2. Claude: research 6 months of market news via web search (Phase 2, agent).
  3. Claude: add Market News Summary tab to Excel (Phase 3, agent).

Source note: Google Finance quote pages reliably expose the live price but NOT analyst
price targets or consensus ratings. So price comes from Google; target_mean/high/low and
consensus are attempted via Yahoo and left null if unavailable.

Usage:
    python qm_market_news.py --screener-csv qm_full_ranking.csv \
        --signal "Strong Buy" --output-dir <dir> [--source google|yahoo|auto]
"""

import argparse
import json
import re
import sys
import os
import time
import warnings

import pandas as pd
import requests

warnings.filterwarnings("ignore")

GF_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
         "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
# Most S&P 500 names list on NASDAQ or NYSE; try those first, then a few others.
GF_EXCHANGES = ["NASDAQ", "NYSE", "NYSEAMERICAN", "NYSEARCA", "OTCMKTS"]
# Google Finance (beta) leads with a related-stocks table whose rows also use
# jsname="Pdsbrc", so we must anchor on the MAIN quote container. The live price sits in
# <div class="N6SYTe"><span jsname="Pdsbrc"><span>$PRICE. We try that first, then a
# broader container-class fallback. If neither matches we return None (a wrong price is
# worse than a missing one). NOTE: Google's obfuscated class names rotate occasionally;
# if prices stop resolving, refresh these anchors from a fresh page fetch.
_PRICE_PATTERNS = [
    re.compile(r'N6SYTe"><span jsname="Pdsbrc"[^>]*>\s*<span>\s*\$?([0-9][0-9,]*\.?[0-9]*)'),
    re.compile(r'class="(?:zhtAvb|ujg0He|N6SYTe)"[^$]{0,200}?\$([0-9][0-9,]*\.[0-9]{2})'),
]


def _parse_gf_price(html):
    for pat in _PRICE_PATTERNS:
        m = pat.search(html)
        if m:
            try:
                v = float(m.group(1).replace(",", ""))
            except ValueError:
                continue
            if v > 0:
                return v
    return None


def _gf_url(ticker, exchange):
    # Screener stores tickers with '.' replaced by '-'; Google uses the dot form (BRK.B).
    gf_ticker = ticker.replace("-", ".")
    return f"https://www.google.com/finance/quote/{gf_ticker}:{exchange}"


def fetch_from_google(ticker, session=None):
    """Current price (and resolved exchange) from google.com/finance. None if not found."""
    sess = session or requests.Session()
    for ex in GF_EXCHANGES:
        try:
            r = sess.get(_gf_url(ticker, ex), headers={"User-Agent": GF_UA}, timeout=15)
        except requests.RequestException:
            continue
        if r.status_code != 200:
            continue
        price = _parse_gf_price(r.text)
        if price is not None:
            return {"current_price": price, "exchange": ex}
    return None


def fetch_targets_yahoo(ticker):
    """Best-effort analyst targets/consensus via Yahoo. Returns dict (fields None on failure)."""
    out = {"target_mean": None, "target_high": None, "target_low": None,
           "recommendation": "N/A", "n_analysts": 0, "yahoo_price": None, "ok": False}
    try:
        import yfinance as yf
        info = yf.Ticker(ticker).info
        out["target_mean"] = info.get("targetMeanPrice")
        out["target_high"] = info.get("targetHighPrice")
        out["target_low"] = info.get("targetLowPrice")
        out["recommendation"] = info.get("recommendationKey", "N/A")
        out["n_analysts"] = info.get("numberOfAnalystOpinions", 0) or 0
        out["yahoo_price"] = info.get("currentPrice") or info.get("regularMarketPrice")
        out["ok"] = any(out[k] is not None for k in ("target_mean", "target_high", "target_low")) \
            or out["yahoo_price"] is not None
    except Exception:
        pass
    return out


def fetch_analyst_data(ticker, source="auto", session=None):
    """
    Combine sources: Google for price (primary), Yahoo for targets/consensus (best-effort).

    source: 'google' (price only), 'yahoo' (legacy Yahoo-only), 'auto' (Google price +
    Yahoo targets fallback).
    """
    rec = {"ticker": ticker, "current_price": None, "target_mean": None,
           "target_high": None, "target_low": None, "upside_pct": None,
           "recommendation": "N/A", "n_analysts": 0, "price_source": None,
           "status": "error"}

    g = None
    if source in ("google", "auto"):
        g = fetch_from_google(ticker, session)
        if g:
            rec["current_price"] = g["current_price"]
            rec["price_source"] = f"google:{g['exchange']}"

    if source in ("yahoo", "auto"):
        y = fetch_targets_yahoo(ticker)
        rec["target_mean"] = y["target_mean"]
        rec["target_high"] = y["target_high"]
        rec["target_low"] = y["target_low"]
        rec["recommendation"] = y["recommendation"]
        rec["n_analysts"] = y["n_analysts"]
        # Fall back to Yahoo price only if Google didn't yield one.
        if rec["current_price"] is None and y["yahoo_price"]:
            rec["current_price"] = y["yahoo_price"]
            rec["price_source"] = "yahoo"

    if rec["current_price"] and rec["target_mean"]:
        rec["upside_pct"] = round((rec["target_mean"] / rec["current_price"] - 1) * 100, 1)

    if rec["current_price"] is not None:
        rec["status"] = "success" if rec["target_mean"] is not None else "price_only"
    return rec


def run(screener_csv, signal_filter="Strong Buy", output_dir=".", source="auto"):
    df = pd.read_csv(screener_csv)
    filtered = df[df["Signal"] == signal_filter]
    tickers = filtered["Ticker"].tolist()
    names = dict(zip(filtered["Ticker"], filtered["Company"]))
    print(f"Found {len(tickers)} stocks with signal '{signal_filter}' (source={source})",
          file=sys.stderr)

    session = requests.Session()
    analyst_data = []
    for i, ticker in enumerate(tickers):
        print(f"  [{i+1}/{len(tickers)}] {ticker}...", file=sys.stderr)
        data = fetch_analyst_data(ticker, source=source, session=session)
        data["company"] = names.get(ticker, "")
        analyst_data.append(data)
        if i < len(tickers) - 1:
            time.sleep(0.3)

    analyst_file = os.path.join(output_dir, "analyst_data.json")
    tickers_file = os.path.join(output_dir, "strong_buy_tickers.json")
    with open(analyst_file, "w", encoding="utf-8") as f:
        json.dump(analyst_data, f, indent=2, default=str)
    with open(tickers_file, "w", encoding="utf-8") as f:
        json.dump(tickers, f, indent=2)

    with_price = [d for d in analyst_data if d["current_price"] is not None]
    with_target = [d for d in analyst_data if d["target_mean"] is not None]
    print(f"\nPrices: {len(with_price)}/{len(tickers)} | "
          f"analyst targets: {len(with_target)}/{len(tickers)}", file=sys.stderr)
    if not with_target:
        print("Note: no analyst targets retrieved (Google has none; Yahoo unavailable). "
              "Price column is populated from Google.", file=sys.stderr)

    summary = {
        "signal_filter": signal_filter, "source": source, "n_stocks": len(tickers),
        "n_with_price": len(with_price), "n_with_target": len(with_target),
        "tickers": tickers, "analyst_data": analyst_data,
    }
    print(json.dumps(summary, indent=2, default=str))
    return analyst_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="QM Market News — price/analyst fetcher")
    parser.add_argument("--screener-csv", type=str, required=True)
    parser.add_argument("--signal", type=str, default="Strong Buy")
    parser.add_argument("--output-dir", type=str, default=".")
    parser.add_argument("--source", type=str, default="auto",
                        choices=["auto", "google", "yahoo"],
                        help="auto=Google price + Yahoo targets; google=price only; yahoo=legacy")
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    run(args.screener_csv, args.signal, args.output_dir, source=args.source)
