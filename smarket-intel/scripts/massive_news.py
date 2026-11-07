#!/usr/bin/env python3
"""
Market Intel — News & Sentiment via Massive (formerly Polygon.io)

Replaces the `mcp__market_news_sentiment__*` servers, which are usually not
connected. Massive's /v2/reference/news carries an `insights` array per article:
each entry is {ticker, sentiment, sentiment_reasoning}, so this is a genuine
per-ticker scored aggregate rather than a qualitative read off web search.

Usage:
    python massive_news.py --tickers NVDA MSFT --output news.json
    python massive_news.py --market --output news.json      # market-wide feed
    python massive_news.py --tickers NVDA --days 14 --limit 50
    python massive_news.py --market --as-of 2026-03-14 --output news.json

--as-of / --date ends the news window at that date instead of today, so the
feed is what had actually been published by then. Coverage thins going back:
Massive's news archive is much shorter than its bar history, and the `insights`
sentiment array only appears on more recent articles — an as-of run a few years
back can legitimately return zero scored articles, which is reported as
unavailable rather than filled in.

Entitlement note: the news endpoint IS covered by the standard stocks plan.
Indices (I:VIX, I:SPX) are NOT — that is a separate add-on, so macro levels
must still come from elsewhere.

What this does NOT provide: retail or social sentiment of any kind. Massive
has no social feed and none is wired in. If the briefing wants retail
sentiment, say the module is unavailable rather than substituting web search.
"""

import argparse
import json
import os
from collections import Counter
from datetime import datetime, timedelta, timezone

import requests

BASE = os.environ.get("MASSIVE_API_BASE", "https://api.polygon.io")

# Sentiment -> numeric, for aggregation into a single score.
SENT_VAL = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}


def get_api_key() -> str:
    """Same key resolution as massive_ingest.py: keyring first, then env."""
    try:
        import keyring
        k = keyring.get_password("polygon-api", "default")
        if k:
            return k
    except Exception:
        pass
    k = os.environ.get("POLYGON_API_KEY")
    if not k:
        raise SystemExit("No API key: set keyring polygon-api/default or "
                         "POLYGON_API_KEY.")
    return k


def fetch_news(api_key: str, ticker: str = None, days: int = 30,
               limit: int = 50, as_of=None) -> list:
    """Pull articles, newest first, published within the window.

    The window ends at `as_of` (inclusive of that whole UTC day) when given,
    else at now. The right-hand bound is what makes a historical run honest:
    without it the API returns today's articles and the "sentiment" would be
    a read on the present dressed up as the past.
    """
    end = as_of or datetime.now(timezone.utc).date()
    since = (end - timedelta(days=days)).strftime("%Y-%m-%d")
    params = {"limit": min(limit, 1000), "order": "desc",
              "sort": "published_utc", "published_utc.gte": since,
              "apiKey": api_key}
    if as_of:
        params["published_utc.lte"] = f"{end.strftime('%Y-%m-%d')}T23:59:59Z"
    if ticker:
        params["ticker"] = ticker
    try:
        r = requests.get(f"{BASE}/v2/reference/news", params=params, timeout=45)
    except requests.RequestException as e:
        return [{"_error": f"request failed: {e}"}]
    if r.status_code == 403:
        return [{"_error": "403 NOT_AUTHORIZED — plan does not cover news"}]
    if r.status_code != 200:
        return [{"_error": f"HTTP {r.status_code}: {r.text[:200]}"}]
    return r.json().get("results", []) or []


def score_ticker(articles: list, ticker: str, as_of=None) -> dict:
    """Aggregate the per-ticker insights across articles into one reading.

    Only insights naming THIS ticker count. An article about the whole sector
    often carries insights for six names with different sentiment each; using
    the article-level tone instead would smear them together.
    """
    err = next((a["_error"] for a in articles if "_error" in a), None)
    if err:
        return {"ticker": ticker, "error": err, "available": False}

    counts, scored, headlines = Counter(), [], []
    for a in articles:
        mine = [i for i in (a.get("insights") or [])
                if (i.get("ticker") or "").upper() == ticker.upper()]
        sent = mine[0].get("sentiment") if mine else None
        if sent in SENT_VAL:
            counts[sent] += 1
            scored.append(SENT_VAL[sent])
        headlines.append({
            "published": (a.get("published_utc") or "")[:10],
            "title": a.get("title"),
            "publisher": (a.get("publisher") or {}).get("name"),
            "url": a.get("article_url"),
            "sentiment": sent,
            "reasoning": mine[0].get("sentiment_reasoning") if mine else None,
        })

    n = len(scored)
    if n == 0:
        return {"ticker": ticker, "available": True, "articles": len(articles),
                "scored_articles": 0,
                "note": "articles found but none carried insights for this ticker",
                "headlines": headlines[:10]}

    mean = sum(scored) / n
    # -1..+1 -> 0..10, matching the "Sentiment: Moderately Bullish (7/10)" form
    # the briefing template uses.
    score10 = round((mean + 1) * 5, 1)
    if mean >= 0.5:
        label = "Bullish"
    elif mean >= 0.15:
        label = "Moderately Bullish"
    elif mean > -0.15:
        label = "Neutral / Mixed"
    elif mean > -0.5:
        label = "Moderately Bearish"
    else:
        label = "Bearish"

    # Coverage is wildly uneven across tickers: mega-cap tech gets scored
    # articles daily, while XOM or SPY can go a week with none. A score built on
    # 1-2 articles is noise, and a score whose newest article is a week old is
    # not "current sentiment" — flag both so the briefing cannot overstate it.
    # Staleness is measured against the report date, not against now — on an
    # as-of run "the newest article is 4 days old" has to mean 4 days before
    # THAT date, or every historical run would look uniformly stale.
    ref = as_of or datetime.now(timezone.utc).date()
    dates = sorted(h["published"] for h in headlines if h["published"])
    stale_days = None
    if dates:
        try:
            stale_days = (ref - datetime.strptime(dates[-1], "%Y-%m-%d").date()).days
        except ValueError:
            pass

    if n < 5:
        confidence = "low"
    elif n < 15:
        confidence = "moderate"
    else:
        confidence = "good"
    if stale_days is not None and stale_days > 5:
        confidence = "low"

    return {
        "ticker": ticker,
        "available": True,
        "articles": len(articles),
        "scored_articles": n,
        "positive": counts["positive"],
        "neutral": counts["neutral"],
        "negative": counts["negative"],
        "mean_sentiment": round(mean, 3),
        "score_10": score10,
        "label": label,
        "confidence": confidence,
        "days_since_latest_article": stale_days,
        "coverage_note": (
            "thin coverage — treat the score as indicative only"
            if confidence == "low" else None),
        "headlines": headlines[:10],
    }


def market_feed(articles: list) -> dict:
    """Market mode: no ticker filter, so aggregate every insight in the feed.

    This is a tone-of-the-tape read across whatever names the wires are
    covering. It is NOT a breadth statistic — the article mix is whatever the
    publishers chose to write about, which skews to large caps and to whatever
    is already moving.
    """
    err = next((a["_error"] for a in articles if "_error" in a), None)
    if err:
        return {"available": False, "error": err}

    counts, per_ticker = Counter(), Counter()
    scored = []
    for a in articles:
        for i in (a.get("insights") or []):
            s = i.get("sentiment")
            if s in SENT_VAL:
                counts[s] += 1
                scored.append(SENT_VAL[s])
                per_ticker[(i.get("ticker") or "").upper()] += 1

    headlines = [{
        "published": (a.get("published_utc") or "")[:10],
        "title": a.get("title"),
        "publisher": (a.get("publisher") or {}).get("name"),
        "url": a.get("article_url"),
        "tickers": (a.get("tickers") or [])[:6],
    } for a in articles[:15]]

    n = len(scored)
    mean = (sum(scored) / n) if n else None
    return {
        "available": True,
        "articles": len(articles),
        "insights_scored": n,
        "positive": counts["positive"],
        "neutral": counts["neutral"],
        "negative": counts["negative"],
        "mean_sentiment": round(mean, 3) if mean is not None else None,
        "score_10": round((mean + 1) * 5, 1) if mean is not None else None,
        "most_covered": per_ticker.most_common(12),
        "basis": "publisher article mix — not a breadth or advance/decline measure",
        "headlines": headlines,
    }


def main():
    p = argparse.ArgumentParser(description="Massive news + sentiment for Market Intel")
    p.add_argument("--tickers", nargs="+", default=None,
                   help="Tickers to score. Omit with --market for the general feed.")
    p.add_argument("--market", action="store_true",
                   help="Also pull the unfiltered market-wide news feed")
    p.add_argument("--days", type=int, default=30, help="Lookback window (default 30)")
    p.add_argument("--limit", type=int, default=50,
                   help="Max articles per ticker (default 50)")
    p.add_argument("--output", required=True, help="Output JSON path")
    p.add_argument("--as-of", "--date", dest="as_of", default=None,
                   metavar="YYYY-MM-DD",
                   help="End the news window at this date instead of today")
    a = p.parse_args()

    as_of = None
    if a.as_of:
        try:
            as_of = datetime.strptime(a.as_of, "%Y-%m-%d").date()
        except ValueError:
            raise SystemExit(f"--as-of must be YYYY-MM-DD, got '{a.as_of}'")
        today = datetime.now(timezone.utc).date()
        if as_of > today:
            raise SystemExit(f"--as-of {as_of} is in the future (today is {today})")
        if as_of == today:
            as_of = None

    key = get_api_key()
    tickers = [t.upper() for t in a.tickers] if a.tickers else []
    want_market = a.market or not tickers

    out = {"generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
           "source": "Massive /v2/reference/news (insights = per-ticker LLM sentiment)",
           "window_days": a.days,
           "social_sentiment": "UNAVAILABLE — Massive carries no social feed",
           "tickers": {}}
    if as_of:
        out["as_of"] = str(as_of)
        out["historical"] = True
        out["window"] = (f"{as_of - timedelta(days=a.days)} .. {as_of} "
                         f"(nothing published after {as_of} was read)")

    for t in tickers:
        print(f"  news: {t}{f' as of {as_of}' if as_of else ''} ...", flush=True)
        out["tickers"][t] = score_ticker(
            fetch_news(key, t, a.days, a.limit, as_of), t, as_of)

    if want_market:
        print(f"  news: market-wide feed{f' as of {as_of}' if as_of else ''} ...",
              flush=True)
        out["market"] = market_feed(
            fetch_news(key, None, min(a.days, 7), a.limit, as_of))

    with open(a.output, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"News written to {a.output}")


if __name__ == "__main__":
    main()
