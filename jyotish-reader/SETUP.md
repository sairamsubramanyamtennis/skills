# Setup — chart computation environment

`scripts/compute_chart.py` needs `pyswisseph` (Swiss Ephemeris) and, on Windows,
`tzdata`. **Use Python 3.11** — it has prebuilt `pyswisseph` Windows wheels.
Python 3.12 and 3.14 on this machine have no wheel and no C compiler, so the
build fails. A skill-local virtual environment pins a known-good combination.

## One-time setup

```powershell
cd "$env:USERPROFILE\.claude\skills\jyotish-reader"
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install -r scripts\requirements.txt
```

This was created and verified on 2026-06-22 with:

| Component   | Version    |
|-------------|------------|
| Python      | 3.11.4     |
| pyswisseph  | 2.10.3.2   |
| tzdata      | 2026.2     |

The `.venv/` folder is local to the skill and is the intended runtime; it is not
tracked anywhere and can be deleted and recreated with the commands above.

## Running

Either call the venv interpreter directly:

```powershell
.venv\Scripts\python scripts\compute_chart.py --date 1990-08-15 --time "09:42 AM" `
    --lat 13.0827 --lon 80.2707 --tz Asia/Kolkata --asof 2026-06-22
```

…or use the wrapper, which self-heals the venv (creates it / reinstalls deps if
missing) and forwards every argument:

```powershell
scripts\run_chart.ps1 --date 1990-08-15 --time "09:42 AM" `
    --lat 13.0827 --lon 80.2707 --tz Asia/Kolkata --asof 2026-06-22
```

Add `--json` for machine-readable output. See the docstring in
`scripts/compute_chart.py` for the full flag list (vargas, dasha span, lifespan,
`--asof`, `--no-dasha`, `--no-sadesati`).

## Why not just `pip install pyswisseph`?

- On **Python 3.11** it installs from a wheel — no compiler needed. ✅
- On **Python 3.12 / 3.14** here, pip tries to build from source and fails for
  lack of a C toolchain. ❌
- `tzdata` is mandatory on Windows: without it `ZoneInfo("Asia/Kolkata")` raises
  `ZoneInfoNotFoundError`, since Windows ships no system IANA tz database.
