param(
    [string]$Python = "$PSScriptRoot\.venv\Scripts\python.exe",
    [ValidateRange(1, 128)]
    [int]$BlasThreads = 1
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
$env:OPENBLAS_NUM_THREADS = "$BlasThreads"
$env:OMP_NUM_THREADS = "$BlasThreads"
$env:MKL_NUM_THREADS = "$BlasThreads"
& $Python -B $MainPath
if ($LASTEXITCODE -ne 0) {
    throw "CAISSA-JEPA exited with code $LASTEXITCODE"
}
