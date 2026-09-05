param(
    [string]$Python = "D:\chess_robot_app\.venv\Scripts\python.exe"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location -LiteralPath $Root

$MainPath = Join-Path $Root "main.py"
if (-not (Test-Path -LiteralPath $MainPath)) {
    throw "Application entry point not found: $MainPath"
}

if (-not (Test-Path -LiteralPath $Python)) {
    $PythonCommand = Get-Command python -ErrorAction Stop
    $Python = $PythonCommand.Source
}

Write-Host ("> {0} -B {1}" -f $Python, $MainPath) -ForegroundColor DarkGray
& $Python -B $MainPath
if ($LASTEXITCODE -ne 0) {
    throw "CAISSA-JEPA exited with code $LASTEXITCODE"
}
