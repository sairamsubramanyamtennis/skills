"""
qm_market_news.py — Fetch analyst data for Strong Buy stocks from the QM screener.

This is Phase 1 of the market news pipeline:
  1. This script: Fetch current price, analyst targets, consensus from Yahoo Finance
  2. Claude: Research 6 months of market news using web search (Phase 2, done by agent)
  3. Claude: Add Market News Summary tab to Excel file (Phase 3, done by agent)

Usage:
    python qm_market_news.py \
        --screener-csv <path/to/qm_full_ranking.csv> \
        --signal "Strong Buy" \
        --output-dir <output_dir>
"""

import argparse
import json
import sys
import os
import time
import warnings
from datetime import datetime

import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")


def fetch_analyst_data(ticker):
    """
    Fetch analyst data from Yahoo Finance for a single ticker.

    Returns dict with:
      - current_price
      - target_mean, target_high, target_low
      - recommendation (e.g. "Buy")
      - n_analysts
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        current_price = info.get("currentPrice") or info.get("regularMarketPrice")
        target_mean = info.get("targetMeanPrice")
        target_high = info.get("targetHighPrice")
        target_low = info.get("targetLowPrice")
        recommendation = info.get("recommendationKey", "N/A")
        n_analysts = info.get("numberOfAnalystOpinions", 0)

        # Calculate upside
        upside = None
        if current_price and target_mean:
            upside = round((target_mean / current_price - 1) * 100, 1)

        return {
            "ticker": ticker,
            "current_price": current_price,
            "target_mean": target_mean,
            "target_high": target_high,
            "target_low": target_low,
            "upside_pct": upside,
            "recommendation": recommendation,
            "n_analysts": n_analysts,
            "status": "success",
        }

    except Exception as e:
        return {
            "ticker": ticker,
            "current_price": None,
            "target_mean": None,
            "target_high": None,
            "target_low": None,
            "upside_pct": None,
            "recommendation": "N/A",
            "n_analysts": 0,
            "status": f"error: {str(e)}",
        }


def run(screener_csv, signal_filter="Strong Buy", output_dir="."):
    """
    Fetch analyst data for all stocks matching the signal filter.
    """
    df = pd.read_csv(screener_csv)
    filtered = df[df["Signal"] == signal_filter]

    tickers = filtered["Ticker"].tolist()
    names = dict(zip(filtered["Ticker"], filtered["Company"]))

    print(f"Found {len(tickers)} stocks with signal '{signal_filter}'", file=sys.stderr)

    analyst_data = []
    for i, ticker in enumerate(tickers):
        print(f"  [{i+1}/{len(tickers)}] Fetching analyst data for {ticker}...", file=sys.stderr)
        data = fetch_analyst_data(ticker)
        data["company"] = names.get(ticker, "")
        analyst_data.append(data)

        # Rate limit — be gentle with Yahoo Finance
        if i < len(tickers) - 1:
            time.sleep(0.5)

    # Save outputs
    analyst_file = os.path.join(output_dir, "analyst_data.json")
    tickers_file = os.path.join(output_dir, "strong_buy_tickers.json")

    with open(analyst_file, "w") as f:
        json.dump(analyst_data, f, indent=2, default=str)

    with open(tickers_file, "w") as f:
        json.dump(tickers, f, indent=2)

    # Summary
    successful = [d for d in analyst_data if d["status"] == "success"]
    failed = [d for d in analyst_data if d["status"] != "success"]

    print(f"\nFetched analyst data: {len(successful)} success, {len(failed)} failed", file=sys.stderr)

    if successful:
        upsides = [d["upside_pct"] for d in successful if d["upside_pct"] is not None]
        if upsides:
            print(f"Avg analyst upside: {sum(upsides)/len(upsides):.1f}%", file=sys.stderr)
            print(f"Range: {min(upsides):.1f}% to {max(upsides):.1f}%", file=sys.stderr)

    # Print JSON to stdout for downstream consumption
    summary = {
        "signal_filter": signal_filter,
        "n_stocks": len(tickers),
        "n_successful": len(successful),
        "n_failed": len(failed),
        "tickers": tickers,
        "analyst_data": analyst_data,
    }
    print(json.dumps(summary, indent=2, default=str))

    return analyst_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="QM Market News — Analyst Data Fetcher")
    parser.add_argument("--screener-csv", type=str, required=True,
                        help="Path to qm_full_ranking.csv from the screener")
    parser.add_argument("--signal", type=str, default="Strong Buy",
                        help="Signal to filter (default: 'Strong Buy')")
    parser.add_argument("--output-dir", type=str, default=".",
                        help="Directory to save analyst_data.json and strong_buy_tickers.json")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    run(args.screener_csv, args.signal, args.output_dir)
