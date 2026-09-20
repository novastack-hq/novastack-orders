# Set up this laptop for NovaStack Orders (Windows).
# Installs uv if its missing, then hands over to tools\setup.py, which does the
# rest on every operating system. Safe to run again.
#
#   powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
#   powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1 --dry-run
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    $uvHome = Join-Path $env:USERPROFILE ".local\bin"
    if (-not (Test-Path (Join-Path $uvHome "uv.exe"))) {
        Write-Host "Installing uv, the Python project manager (https://docs.astral.sh/uv/) ..."
        powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    }
    $env:Path = "$uvHome;$env:Path"
}

# --no-project: run the set-up script before the project environment exists.
# --python 3.12: uv downloads Python 3.12 first if this laptop doesnt have it.
uv run --no-project --python 3.12 tools/setup.py @args
exit $LASTEXITCODE
