"""
qm_polygon_news.py — Fetch news + current price for Strong Buy stocks via Polygon.io.

Replaces the Yahoo-based qm_market_news.py when Yahoo is rate-limited. Polygon's
News v2 endpoint returns structured articles with published_utc timestamps,
publishers, and headlines. Polygon Snapshot gives current price. Polygon does NOT
provide analyst price targets / consensus on Starter tier — those fields are
emitted as None and the Excel renders "N/A".

Outputs (compatible with qm_market_news_excel.py):
  - analyst_data.json: list of {ticker, company, current_price, target_mean, ...}
  - news_articles.json: list of {ticker, company, summary}
      where `summary` is a chronological dated bulletlist of headlines.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta

import pandas as pd
import requests


POLYGON_BASE = "https://api.polygon.io"


def get_polygon_api_key():
    try:
        import keyring
        key = keyring.get_password("polygon-api", "default")
        if key:
            return key
    except Exception:
        pass
    return os.environ.get("POLYGON_API_KEY")


def fetch_snapshot(session, key, ticker):
    """Return last/prev-day close from Polygon snapshot."""
    url = f"{POLYGON_BASE}/v2/snapshot/locale/us/markets/stocks/tickers/{ticker}"
    r = session.get(url, params={"apiKey": key}, timeout=20)
    if r.status_code != 200:
        return None
    snap = r.json().get("ticker", {})
    day = snap.get("day") or {}
    prev = snap.get("prevDay") or {}
    return day.get("c") or prev.get("c")


def fetch_news(session, key, ticker, months=6, limit=100):
    """Return list of news articles for a ticker over the last N months."""
    since = (datetime.utcnow() - timedelta(days=months * 31)).strftime("%Y-%m-%d")
    url = f"{POLYGON_BASE}/v2/reference/news"
    params = {
        "apiKey": key,
        "ticker": ticker,
        "published_utc.gte": since,
        "limit": limit,
        "order": "desc",
        "sort": "published_utc",
    }
    r = session.get(url, params=params, timeout=30)
    if r.status_code != 200:
        return []
    return r.json().get("results", []) or []


def summarize_articles(articles, max_items=25):
    """Build a chronological dated bullet list from Polygon News articles."""
    if not articles:
        return "(no Polygon News articles in the last 6 months)"

    # Polygon returns newest-first; reverse to chronological (oldest -> newest)
    items = sorted(articles, key=lambda a: a.get("published_utc", ""))[-max_items:]
    lines = []
    for art in items:
        date = (art.get("published_utc") or "")[:10]
        title = (art.get("title") or "").strip()
        publisher = ((art.get("publisher") or {}).get("name") or "").strip()
        # Encode title-only without source URL (URLs are reachable separately if needed)
        if publisher:
            lines.append(f"{date} — {title} ({publisher})")
        else:
            lines.append(f"{date} — {title}")
    return "\n".join(lines)


def run(screener_csv, signal_filter, output_dir, months=6):
    api_key = get_polygon_api_key()
    if not api_key:
        print("ERROR: No Polygon API key in keyring or POLYGON_API_KEY env var", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(screener_csv)
    filtered = df[df["Signal"] == signal_filter]
    tickers = filtered["Ticker"].tolist()
    names = dict(zip(filtered["Ticker"], filtered["Company"]))

    print(f"Fetching Polygon news + snapshot for {len(tickers)} '{signal_filter}' stocks "
          f"(last {months} months)...", file=sys.stderr)

    session = requests.Session()
    analyst_rows = []
    news_rows = []

    for i, ticker in enumerate(tickers):
        print(f"  [{i+1}/{len(tickers)}] {ticker} ...", file=sys.stderr)
        price = fetch_snapshot(session, api_key, ticker)
        articles = fetch_news(session, api_key, ticker, months=months, limit=100)

        analyst_rows.append({
            "ticker": ticker,
            "company": names.get(ticker, ""),
            "current_price": price,
            "target_mean": None,
            "target_high": None,
            "target_low": None,
            "upside_pct": None,
            "recommendation": "N/A",
            "n_analysts": 0,
            "status": "polygon",
        })

        news_rows.append({
            "ticker": ticker,
            "company": names.get(ticker, ""),
            "article_count": len(articles),
            "summary": summarize_articles(articles),
        })

        # Light pacing for politeness; Polygon Starter is effectively unlimited
        time.sleep(0.05)

    analyst_path = os.path.join(output_dir, "analyst_data.json")
    news_path = os.path.join(output_dir, "news_articles.json")
    with open(analyst_path, "w", encoding="utf-8") as f:
        json.dump(analyst_rows, f, indent=2, default=str)
    with open(news_path, "w", encoding="utf-8") as f:
        json.dump(news_rows, f, indent=2, default=str)

    n_with_news = sum(1 for r in news_rows if r["article_count"] > 0)
    n_with_price = sum(1 for r in analyst_rows if r["current_price"] is not None)
    print(f"Saved: {analyst_path}", file=sys.stderr)
    print(f"Saved: {news_path}", file=sys.stderr)
    print(f"Tickers with prices: {n_with_price}/{len(tickers)}", file=sys.stderr)
    print(f"Tickers with news: {n_with_news}/{len(tickers)}", file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--screener-csv", required=True)
    parser.add_argument("--signal", default="Strong Buy")
    parser.add_argument("--output-dir", default=".")
    parser.add_argument("--months", type=int, default=6)
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    run(args.screener_csv, args.signal, args.output_dir, args.months)
