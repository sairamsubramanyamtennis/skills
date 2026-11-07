#!/usr/bin/env python3
"""
Market Intel — Technical Analysis & Data Gathering Script

Fetches price data, computes technical indicators, checks macro signals,
and performs sector/correlation analysis for a watchlist of stocks.

Usage:
    python market_analysis.py --output /tmp/market_intel_data.json          # market mode
    python market_analysis.py --tickers AAPL MSFT GOOG --output /tmp/out.json
    python market_analysis.py --tickers NVDA --source db --output out.json
    python market_analysis.py --as-of 2026-03-14 --output /tmp/out.json     # historical

With no --tickers, the script runs MARKET MODE: index ETFs, the full sector
heatmap, risk-appetite ratios, safe havens, and macro — no watchlist required.

--as-of / --date runs the whole report as it would have read at the close of
that day. Every series is truncated at the date, ticker->company identity is
resolved AT that date (not today), and the moving averages, RSI, relative
performance and correlations are all computed from bars ending there. Nothing
after the date is read, so the output carries no look-ahead. Two things simply
cannot be reconstructed and are reported as unavailable rather than faked:
the live intraday quote overlay, and yfinance's earnings calendar (which is
forward-looking only — it knows the NEXT earnings date, not the one that was
next back then).

Data sources:
    pg     — Postgres `trading` mkt.price_daily (fast, offline, full OHLC since 2026-08-06).
             Bars come from massive_ingest.py's grouped-daily pull; if they are
             stale, run `python massive_ingest.py pull`.
    yf     — yfinance (live, full OHLC, but network-dependent)
    auto   — Postgres for history + yfinance for the live quote/earnings/macro
             (default). `db` is an accepted alias for `pg`.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import yfinance as yf


# Bar history backend. Postgres `trading` is the only bar store: mkt.price_daily,
# 49M+ rows, ~36k tickers, OHLC + vwap + volume, 2003 -> present (T-1, or T-0 after
# the close). The local file cache this replaced was retired in the Aug-2026 cutover.
PG_BACKEND = "pg"
PG_DSN = dict(host="localhost", port=5433, user="postgres", dbname="trading")
DEFAULT_DB = PG_BACKEND

# How stale the DB may be before we refuse to trust it (calendar days).
DB_MAX_STALENESS_DAYS = 7

# A real grouped-daily pull lands ~12,400 tickers. Anything far below that is a
# partial write from another job and will be missing every ETF.
PG_MIN_DAY_BREADTH = 5000

# The DB is Polygon-sourced: equities/ETFs only, no index symbols. These ETF
# proxies stand in for the macro indices when yfinance is unavailable. They are
# directionally useful only — a proxy never gives you the actual index level.
MACRO_PROXIES = {
    "treasury_10y": ("IEF", "7-10Y Treasury ETF (inverse to yields)"),
    "vix": ("VIXY", "Short-term VIX futures ETF (decay-distorted)"),
    "dxy": ("UUP", "Dollar Index bullish ETF"),
}

# Sector lookup fallback for when yfinance metadata is unreachable.
SECTOR_FALLBACK = {
    "NVDA": "Technology", "AAPL": "Technology", "MSFT": "Technology",
    "AVGO": "Technology", "AMD": "Technology", "INTC": "Technology",
    "MU": "Technology", "CRM": "Technology", "ORCL": "Technology",
    "GOOGL": "Communication Services", "GOOG": "Communication Services",
    "META": "Communication Services", "NFLX": "Communication Services",
    "AMZN": "Consumer Cyclical", "TSLA": "Consumer Cyclical",
    "JPM": "Financial Services", "BRK.B": "Financial Services",
    "XOM": "Energy", "CVX": "Energy",
    "UNH": "Healthcare", "LLY": "Healthcare", "JNJ": "Healthcare",
}


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

# --- Market mode -----------------------------------------------------------
# Used when no watchlist is supplied. ETFs, not index symbols, so the local
# Polygon-sourced cache can serve them too.

INDEX_ETFS = [
    ("SPY", "S&P 500"),
    ("QQQ", "Nasdaq 100"),
    ("DIA", "Dow 30"),
    ("IWM", "Russell 2000"),
    ("RSP", "S&P 500 Equal Weight"),
]

# Ratio pairs that read risk appetite. A rising ratio = the numerator is
# winning, which for each pair below means risk-on.
RISK_RATIOS = [
    ("XLY", "XLP", "Cyclicals vs Defensives"),
    ("IWM", "SPY", "Small caps vs Large caps"),
    ("RSP", "SPY", "Equal weight vs Cap weight (breadth)"),
    ("HYG", "IEF", "High-yield credit vs Treasuries"),
    ("SMH", "SPY", "Semiconductors vs Market"),
]

SAFE_HAVENS = [
    ("TLT", "20Y+ Treasuries"),
    ("GLD", "Gold"),
    ("UUP", "US Dollar"),
]


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


# ---------------------------------------------------------------------------
# Postgres bar store (the live backend)
# ---------------------------------------------------------------------------

def _pg_connect():
    import psycopg2
    return psycopg2.connect(**PG_DSN)


def _pg_resolve(cur, symbols, on_date) -> dict:
    """Map ticker -> security_id as of one date. Returns {ticker: security_id}.

    173 tickers denote more than one company across time (ABX = Barrick, then
    Abacus). Resolving at a date and then querying by security_id keeps the
    series single-identity; joining on the ticker string would splice two
    companies together and manufacture a price discontinuity.
    """
    out = {}
    for sym in symbols:
        cur.execute("SELECT ref.resolve(%s, %s)", (sym, on_date))
        row = cur.fetchone()
        if row and row[0] is not None:
            out[sym] = row[0]
    return out


def pg_check(as_of=None) -> dict:
    """Verify Postgres is reachable and its bars cover the requested date.

    With `as_of` set the reference point moves from today to that date: the
    relevant bar is the last one ON OR BEFORE it, and "stale" means the store
    has no bar within DB_MAX_STALENESS_DAYS *before* the date — which is how a
    date outside the store's coverage (too early, or past the last pull) shows
    up. Bars after the date are never consulted.
    """
    ref = as_of or datetime.now().date()
    status = {"path": f"postgres://{PG_DSN['host']}:{PG_DSN['port']}/"
                      f"{PG_DSN['dbname']} mkt.price_daily", "usable": False}
    if as_of:
        status["as_of_requested"] = str(as_of)
    try:
        with _pg_connect() as pg:
            cur = pg.cursor()
            cur.execute("SELECT max(obs_date) FROM mkt.price_daily "
                        "WHERE obs_date <= %s", (ref,))
            max_date = cur.fetchone()[0]
            if max_date is not None:
                # Breadth guard: a day carrying only a few hundred tickers is a
                # partial write from some other job, not a grouped-daily pull,
                # and it will be missing every ETF the market module needs.
                cur.execute("SELECT count(*) FROM mkt.price_daily WHERE obs_date = %s",
                            (max_date,))
                breadth = cur.fetchone()[0]
    except Exception as e:
        status["error"] = f"Postgres unreachable: {e}"
        return status

    if max_date is None:
        status["error"] = (f"mkt.price_daily has no bars on or before {ref} — "
                           f"the date is before the store's coverage begins "
                           f"(bars start in 2003)")
        return status

    status["last_bar_date"] = str(max_date)
    status["last_bar_breadth"] = breadth
    age = (ref - max_date).days
    status["staleness_days"] = age
    if age > DB_MAX_STALENESS_DAYS:
        if as_of:
            status["error"] = (f"no bar within {DB_MAX_STALENESS_DAYS} days before "
                              f"{ref}: nearest is {max_date} ({age} days earlier). "
                              f"That date is outside the store's coverage — if it is "
                              f"recent, run: python massive_ingest.py pull")
        else:
            status["error"] = (f"Postgres bars are stale: last bar {max_date} is "
                              f"{age} days old (limit {DB_MAX_STALENESS_DAYS}). "
                              f"Run: python massive_ingest.py pull")
        return status
    if breadth < PG_MIN_DAY_BREADTH:
        status["error"] = (f"bar {max_date} has only {breadth:,} tickers "
                          f"(expected >{PG_MIN_DAY_BREADTH:,}) — that is a partial "
                          f"write, ETFs will be missing. Run: "
                          f"python massive_ingest.py pull")
        return status
    status["usable"] = True
    return status


def load_prices_from_pg(symbols, lookback_days: int = 500, as_of=None) -> dict:
    """Load bars from mkt.price_daily. Returns {symbol: DataFrame}.

    Same frame shape as the yfinance loader (DatetimeIndex, Close/Volume, plus
    Open/High/Low where the store has them).

    OHLC was added to mkt.price_daily on 2026-08-06 and backfilled to 2003; a
    window is only given Open/High/Low if EVERY bar in it carries them. A
    partially-filled High column is worse than none at all — a rolling max would
    skip the NaN rows silently and return a true range computed off whichever
    days happened to be populated. All-or-nothing keeps the failure loud.

    `as_of` caps the window on the right AND moves the identity resolution to
    that date. Both halves matter: resolving at today would hand back the
    security_id of whoever holds the ticker NOW, which for a reused ticker is a
    different company than the one trading under it on the historical date.
    """
    if not symbols:
        return {}
    ref = as_of or datetime.now().date()
    start = ref - timedelta(days=lookback_days)
    out = {}
    with _pg_connect() as pg:
        cur = pg.cursor()
        cur.execute("SELECT max(obs_date) FROM mkt.price_daily WHERE obs_date <= %s",
                    (ref,))
        resolve_date = cur.fetchone()[0]
        if resolve_date is None:
            return {}
        ids = _pg_resolve(cur, symbols, resolve_date)
        if not ids:
            return {}
        by_id = {v: k for k, v in ids.items()}
        cur.execute(
            "SELECT security_id, obs_date, close, volume, open, high, low "
            "FROM mkt.price_daily "
            "WHERE security_id = ANY(%s) AND obs_date >= %s AND obs_date <= %s "
            "ORDER BY obs_date",
            (list(ids.values()), start, ref),
        )
        rows = cur.fetchall()

    df = pd.DataFrame(rows, columns=["security_id", "date", "close", "volume",
                                     "open", "high", "low"])
    for sid, sym in by_id.items():
        sub = df[df["security_id"] == sid]
        if sub.empty:
            continue
        sub = sub.set_index(pd.to_datetime(sub["date"])).sort_index()
        frame = {"Close": sub["close"].astype(float),
                 "Volume": sub["volume"].astype(float)}
        if not sub[["open", "high", "low"]].isna().any().any():
            frame["Open"] = sub["open"].astype(float)
            frame["High"] = sub["high"].astype(float)
            frame["Low"] = sub["low"].astype(float)
        out[sym] = pd.DataFrame(frame)
    return out


def pg_constituent_breadth(as_of=None, index_code: str = "SP500") -> dict:
    """True breadth across the ~500 index members, straight from Postgres.

    The sector-ETF breadth this supplements answers "how many of 11 SPDRs rose",
    which on a day like 2026-08-04 reported 7-of-11 advancing while one sector
    supplied the entire index move. Counting constituents instead gives the
    advance/decline line, the share above each moving average, and the 52-week
    high/low tally — the numbers that actually distinguish a broad rally from a
    narrow one.

    Membership is point-in-time (ref.index_membership intersected with the
    date), so a historical run counts the names that were in the index THEN,
    never today's list. Everything derives from bars already in the store, so
    this costs one query and no network.

    Returns {} when Postgres is unreachable or the date has no bars — the
    caller omits the section rather than substituting the coarser measure.
    """
    ref = as_of or datetime.now().date()
    try:
        with _pg_connect() as pg:
            cur = pg.cursor()
            cur.execute("SELECT max(obs_date) FROM mkt.price_daily WHERE obs_date <= %s",
                        (ref,))
            bar_date = cur.fetchone()[0]
            if bar_date is None:
                return {}
            cur.execute(
                """
                WITH mem AS (
                    SELECT security_id FROM ref.index_membership
                     WHERE index_code = %(idx)s AND %(d)s::date <@ valid
                ), px AS (
                    SELECT p.security_id, p.close,
                           row_number() OVER (PARTITION BY p.security_id
                                              ORDER BY p.obs_date DESC) AS rn
                      FROM mkt.price_daily p JOIN mem USING (security_id)
                     WHERE p.obs_date <= %(d)s
                       AND p.obs_date > %(d)s::date - 420
                )
                SELECT security_id,
                       max(close) FILTER (WHERE rn = 1)    AS c0,
                       max(close) FILTER (WHERE rn = 2)    AS c1,
                       avg(close) FILTER (WHERE rn <= 50)  AS ma50,
                       avg(close) FILTER (WHERE rn <= 200) AS ma200,
                       max(close) FILTER (WHERE rn <= 252) AS hi52,
                       min(close) FILTER (WHERE rn <= 252) AS lo52,
                       count(*)                            AS n
                  FROM px GROUP BY security_id
                """,
                {"idx": index_code, "d": bar_date},
            )
            rows = cur.fetchall()
    except Exception:
        return {}

    if not rows:
        return {}

    adv = dec = unch = 0
    rets, a50, n50, a200, n200, hi, lo = [], 0, 0, 0, 0, 0, 0
    for _sid, c0, c1, ma50, ma200, hi52, lo52, n in rows:
        if c0 is None:
            continue
        if c1:
            r = 100.0 * (c0 / c1 - 1.0)
            rets.append(r)
            adv += r > 0
            dec += r < 0
            unch += r == 0
        # A name with fewer bars than the window has no honest average yet;
        # counting it as "below" would bias the reading down every January
        # after a wave of index additions.
        if ma50 is not None and n >= 50:
            n50 += 1
            a50 += c0 > ma50
        if ma200 is not None and n >= 200:
            n200 += 1
            a200 += c0 > ma200
        if hi52 is not None and n >= 200:
            hi += c0 >= hi52
            lo += c0 <= lo52

    if not rets:
        return {}
    rets.sort()
    mid = len(rets) // 2
    median = rets[mid] if len(rets) % 2 else (rets[mid - 1] + rets[mid]) / 2

    return {
        "basis": (f"{len(rows)} point-in-time {index_code} constituents from "
                  f"Postgres mkt.price_daily on {bar_date}"),
        "as_of": str(bar_date),
        "members": len(rows),
        "advancing": adv,
        "declining": dec,
        "unchanged": unch,
        "advance_decline_ratio": round(adv / dec, 2) if dec else None,
        "pct_advancing": round(100.0 * adv / (adv + dec + unch), 1) if rets else None,
        "pct_above_50dma": round(100.0 * a50 / n50, 1) if n50 else None,
        "pct_above_200dma": round(100.0 * a200 / n200, 1) if n200 else None,
        "n_above_50dma_measured": n50,
        "n_above_200dma_measured": n200,
        "new_52w_highs": hi,
        "new_52w_lows": lo,
        "median_member_return": round(median, 2),
        "mean_member_return": round(sum(rets) / len(rets), 2),
    }


def get_ex_dividend_from_pg(symbol: str, as_of=None) -> str:
    """Most recent / next ex-dividend date from mkt.dividend.

    In a historical run the ex-date is capped at `as_of` — mkt.dividend has no
    declaration dates, so an ex-date sitting after the report date is not
    something that was knowable then. Capping trades a slightly less useful
    answer for one with no look-ahead.
    """
    ref = as_of or datetime.now().date()
    try:
        with _pg_connect() as pg:
            cur = pg.cursor()
            cur.execute("SELECT max(obs_date) FROM mkt.price_daily "
                        "WHERE obs_date <= %s", (ref,))
            resolve_date = cur.fetchone()[0]
            cur.execute("SELECT ref.resolve(%s, %s)", (symbol, resolve_date))
            row = cur.fetchone()
            if not row or row[0] is None:
                return None
            if as_of:
                cur.execute("SELECT ex_date FROM mkt.dividend WHERE security_id = %s "
                            "AND ex_date <= %s ORDER BY ex_date DESC LIMIT 1",
                            (row[0], ref))
            else:
                cur.execute("SELECT ex_date FROM mkt.dividend WHERE security_id = %s "
                            "ORDER BY ex_date DESC LIMIT 1", (row[0],))
            r = cur.fetchone()
            return str(r[0]) if r else None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Bar loading from Postgres
# ---------------------------------------------------------------------------

def db_check(db_path: str, as_of=None) -> dict:
    """Verify the bar cache exists and covers the requested date.

    Returns a status dict. A cache that does not reach the reference date is
    reported rather than silently used — computing a 50-day MA on month-old
    bars looks identical to a correct answer.
    """
    return pg_check(as_of)


def load_prices_from_db(symbols, db_path: str, lookback_days: int = 500,
                        as_of=None) -> dict:
    """Load close+volume bars for symbols. Returns {symbol: DataFrame}.

    The frame mimics the yfinance shape (DatetimeIndex, Close/Volume columns)
    so downstream analysis is source-agnostic. There is no OHLC in the cache,
    so High/Low/Open are absent by design — anything needing them must not
    silently fall back to Close.
    """
    return load_prices_from_pg(symbols, lookback_days, as_of)


def get_ex_dividend_from_db(symbol: str, db_path: str, as_of=None) -> str:
    """Most recent / next ex-dividend date from the cache's dividends table."""
    return get_ex_dividend_from_pg(symbol, as_of)


def get_live_quote(symbol: str) -> dict:
    """One lightweight yfinance call for today's price, to overlay on T-1 bars."""
    try:
        data = yf.Ticker(symbol).history(period="2d", auto_adjust=True)
        if data.empty:
            return {}
        return {
            "live_price": round(float(data["Close"].iloc[-1]), 2),
            "live_volume": int(data["Volume"].iloc[-1]),
            "live_date": str(data.index[-1].date()),
        }
    except Exception:
        return {}


def get_macro_from_db(db_path: str, as_of=None) -> dict:
    """Proxy macro read from ETF bars when the real indices are unreachable.

    Explicitly labelled as proxies: these give direction, never the index level.
    """
    macro = {}
    symbols = [s for s, _ in MACRO_PROXIES.values()]
    data = load_prices_from_db(symbols, db_path, lookback_days=60, as_of=as_of)
    for name, (sym, desc) in MACRO_PROXIES.items():
        if sym not in data or len(data[sym]) < 6:
            continue
        close = data[sym]["Close"]
        chg = float((close.iloc[-1] / close.iloc[-5] - 1) * 100)
        macro[name] = {
            "proxy_symbol": sym,
            "proxy_note": desc,
            "proxy_level": round(float(close.iloc[-1]), 2),
            "change_1w": round(chg, 2),
            "value": None,  # real index level unavailable from this source
        }
    return macro


def load_closes_yf(symbols, start, end) -> dict:
    """Load close+volume frames from yfinance in the same shape as the cache."""
    out = {}
    if not symbols:
        return out
    raw = yf.download(list(symbols), start=start, end=end, progress=False,
                      group_by="ticker", auto_adjust=True)
    if raw is None or raw.empty:
        return out
    for sym in symbols:
        try:
            # yfinance returns a MultiIndex even for a single symbol, and the
            # ticker can sit on either level depending on group_by. Probe both
            # rather than assuming — guessing here silently yields empty frames.
            if isinstance(raw.columns, pd.MultiIndex):
                lvl0 = raw.columns.get_level_values(0)
                lvl1 = raw.columns.get_level_values(1)
                if sym in lvl0:
                    sub = raw[sym]
                elif sym in lvl1:
                    sub = raw.xs(sym, axis=1, level=1)
                else:
                    continue
            else:
                sub = raw
            if sub is None or sub.empty:
                continue
            close, vol = sub["Close"], sub["Volume"]
            if hasattr(close, "columns"):
                close = close.iloc[:, 0]
            if hasattr(vol, "columns"):
                vol = vol.iloc[:, 0]
            df = pd.DataFrame({"Close": close.astype(float),
                               "Volume": vol.astype(float)}).dropna()
            if not df.empty:
                out[sym] = df
        except Exception:
            continue
    return out


def _pct_change_n(series: pd.Series, n: int):
    """Percent change over the last n bars, or None if there isn't the history."""
    if len(series) <= n:
        return None
    return round(float(series.iloc[-1] / series.iloc[-1 - n] - 1) * 100, 2)


def _pct_change_ytd(series: pd.Series):
    year_start = f"{series.index[-1].year}-01-01"
    ytd = series[series.index >= year_start]
    if len(ytd) < 2:
        return None
    return round(float(series.iloc[-1] / ytd.iloc[0] - 1) * 100, 2)


def summarize_symbol(symbol: str, df: pd.DataFrame, label: str = None) -> dict:
    """Compact multi-horizon read on one ETF/index — the market-mode building block."""
    close, volume = df["Close"], df["Volume"]
    ma50 = float(close.tail(50).mean()) if len(close) >= 50 else None
    ma200 = float(close.tail(200).mean()) if len(close) >= 200 else None
    out = {
        "symbol": symbol,
        "label": label or symbol,
        "price": round(float(close.iloc[-1]), 2),
        "change_pct": _pct_change_n(close, 1),
        "chg_1w": _pct_change_n(close, 5),
        "chg_1m": _pct_change_n(close, 21),
        "chg_3m": _pct_change_n(close, 63),
        "chg_ytd": _pct_change_ytd(close),
        "rsi_14": compute_rsi(close),
        "ma_50": round(ma50, 2) if ma50 else None,
        "ma_200": round(ma200, 2) if ma200 else None,
        "above_ma50": bool(close.iloc[-1] > ma50) if ma50 else None,
        "above_ma200": bool(close.iloc[-1] > ma200) if ma200 else None,
        "as_of": str(close.index[-1].date()),
    }
    if len(volume) >= 30:
        avg = float(volume.tail(30).mean())
        out["volume"] = int(volume.iloc[-1])
        out["vol_vs_avg"] = round(float(volume.iloc[-1] / avg), 2) if avg else None
    return out


def run_market_mode(data: dict, as_of=None) -> dict:
    """Whole-market picture: indices, sector heatmap, risk ratios, safe havens, breadth.

    `data` is a {symbol: DataFrame} map already loaded from whichever source.
    Anything missing is simply omitted — never substituted with a related symbol.
    """
    market = {}
    spy = data.get("SPY", {}).get("Close") if "SPY" in data else None

    market["indices"] = [
        summarize_symbol(sym, data[sym], label)
        for sym, label in INDEX_ETFS if sym in data
    ]

    # Sector heatmap, each sector measured against SPY over the same windows.
    sectors = []
    for sector_name, etf in SECTOR_ETFS.items():
        if etf not in data:
            continue
        s = summarize_symbol(etf, data[etf], sector_name)
        if spy is not None:
            for horizon, n in (("1d", 1), ("1w", 5), ("1m", 21)):
                spy_chg = _pct_change_n(spy, n)
                key = "change_pct" if horizon == "1d" else f"chg_{horizon}"
                if s.get(key) is not None and spy_chg is not None:
                    s[f"vs_spy_{horizon}"] = round(s[key] - spy_chg, 2)
        sectors.append(s)
    sectors.sort(key=lambda x: (x.get("change_pct") is None, -(x.get("change_pct") or 0)))
    market["sectors"] = sectors

    # Real breadth: the advance/decline line across the ~500 point-in-time index
    # members. Postgres already holds every constituent bar, so the only reason
    # this was ever measured on 11 sector ETFs was that nobody asked it to.
    cb = pg_constituent_breadth(as_of=as_of)
    if cb:
        market["constituent_breadth"] = cb

    # The sector-ETF reading is kept alongside rather than replaced: it is the
    # sector-participation view (how many sectors, not how many names), and on a
    # narrow day the gap between the two is itself the story.
    if sectors:
        adv = sum(1 for s in sectors if (s.get("change_pct") or 0) > 0)
        above50 = [s for s in sectors if s.get("above_ma50") is not None]
        above200 = [s for s in sectors if s.get("above_ma200") is not None]
        # On a historical run some sector ETFs did not exist yet (XLRE launched
        # 2015, XLC 2018), so the denominator is whatever actually loaded. Say
        # which — a "% above the 200-day" computed over 9 sectors reported as
        # if it were 11 is a quietly wrong number.
        market["breadth"] = {
            "basis": (f"{len(sectors)} of {len(SECTOR_ETFS)} SPDR sector ETFs "
                      f"(not individual constituents)"),
            "sectors_measured": len(sectors),
            "sectors_advancing": adv,
            "sectors_declining": len(sectors) - adv,
            "pct_sectors_above_50dma": (
                round(100 * sum(1 for s in above50 if s["above_ma50"]) / len(above50))
                if above50 else None),
            "pct_sectors_above_200dma": (
                round(100 * sum(1 for s in above200 if s["above_ma200"]) / len(above200))
                if above200 else None),
        }

    # Risk-appetite ratios. Rising = risk-on for every pair defined above.
    ratios = []
    for num, den, desc in RISK_RATIOS:
        if num not in data or den not in data:
            continue
        pair = pd.concat([data[num]["Close"], data[den]["Close"]],
                         axis=1, join="inner").dropna()
        if len(pair) < 22:
            continue
        ratio = pair.iloc[:, 0] / pair.iloc[:, 1]
        ratios.append({
            "pair": f"{num}/{den}",
            "description": desc,
            "chg_1w": _pct_change_n(ratio, 5),
            "chg_1m": _pct_change_n(ratio, 21),
            "chg_3m": _pct_change_n(ratio, 63),
            "direction_1m": "risk-on" if (_pct_change_n(ratio, 21) or 0) > 0 else "risk-off",
        })
    market["risk_ratios"] = ratios

    market["safe_havens"] = [
        summarize_symbol(sym, data[sym], label)
        for sym, label in SAFE_HAVENS if sym in data
    ]

    missing = sorted(set(market_mode_symbols()) - set(data))
    if missing:
        market["unavailable_symbols"] = missing
        # A historical run far enough back predates several of these funds
        # (RSP 2003, XLRE 2015, XLC 2018, SMH 2000). Losing one or two is
        # routine; losing a third of them means the picture is genuinely
        # partial and the briefing has to say so rather than read the
        # remainder as if it were the whole market.
        if len(missing) > len(market_mode_symbols()) / 3:
            market["coverage_warning"] = (
                f"{len(missing)} of {len(market_mode_symbols())} market symbols "
                f"unavailable — either they had not launched yet at this date or "
                f"the source could not serve them. Treat every aggregate below "
                f"as partial.")
    return market


def market_mode_symbols() -> list:
    """Every symbol market mode needs, deduplicated."""
    syms = {s for s, _ in INDEX_ETFS}
    syms |= set(SECTOR_ETFS.values())
    syms |= {s for pair in RISK_RATIOS for s in pair[:2]}
    syms |= {s for s, _ in SAFE_HAVENS}
    return sorted(syms)


def analyze_ticker(symbol: str, hist: pd.DataFrame, spy_returns: pd.Series, sector_etf_data: dict,
                   source: str = "yf", db_path: str = None, live: bool = True,
                   as_of=None) -> dict:
    """Run full analysis for a single ticker."""
    result = {"symbol": symbol, "source": source}

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

    # Sector comparison — prefer the static map in db mode to avoid a network call
    ticker_obj = None
    if source == "db" and symbol in SECTOR_FALLBACK:
        sector = SECTOR_FALLBACK[symbol]
    else:
        try:
            ticker_obj = yf.Ticker(symbol)
            sector = get_sector_for_ticker(ticker_obj)
        except Exception:
            sector = "Unknown"
        if sector == "Unknown":
            sector = SECTOR_FALLBACK.get(symbol, "Unknown")
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

    # Ex-dividend from the local cache when available (no network needed)
    if db_path:
        db_ex_div = get_ex_dividend_from_db(symbol, db_path, as_of)
        if db_ex_div:
            result["ex_dividend_date"] = db_ex_div

    # Earnings calendar has no local equivalent — yfinance only, and it reports
    # the NEXT earnings date as of now. There is no way to ask it what was
    # upcoming on a past date, so a historical run reports it missing rather
    # than attaching a date from the wrong era.
    if as_of:
        result["next_earnings"] = None
        result["earnings_calendar_note"] = (
            "unavailable for historical runs — yfinance's calendar is "
            "forward-looking from today only")
    elif live:
        try:
            if ticker_obj is None:
                ticker_obj = yf.Ticker(symbol)
            cal = ticker_obj.calendar
            if cal is not None and not (isinstance(cal, pd.DataFrame) and cal.empty):
                if isinstance(cal, dict):
                    if cal.get("Earnings Date"):
                        result["next_earnings"] = str(cal["Earnings Date"][0])
                    if cal.get("Ex-Dividend Date") and "ex_dividend_date" not in result:
                        result["ex_dividend_date"] = str(cal["Ex-Dividend Date"])
                elif isinstance(cal, pd.DataFrame):
                    if "Earnings Date" in cal.index:
                        result["next_earnings"] = str(cal.loc["Earnings Date"].iloc[0])
                    if "Ex-Dividend Date" in cal.index and "ex_dividend_date" not in result:
                        result["ex_dividend_date"] = str(cal.loc["Ex-Dividend Date"].iloc[0])
        except Exception:
            result.setdefault("next_earnings", None)

    # Overlay today's quote — the cache is T-1, so without this the "price" is
    # yesterday's close. Flagged so the briefing can say which day it is.
    result["as_of"] = str(hist.index[-1].date())
    if source == "db" and live and as_of is None:
        quote = get_live_quote(symbol)
        if quote and quote.get("live_date") != result["as_of"]:
            result["price"] = quote["live_price"]
            result["volume"] = quote["live_volume"]
            result["as_of"] = quote["live_date"]
            live_ret = quote["live_price"] / float(close.iloc[-1]) - 1
            result["change_pct"] = round(live_ret * 100, 2)
            result["prev_close"] = round(float(close.iloc[-1]), 2)
            result["live_overlay"] = True
            # Re-score the volatility alert against today's move, not yesterday's.
            live_returns = pd.concat([returns, pd.Series([live_ret])], ignore_index=True)
            result["volatility_alert"] = compute_volatility_alert(live_returns)

    return result


def get_macro_snapshot(as_of=None) -> dict:
    """Fetch macro indicators: 10Y yield, VIX, DXY.

    With `as_of` the window ends the day AFTER the date (yfinance treats `end`
    as exclusive), so the last row is that day's close and nothing later is
    pulled in. Note the difference from a live run: without `as_of` this is an
    intraday quote mid-session, with it it is always a settled close.
    """
    macro = {}
    end = (as_of + timedelta(days=1)) if as_of else datetime.now()
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
                    "as_of": str(close.index[-1].date()),
                }
        except Exception as e:
            macro[name] = {"error": str(e)}

    # VIX interpretation
    if "vix" in macro and "value" in macro["vix"]:
        v = macro["vix"]["value"]
        macro["vix"]["level"] = "Low" if v < 15 else ("Moderate" if v < 20 else ("Elevated" if v < 30 else "High"))

    return macro


def run_db_mode(tickers, db_path, live, results, as_of=None):
    """History from the local cache; only the quote/earnings/macro touch the network."""
    # 500 calendar days ~ 345 trading days, enough headroom for a 200-day MA.
    needed = set(tickers) | {"SPY"}
    sectors = {t: SECTOR_FALLBACK.get(t, "Unknown") for t in tickers}
    for t in tickers:
        etf = SECTOR_ETFS.get(sectors[t])
        if etf:
            needed.add(etf)

    data = load_prices_from_db(sorted(needed), db_path, lookback_days=500, as_of=as_of)

    missing = [t for t in tickers if t not in data]
    if missing:
        print(f"  not in cache: {', '.join(missing)}")

    if "SPY" not in data:
        print("  WARNING: SPY missing from cache — correlations unavailable")
        spy_returns = pd.Series(dtype=float)
    else:
        spy_returns = data["SPY"]["Close"].pct_change().dropna()

    sector_etf_data = {
        etf: data[etf]["Close"] for etf in data if etf in SECTOR_ETFS.values()
    }

    for t in tickers:
        print(f"Analyzing {t} (db)...")
        if t not in data:
            results["tickers"][t] = {"error": f"{t} not found in local cache"}
            continue
        results["tickers"][t] = analyze_ticker(
            t, data[t], spy_returns, sector_etf_data,
            source="db", db_path=db_path, live=live, as_of=as_of,
        )
    return results


def parse_as_of(raw: str):
    """Validate --as-of and normalise it. Returns a date, or None for 'live'.

    A date of today (or later today, before the close) is not an error — it is
    just a live run, so it collapses to None and keeps the quote overlay. A
    future date is an error: there is nothing to report.
    """
    try:
        d = datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        raise SystemExit(f"--as-of must be YYYY-MM-DD, got '{raw}'")
    today = datetime.now().date()
    if d > today:
        raise SystemExit(f"--as-of {d} is in the future (today is {today})")
    if d == today:
        print(f"--as-of {d} is today — running live (quote overlay stays on)")
        return None
    return d


def main():
    parser = argparse.ArgumentParser(description="Market Intel Analysis")
    parser.add_argument("--tickers", nargs="+", default=None,
                        help="Stock tickers to analyze. Omit to run market mode "
                             "(indices, sector heatmap, risk ratios, macro).")
    parser.add_argument("--output", required=True, help="Output JSON file path")
    parser.add_argument("--source",
                        choices=["auto", "db", "pg", "yf"], default="auto",
                        help="Price source: pg/db=Postgres mkt.price_daily, "
                             "yf=yfinance, auto=Postgres with yf fallback")
    parser.add_argument("--no-live", action="store_true",
                        help="Skip all network calls (no live quote, no earnings, proxy macro)")
    parser.add_argument("--market", action="store_true",
                        help="Force the market-wide block on even when --tickers is given "
                             "(it is already on by default when --tickers is omitted)")
    parser.add_argument("--as-of", "--date", dest="as_of", default=None,
                        metavar="YYYY-MM-DD",
                        help="Run the report as of this date's close instead of today. "
                             "All series are truncated there and identity is resolved "
                             "at that date; the live quote overlay and the earnings "
                             "calendar are unavailable and reported as such.")
    args = parser.parse_args()

    as_of = parse_as_of(args.as_of) if args.as_of else None
    tickers = [t.upper() for t in args.tickers] if args.tickers else []
    # No watchlist means the market itself is the subject.
    want_market = args.market or not tickers
    live = not args.no_live
    end = (datetime.combine(as_of, datetime.min.time()) + timedelta(days=1)
           if as_of else datetime.now())
    # ~420 calendar days ≈ 290 trading days: enough for a real 200-day MA. The
    # old 250-day window silently returned null for ma_200 on the yfinance path.
    start = end - timedelta(days=420)

    report_date = as_of or datetime.now().date()
    results = {"date": report_date.strftime("%Y-%m-%d"),
               "mode": "market" if not tickers else "watchlist",
               "tickers": {}}
    if as_of:
        results["as_of_requested"] = str(as_of)
        results["historical"] = True
        results["historical_note"] = (
            "Point-in-time run: every series ends at this date and nothing after "
            "it was read. No live quote overlay (prices are that day's close) and "
            "no earnings calendar.")

    # --- source routing -----------------------------------------------------
    # "db" is kept as an alias for "pg" so older invocations keep working; it
    # used to mean a local file cache, which was retired in the Aug-2026 cutover.
    store = PG_BACKEND
    args.db = store

    use_db = False
    if args.source in ("db", "pg", "auto"):
        db_status = db_check(store, as_of)
        results["db_status"] = db_status
        if db_status["usable"]:
            use_db = True
        elif args.source in ("db", "pg"):
            print(f"ERROR: {db_status.get('error')}", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"Bar store unusable ({db_status.get('error')}) — falling back to yfinance")
            if as_of:
                print(f"  note: yfinance is being asked for {as_of}. It has deep "
                      f"history for the big ETFs but not for funds that had not "
                      f"launched yet — check unavailable_symbols in the output.")

    if use_db:
        subject = ", ".join(tickers) if tickers else "whole market"
        when = f" as of {as_of}" if as_of else ""
        print(f"Fetching data for: {subject}{when} [source: Postgres "
              f"mkt.price_daily @ {results['db_status']['last_bar_date']}]")
        results["source"] = "pg"
        if tickers:
            run_db_mode(tickers, args.db, live, results, as_of)

        if want_market:
            print("Building market-wide view...")
            mkt_data = load_prices_from_db(market_mode_symbols(), args.db,
                                           lookback_days=500, as_of=as_of)
            results["market"] = run_market_mode(mkt_data, as_of=as_of)

        print("Fetching macro data...")
        macro = get_macro_snapshot(as_of) if live else {}
        if not macro or all("error" in v or v.get("value") is None for v in macro.values()):
            print("  macro indices unavailable — using ETF proxies from cache")
            macro = get_macro_from_db(args.db, as_of)
            results["macro_is_proxy"] = True
        results["macro"] = macro

        with open(args.output, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Analysis complete. Output written to {args.output}")
        return

    # --- yfinance path (original behaviour) ---------------------------------
    results["source"] = "yf"
    subject = ", ".join(tickers) if tickers else "whole market"
    when = f" as of {as_of}" if as_of else ""
    print(f"Fetching data for: {subject}{when} [source: yfinance]")

    if want_market:
        print("Building market-wide view...")
        mkt_data = load_closes_yf(market_mode_symbols(), start, end)
        # Constituent breadth still comes from Postgres on the yfinance path —
        # it is a store query, not a price-source concern, and returns {} if the
        # store is unreachable.
        results["market"] = run_market_mode(mkt_data, as_of=as_of)

    if not tickers:
        print("Fetching macro data...")
        results["macro"] = get_macro_snapshot(as_of) if live else {}
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Analysis complete. Output written to {args.output}")
        return

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

    # Fetch sector ETF data. Reuse the shared loader — the previous inline
    # version raised KeyError on a single-ETF download (group_by="ticker" still
    # returns a MultiIndex) and swallowed it, leaving rel_perf_* silently null.
    sector_etf_data = {}
    if needed_sectors:
        if want_market and "market" in results:
            # Market mode already pulled every sector ETF; don't refetch.
            sector_frames = mkt_data
        else:
            sector_frames = load_closes_yf(sorted(needed_sectors), start, end)
        for etf in needed_sectors:
            if etf in sector_frames:
                sector_etf_data[etf] = sector_frames[etf]["Close"]

    # Analyze each ticker
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

        results["tickers"][t] = analyze_ticker(t, hist, spy_returns, sector_etf_data,
                                               live=live, as_of=as_of)

    # Macro snapshot
    print("Fetching macro data...")
    results["macro"] = get_macro_snapshot(as_of) if live else {}

    # Write output
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"Analysis complete. Output written to {args.output}")


if __name__ == "__main__":
    main()
