# Launch JARVIS Voice Assistant
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "     Starting JARVIS AI Voice Assistant...          " -ForegroundColor Yellow
Write-Host "====================================================" -ForegroundColor Cyan

$VenvPython = Join-Path $PSScriptRoot "venv\Scripts\python.exe"
$MainScript = Join-Path $PSScriptRoot "main.py"

if (Test-Path $VenvPython) {
    & $VenvPython $MainScript
} else {
    python $MainScript
}
