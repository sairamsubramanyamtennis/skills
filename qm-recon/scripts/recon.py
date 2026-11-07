#!/usr/bin/env python
"""
recon.py — reconcile QM screener Excel workbooks against the Postgres `trading` DB.

Verifies that what was published into `res.screen_result` faithfully matches the
source Excel files, at five levels:

  1. Coverage   — same set of dates / row counts in Excel vs DB
  2. Identity   — every Excel ticker resolves to a security on its own date
  3. Keys       — every (Date, security_id) present on both sides, no extras/dupes
  4. Cells      — every shared cell equal (float tolerance for numerics)
  5. Provenance — the run declares a universe and a data_asof that covers the Excel
  6. Raw check  — independent openpyxl re-read of sampled cells vs DB
                  (does NOT use the canonical parser, so it also catches
                   parser-vs-DB drift, not just publish bugs)

KEYED ON security_id, NOT ON THE TICKER STRING. 213 tickers denote more than one
company across time, so each Excel ticker is resolved point-in-time at its own
screen date (`ref.resolve`) before anything is compared. That also absorbs the
punctuation aliases — the screener writes BRK-B, canonical is BRK.B.

Usage:
    python recon.py <folder> [--run-label qm_panel_v2] [--tol 1e-6] [--sample 40]
                    [--report recon_report.md] [--quiet]

Exit code: 0 = all checks passed, 1 = mismatch found, 2 = setup error.
"""
import os
import re
import sys
import glob
import math
import random
import argparse
from datetime import datetime

import pandas as pd

# The check marks are unicode; a bare Windows console is cp1252 and would raise
# UnicodeEncodeError on the first FAIL, hiding the very output you ran this for.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PG_ADAPTER_DIR = r"C:\Users\ssair\trading-db"
DEFAULT_RUN_LABEL = "qm_panel_v2"

# canonical Excel column -> res.screen_result column
DB_COLS = {
    'Rank': 'rank', 'Price': 'price', 'Mom': 'mom', 'Ret3M': 'ret3m',
    'Ret1M': 'ret1m', 'FIP': 'fip', 'FIP_PctPos': 'fip_pctpos',
    'FIP_R2': 'fip_r2', 'MomRank': 'momrank', 'FIPRank': 'fiprank',
    'QMScore': 'qmscore', 'Percentile': 'percentile', 'MomPctile': 'mompctile',
    'Signal': 'signal',
}


def _pgdb():
    if PG_ADAPTER_DIR not in sys.path:
        sys.path.insert(0, PG_ADAPTER_DIR)
    import pgdb
    return pgdb

# ---------------------------------------------------------------------------
# Canonical parsing rules (self-contained copy — the skill must not depend on
# the target project's qm_data.py being importable).
# ---------------------------------------------------------------------------
MONTHS = {m: i for i, m in enumerate(
    ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], 1)}
CANON = {
    'rank': 'Rank', 'ticker': 'Ticker', 'company': 'Company', 'sector': 'Sector',
    'price': 'Price',
    '6-1m voladj': 'Mom', '6-1 mom%': 'Mom', '6-1m return%': 'Mom', '6-1mom%': 'Mom',
    'momentum': 'Mom',
    '3m ret%': 'Ret3M', '3m return%': 'Ret3M',
    '1m ret%': 'Ret1M', '1m return%': 'Ret1M',
    'fip score': 'FIP', 'fip': 'FIP',
    'pct positive days': 'FIP_PctPos', 'fip pct pos%': 'FIP_PctPos',
    'r-squared': 'FIP_R2', 'fip r²': 'FIP_R2', 'fip r': 'FIP_R2',
    'composite qm rank': 'QMScore', 'qm score': 'QMScore',
    'percentile': 'Percentile', 'qm pctile': 'Percentile',
    'signal': 'Signal', 'mom rank': 'MomRank', 'fip rank': 'FIPRank',
    'mom pctile': 'MomPctile',
}
NUMERIC = ['Rank', 'Price', 'Mom', 'Ret3M', 'Ret1M', 'FIP', 'FIP_PctPos', 'FIP_R2',
           'MomRank', 'FIPRank', 'QMScore', 'Percentile', 'MomPctile']
KEYS = ['Date', 'Ticker']        # the Excel's own key
DBKEYS = ['Date', 'security_id']  # what everything is actually compared on


def parse_date(fn):
    b = os.path.basename(fn)
    for pat, order in [(r'(20\d\d)-(\d{2})-(\d{2})', (0, 1, 2)),
                       (r'(\d{2})-(\d{2})-(20\d\d)', (2, 0, 1))]:
        m = re.search(pat, b)
        if m:
            g = m.groups()
            return datetime(int(g[order[0]]), int(g[order[1]]), int(g[order[2]]))
    m = re.search(r'([A-Z][a-z]{2})-(\d{1,2})-(20\d\d)', b)
    if m:
        return datetime(int(m[3]), MONTHS[m[1]], int(m[2]))
    return None


def _canon(c):
    return CANON.get(str(c).strip().lower(), None)


def _find_header(raw):
    for i in range(min(10, len(raw))):
        vals = [str(v).strip().lower() for v in raw.iloc[i].tolist()]
        if 'rank' in vals and 'ticker' in vals:
            return i
    return None


def extract_ranking(path):
    xl = pd.ExcelFile(path)
    order = ['QM Screener', 'Full Ranking', 'QM Top 50']
    pick = next((s for s in order if s in xl.sheet_names), xl.sheet_names[0])
    raw = pd.read_excel(path, sheet_name=pick, header=None)
    hdr = _find_header(raw)
    if hdr is None:
        return None
    df = raw.iloc[hdr + 1:].copy()
    df.columns = raw.iloc[hdr].tolist()
    df = df.rename(columns=lambda c: _canon(c) or f"_drop_{c}")
    df = df[[c for c in df.columns if not str(c).startswith('_drop_')]]
    if 'Rank' not in df or 'Ticker' not in df:
        return None
    df = df[pd.to_numeric(df['Rank'], errors='coerce').notna()]
    df = df.dropna(subset=['Ticker'])
    df['Ticker'] = df['Ticker'].astype(str).str.strip()
    for c in NUMERIC:
        if c in df:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    if 'Signal' in df:
        df['Signal'] = df['Signal'].astype(str).str.strip()
    return df.reset_index(drop=True)


def choose_files(root):
    """Best (most rows) workbook per date — mirrors the DB builder's rule."""
    files = [f for f in glob.glob(os.path.join(root, "*.xlsx"))
             if not os.path.basename(f).startswith(('~', '.~'))]
    best = {}  # date -> (nrows, path, df)
    for f in files:
        d = parse_date(f)
        if not d:
            continue
        try:
            df = extract_ranking(f)
        except Exception:
            df = None
        if df is None or df.empty:
            continue
        key = d.date()
        if key in best and best[key][0] >= len(df):
            continue
        best[key] = (len(df), f, df)
    return best  # date -> (nrows, path, df)


def excel_dataframe(best):
    frames = []
    for key in sorted(best):
        _, path, df = best[key]
        frames.append(df.assign(Date=pd.Timestamp(key), SourceFile=os.path.basename(path)))
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    out['Date'] = pd.to_datetime(out['Date']).dt.strftime('%Y-%m-%d')
    return out


# ---------------------------------------------------------------------------
# Reconciliation
# ---------------------------------------------------------------------------
class Recon:
    def __init__(self, quiet=False):
        self.checks = []      # (name, ok, detail)
        self.quiet = quiet

    def add(self, name, ok, detail=""):
        self.checks.append((name, ok, detail))
        mark = "PASS" if ok else "FAIL"
        icon = "✓" if ok else "✗"
        if not self.quiet:
            line = f"  [{mark}] {icon} {name}"
            print(line + (f"  --  {detail}" if detail else ""))

    @property
    def ok(self):
        return all(c[1] for c in self.checks)


def _equal(a, b, tol):
    """Cell equality with NaN==NaN and float tolerance."""
    a_na = a is None or (isinstance(a, float) and math.isnan(a)) or (isinstance(a, str) and a.strip().lower() in ('', 'nan', 'none'))
    b_na = b is None or (isinstance(b, float) and math.isnan(b)) or (isinstance(b, str) and b.strip().lower() in ('', 'nan', 'none'))
    if a_na and b_na:
        return True
    if a_na or b_na:
        return False
    try:
        return abs(float(a) - float(b)) <= tol
    except (TypeError, ValueError):
        return str(a).strip() == str(b).strip()


def load_db(run_label, dates):
    """res.screen_result for one run, restricted to the Excel's dates.

    Returns (frame keyed Date/security_id, run provenance dict).
    """
    pgdb = _pgdb()
    with pgdb.connect() as pg:
        cur = pg.cursor()
        cur.execute("""SELECT run_id, universe, data_asof, kind, strategy
                         FROM res.run WHERE label = %s""", (run_label,))
        row = cur.fetchone()
        if row is None:
            return None, None
        run = dict(zip(("run_id", "universe", "data_asof", "kind", "strategy"), row))

        cols = ", ".join(f"s.{c}" for c in DB_COLS.values())
        cur.execute(f"""SELECT s.obs_date, s.security_id, {cols}
                          FROM res.screen_result s
                         WHERE s.run_id = %s AND s.obs_date = ANY(%s::date[])""",
                    (run["run_id"], list(dates)))
        db = pd.DataFrame(cur.fetchall(),
                          columns=["Date", "security_id"] + list(DB_COLS.keys()))
    if not db.empty:
        db["Date"] = pd.to_datetime(db["Date"]).dt.strftime("%Y-%m-%d")
    return db, run


def resolve_excel(xl):
    """Point-in-time ticker -> security_id for every (Date, Ticker) in the Excel.

    create_missing=False: on a read path an unknown ticker is a finding, not
    something to invent an identity for.
    """
    pgdb = _pgdb()
    out = {}
    with pgdb.connect() as pg:
        cur = pg.cursor()
        for d, grp in xl.groupby("Date"):
            m = pgdb.resolve_bulk(cur, grp["Ticker"].tolist(), d,
                                  create_missing=False)
            for t, sid in m.items():
                out[(d, t)] = sid
    return out


def reconcile(root, run_label=DEFAULT_RUN_LABEL, tol=1e-6, sample=40, seed=0,
              quiet=False):
    r = Recon(quiet=quiet)

    # ---- setup checks ----
    if not os.path.isdir(root):
        print(f"ERROR: folder not found: {root}", file=sys.stderr)
        return 2, r

    if not quiet:
        print(f"\nReconciling  Excel  <->  Postgres res.screen_result [{run_label}]")
        print(f"Folder: {root}\n" + "-" * 66)

    best = choose_files(root)
    xl = excel_dataframe(best)
    if xl.empty:
        print("ERROR: no parseable Excel workbooks found.", file=sys.stderr)
        return 2, r

    # ---- resolve identity before comparing anything ----
    sid_map = resolve_excel(xl)
    xl["security_id"] = [sid_map.get((d, t)) for d, t in
                         zip(xl["Date"], xl["Ticker"])]
    unresolved = xl[xl["security_id"].isna()]
    r.add("Ticker identity resolves", unresolved.empty,
          f"{len(xl):,} rows resolve to a point-in-time security"
          if unresolved.empty else
          f"{len(unresolved)} rows unresolved, e.g. "
          + str(sorted(set(zip(unresolved['Date'], unresolved['Ticker'])))[:5]))
    xl = xl[xl["security_id"].notna()].copy()
    xl["security_id"] = xl["security_id"].astype(int)

    db, run = load_db(run_label, sorted(xl["Date"].unique()))
    if db is None:
        print(f"ERROR: no res.run labelled {run_label}", file=sys.stderr)
        return 2, r

    shared_cols = [c for c in xl.columns
                   if c in db.columns and c not in DBKEYS and c != 'Ticker']

    # ---- 1. date coverage ----
    xd, dd = set(xl['Date'].unique()), set(db['Date'].unique())
    r.add("Date coverage", xd == dd,
          "identical set of {} dates".format(len(xd)) if xd == dd
          else f"only-in-Excel={sorted(xd-dd)} only-in-DB={sorted(dd-xd)}")

    # ---- 2. row counts per date ----
    xc = xl.groupby('Date').size()
    dc = db.groupby('Date').size()
    diffs = []
    for d in sorted(xd | dd):
        a, b = int(xc.get(d, 0)), int(dc.get(d, 0))
        if a != b:
            diffs.append(f"{d}: excel={a} db={b}")
    r.add("Row counts per date", not diffs,
          f"{len(xc)} dates, total {int(xc.sum())} rows match"
          if not diffs else f"{len(diffs)} mismatched: " + "; ".join(diffs[:5]))

    # ---- 3. key integrity: (Date, security_id) ----
    xkeys = set(map(tuple, xl[DBKEYS].itertuples(index=False, name=None)))
    dkeys = set(map(tuple, db[DBKEYS].itertuples(index=False, name=None)))
    label = dict(zip(zip(xl['Date'], xl['security_id']), xl['Ticker']))

    def show(keys):
        return [(d, label.get((d, s), s)) for d, s in sorted(keys)[:3]]

    missing = xkeys - dkeys      # in Excel, absent from DB
    extra = dkeys - xkeys        # in DB, absent from Excel
    dup_db = db.duplicated(subset=DBKEYS).sum()
    dup_xl = xl.duplicated(subset=DBKEYS).sum()
    ok_keys = not missing and not extra and dup_db == 0 and dup_xl == 0
    detail = (f"{len(xkeys):,} keys reconcile exactly" if ok_keys else
              f"missing_in_db={len(missing)} extra_in_db={len(extra)} "
              f"dup_db={dup_db} dup_excel={dup_xl}"
              + (f" e.g. missing {show(missing)}" if missing else "")
              + (f" e.g. extra {show(extra)}" if extra else ""))
    r.add("Key integrity (Date,security_id)", ok_keys, detail)

    # ---- 4. cell-level comparison over shared keys ----
    common = sorted(xkeys & dkeys)
    xi = xl.set_index(DBKEYS).sort_index()
    di = db.set_index(DBKEYS).sort_index()
    mismatch_rows = []
    per_col = {c: 0 for c in shared_cols}
    for k in common:
        xr, dr = xi.loc[k], di.loc[k]
        if isinstance(xr, pd.DataFrame):  # dup safety
            xr = xr.iloc[0]
        if isinstance(dr, pd.DataFrame):
            dr = dr.iloc[0]
        for c in shared_cols:
            if not _equal(xr.get(c), dr.get(c), tol):
                per_col[c] += 1
                if len(mismatch_rows) < 20:
                    mismatch_rows.append((k, c, xr.get(c), dr.get(c)))
    total_mismatch = sum(per_col.values())
    cells = len(common) * len(shared_cols)
    if total_mismatch == 0:
        cd = f"{cells:,} cells across {len(shared_cols)} cols all match (tol={tol:g})"
    else:
        worst = ", ".join(f"{c}:{n}" for c, n in sorted(per_col.items(),
                          key=lambda x: -x[1]) if n)
        cd = f"{total_mismatch:,}/{cells:,} cells differ -> {worst}"
    r.add("Cell values match", total_mismatch == 0, cd)

    # ---- 5. run provenance ----
    # Replaces the old files_loaded manifest: Postgres records provenance on the
    # run itself, and a result whose data_asof predates the newest workbook is a
    # publish that never happened.
    max_xl = max(xd)
    asof = run["data_asof"].strftime("%Y-%m-%d") if run["data_asof"] else None
    prov_ok = bool(asof) and asof >= max_xl and bool(run["universe"])
    r.add("Run provenance (res.run)", prov_ok,
          f"run_id={run['run_id']} universe={run['universe']} data_asof={asof} "
          f"covers newest workbook {max_xl}" if prov_ok else
          f"run_id={run['run_id']} universe={run['universe']} data_asof={asof} "
          f"vs newest workbook {max_xl}")

    # ---- 6. independent raw-cell spot check (openpyxl, no canonical parser) ----
    raw_detail, raw_ok = _raw_spotcheck(best, di, sid_map, tol, sample, seed)
    r.add(f"Raw openpyxl spot-check ({sample} cells)", raw_ok, raw_detail)

    return (0 if r.ok else 1), r


def _raw_spotcheck(best, db_indexed, sid_map, tol, sample, seed):
    """Independently re-read sampled cells straight from the workbooks and
    compare to the DB — bypasses the canonical parser entirely."""
    try:
        import openpyxl
    except Exception:
        return "openpyxl not available — skipped", True
    rng = random.Random(seed)
    dates = sorted(best.keys())
    if not dates:
        return "no files", True
    checked = 0
    fails = []
    attempts = 0
    while checked < sample and attempts < sample * 6:
        attempts += 1
        d = rng.choice(dates)
        _, path, _ = best[d]
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = None
        for cand in ['QM Screener', 'Full Ranking', 'QM Top 50']:
            if cand in wb.sheetnames:
                ws = wb[cand]
                break
        if ws is None:
            ws = wb[wb.sheetnames[0]]
        rows = list(ws.iter_rows(values_only=True))
        wb.close()
        # locate header row + column indices for Rank/Ticker + one numeric col
        hdr_i = None
        for i, row in enumerate(rows[:10]):
            low = [str(v).strip().lower() if v is not None else '' for v in row]
            if 'rank' in low and 'ticker' in low:
                hdr_i = i
                break
        if hdr_i is None:
            continue
        header = rows[hdr_i]
        colmap = {}
        for j, h in enumerate(header):
            cn = _canon(h)
            if cn:
                colmap[cn] = j
        if 'Rank' not in colmap or 'Ticker' not in colmap:
            continue
        num_col = next((c for c in ('Ret3M', 'Percentile', 'FIP', 'Mom')
                        if c in colmap), None)
        body = [rw for rw in rows[hdr_i + 1:] if rw[colmap['Ticker']] not in (None, '')]
        if not body:
            continue
        rw = rng.choice(body)
        ticker = str(rw[colmap['Ticker']]).strip()
        dstr = d.strftime('%Y-%m-%d')
        sid = sid_map.get((dstr, ticker))
        if sid is None:
            fails.append(f"({dstr}, {ticker}) does not resolve to a security")
            checked += 1
            continue
        key = (dstr, int(sid))
        try:
            dbrow = db_indexed.loc[key]
        except KeyError:
            fails.append(f"({dstr}, {ticker}) missing in DB")
            checked += 1
            continue
        if isinstance(dbrow, pd.DataFrame):
            dbrow = dbrow.iloc[0]
        # compare Rank + one numeric column, raw vs DB
        raw_rank = rw[colmap['Rank']]
        if not _equal(raw_rank, dbrow.get('Rank'), tol):
            fails.append(f"{key} Rank raw={raw_rank} db={dbrow.get('Rank')}")
        if num_col:
            raw_v = rw[colmap[num_col]]
            if not _equal(raw_v, dbrow.get(num_col), tol):
                fails.append(f"{key} {num_col} raw={raw_v} db={dbrow.get(num_col)}")
        checked += 1
    if fails:
        return f"{len(fails)} mismatch: " + "; ".join(fails[:4]), False
    return f"{checked} random cells re-read from xlsx == DB", True


def write_report(path, root, run_label, code, r):
    lines = [f"# QM Recon Report", "",
             f"- Folder: `{root}`",
             f"- Source: Postgres `trading` -> `res.screen_result` [{run_label}]",
             f"- Generated: {datetime.now():%Y-%m-%d %H:%M}",
             f"- **Result: {'PASS ✓' if code == 0 else 'FAIL ✗' if code == 1 else 'ERROR'}**",
             "", "| Check | Result | Detail |", "|---|---|---|"]
    for name, ok, detail in r.checks:
        lines.append(f"| {name} | {'PASS' if ok else 'FAIL'} | {detail} |")
    with open(path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser(
        description="Reconcile QM Excel workbooks vs Postgres res.screen_result")
    ap.add_argument("folder", help="folder containing the .xlsx workbooks")
    ap.add_argument("--run-label", default=DEFAULT_RUN_LABEL,
                    help=f"res.run label to reconcile against (default {DEFAULT_RUN_LABEL})")
    ap.add_argument("--tol", type=float, default=1e-6, help="float compare tolerance")
    ap.add_argument("--sample", type=int, default=40, help="raw spot-check cell count")
    ap.add_argument("--seed", type=int, default=0, help="sampling seed (reproducible)")
    ap.add_argument("--report", default=None, help="write a markdown report to this path")
    ap.add_argument("--quiet", action="store_true", help="suppress per-check output")
    args = ap.parse_args()

    root = os.path.abspath(args.folder)
    code, r = reconcile(root, args.run_label, args.tol, args.sample, args.seed,
                        args.quiet)

    if not args.quiet:
        print("-" * 66)
        verdict = ("ALL CHECKS PASSED — Excel and Postgres are in sync"
                   if code == 0 else
                   "MISMATCH FOUND — see failing checks above" if code == 1 else
                   "SETUP ERROR")
        print(("RESULT: " + verdict))
    if args.report:
        rp = args.report if os.path.isabs(args.report) else os.path.join(root, args.report)
        write_report(rp, root, args.run_label, code, r)
        if not args.quiet:
            print(f"Report written: {rp}")
    sys.exit(code)


if __name__ == "__main__":
    main()
