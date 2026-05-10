param(
    [int]$Port = 8502
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvActivate = Join-Path $ProjectRoot ".venv\Scripts\Activate.ps1"
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Requirements = Join-Path $ProjectRoot "media_update_broadcaster\requirements.txt"
$App = Join-Path $ProjectRoot "media_update_broadcaster\main.py"

Set-Location $ProjectRoot

if (-not (Test-Path $VenvPython)) {
    python -m venv .venv
}

. $VenvActivate
python -m pip install -r $Requirements
streamlit run $App --server.address 127.0.0.1 --server.port $Port
