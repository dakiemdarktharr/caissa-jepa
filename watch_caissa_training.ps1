param(
    [string]$Model = "chess_data\caissa_a_jepa_v7.npz",
    [switch]$Follow,
    [int]$IntervalSeconds = 10
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Definition
$Runner = Join-Path $Root "run_caissa_jepa_v7.ps1"

if ($IntervalSeconds -lt 1) {
    throw "IntervalSeconds must be at least 1"
}

do {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Runner -Mode train-status -Model $Model
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to read training progress"
    }
    if (-not $Follow) {
        break
    }
    Start-Sleep -Seconds $IntervalSeconds
} while ($true)
