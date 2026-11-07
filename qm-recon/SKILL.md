---
name: qm-recon
description: |
  Reconcile QM screener Excel workbooks against the Postgres `trading` database
  (res.screen_result) to verify the two data sources match exactly. Use this skill
  whenever the user wants to verify, reconcile, audit, cross-check, or validate that
  the published database data matches the source Excel files — e.g. "reconcile the qm
  data", "verify excel and postgres match", "check the database against the
  spreadsheets", "run a recon on the qm-results folder", "audit the qm panel", "did
  the screen publish correctly", "do the excel and database agree". Takes a folder as
  argument (the folder holding the .xlsx workbooks) and reports a per-check PASS/FAIL
  with an exit code. Built for the QM screener workbooks (Wes Gray / Alpha Architect
  momentum) but works on any folder following that layout.
---

# QM Recon — Excel ↔ Postgres Reconciliation

## What this skill does

Independently verifies that what was published into `res.screen_result` faithfully
matches the source QM screener Excel workbooks in a folder. It re-parses every dated
`.xlsx`, reads the run's rows out of Postgres, and compares them across six checks:

1. **Ticker identity resolves** — every Excel ticker maps to a security *on its own
   screen date* via `ref.resolve`. A ticker that resolves to nothing is a finding, not
   something to invent an identity for.
2. **Date coverage** — the exact same set of screen dates on both sides
3. **Row counts per date** — same number of stocks screened each day
4. **Key integrity** — every `(Date, security_id)` present on both sides; no missing,
   extra, or duplicate keys
5. **Cell values** — every shared cell equal, with float tolerance for numerics
   and NaN==NaN handling
6. **Run provenance** — `res.run` declares a universe and a `data_asof` that actually
   covers the newest workbook. A run whose `data_asof` predates the latest Excel is a
   publish that never happened.
7. **Raw openpyxl spot-check** — a random sample of cells re-read *directly* from
   the workbooks with openpyxl (bypassing the canonical parser), compared to the
   DB. This catches parser-vs-DB drift, not just publish bugs.

**Everything is compared on `security_id`, never on the ticker string.** 213 tickers
denote more than one company across time, so each Excel ticker is resolved
point-in-time before any comparison. That also absorbs the punctuation aliases — the
screener writes `BRK-B`, canonical is `BRK.B`, and both resolve to the same security.

It exits `0` when everything matches, `1` on any mismatch, `2` on a setup error
(missing folder, or no run with that label), so it can be wired into automation.

## How to run it

The skill takes the **folder** containing the `.xlsx` workbooks as its argument.
Postgres must be up (localhost:5433, via `C:\Users\ssair\trading-db\pgdb.py`).

```bash
python "<skill_dir>/scripts/recon.py" "<FOLDER>"
```

For the user's QM workspace that is:

```bash
python "C:/Users/ssair/.claude/skills/qm-recon/scripts/recon.py" "C:/Users/ssair/qm-results"
```

### Options

| Flag | Default | Purpose |
|---|---|---|
| `--run-label NAME` | `qm_panel_v2` | which `res.run` to reconcile against |
| `--tol X` | `1e-6` | float comparison tolerance |
| `--sample N` | `40` | number of cells for the raw openpyxl spot-check |
| `--seed N` | `0` | sampling seed (reproducible spot-checks) |
| `--report PATH` | — | also write a Markdown report (relative paths land in the folder) |
| `--quiet` | off | suppress per-check console output (rely on exit code) |

Example with a report:

```bash
python "<skill_dir>/scripts/recon.py" "C:/Users/ssair/qm-results" --report recon_report.md
```

## When invoked

1. Determine the target folder from the user's request (default to
   `C:/Users/ssair/qm-results` if they clearly mean the QM workspace but don't
   name a path).
2. Run `scripts/recon.py` on that folder, adding `--report` if the user wants a
   saved artifact.
3. Report the outcome: overall PASS/FAIL, and for any failing check quote the
   detail line (which dates/keys/columns diverged). If dates are missing on the DB
   side, the fix is to re-publish those screens (`qm_pg.publish()` in the QM
   workspace), not to edit the workbooks.

## Notes

- **Last verified 2026-08-05:** all 7 checks PASS over 152 dates / 75,469 rows /
  1,056,566 cells. The conversion also caught what the previous file-based version was
  blind to — its local mirror had frozen three screens behind, because the live pipeline
  publishes only to Postgres now.
- The script is **self-contained** — it carries its own copy of the canonical
  parsing rules, so it does not depend on the target project's `qm_data.py`
  being importable. This keeps the reconciliation independent.
- It only ever reads; it never writes to Postgres or the Excel files.
- Requires `pandas`, `psycopg2`, `openpyxl` (the last only for the raw spot-check;
  skipped gracefully if absent). All are already present in the user's environment.

---

## Telemetry (standing requirement — all skills)

Log this run **once, at the very end**, whether it went well or not (Bash tool; forward slashes):

```bash
python C:/Users/ssair/.claude/telemetry/telemetry.py log --skill qm-recon \
  --outcome delivered|partial|blocked|corrected|routed \
  --asked    "what he actually wanted, one line" \
  --produced "what he got, one line" \
  [--friction "what slowed it down or went wrong"] [--routed-to <skill>] [--tags a,b]
```

* `corrected` = Sai had to push back before it was right. **Log it.** A telemetry file that is all
  `delivered` is worthless for skill health — the corrections and blocks are the whole point.
* One record per run, not per step. Silent side effect: never announce it, never ask permission for
  it, never let it delay or clutter the answer.
* Paraphrase in `--asked`; never log credentials, birth data, account numbers or verbatim personal
  detail. If the call fails, drop it and move on.

Full contract: `C:/Users/ssair/.claude/telemetry/TELEMETRY.md` · read it back in the Recap app's
Telemetry page or via `telemetry.py stats --days 30`.
