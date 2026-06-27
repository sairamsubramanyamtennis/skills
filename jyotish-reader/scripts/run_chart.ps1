# run_chart.ps1 — invoke compute_chart.py through the pinned 3.11 venv.
# Creates/repairs the venv on first run, then forwards all args to the script.
#
#   ./scripts/run_chart.ps1 --date 1990-08-15 --time "09:42 AM" `
#       --lat 13.0827 --lon 80.2707 --tz Asia/Kolkata --asof 2026-06-22
#
$ErrorActionPreference = "Stop"
$root   = Split-Path -Parent $PSScriptRoot          # skill root
$venv   = Join-Path $root ".venv"
$py     = Join-Path $venv "Scripts\python.exe"
$req    = Join-Path $PSScriptRoot "requirements.txt"
$script = Join-Path $PSScriptRoot "compute_chart.py"

if (-not (Test-Path $py)) {
    Write-Host "Creating Python 3.11 venv at $venv ..."
    py -3.11 -m venv $venv
    & $py -m pip install --quiet --upgrade pip
    & $py -m pip install --quiet -r $req
}
# Verify deps are importable; (re)install if the venv is stale.
& $py -c "import swisseph, tzdata" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing pinned dependencies ..."
    & $py -m pip install --quiet -r $req
}

& $py $script @args
exit $LASTEXITCODE
