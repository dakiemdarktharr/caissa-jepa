param(
    [int]$AdditionalEpochs = 5,
    [string]$Model = "chess_data\caissa_a_jepa_v7.npz",
    [ValidateSet("adversarial-jepa", "policy-value")]
    [string]$Architecture = "adversarial-jepa",
    [ValidateSet("h1", "h1-h2", "full", "no-response", "direct")]
    [string]$ModelVariant = "full",
    [int]$BatchSize = 64,
    [int]$LatentSize = 96,
    [int]$ValidationPercent = 10,
    [int]$Seed = 20260903,
    [double]$ProgressInterval = 10.0,
    [switch]$AllowPartialDataset,
    [switch]$AllowDatasetChange
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Definition
$Runner = Join-Path $Root "run_caissa_jepa_v7.ps1"

if ($AdditionalEpochs -lt 1) {
    throw "AdditionalEpochs must be at least 1"
}

$arguments = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $Runner,
    "-Mode", "continue-train",
    "-Epochs", "$AdditionalEpochs",
    "-Model", $Model,
    "-Architecture", $Architecture,
    "-ModelVariant", $ModelVariant,
    "-BatchSize", "$BatchSize",
    "-LatentSize", "$LatentSize",
    "-ValidationPercent", "$ValidationPercent",
    "-Seed", "$Seed",
    "-ProgressInterval", "$ProgressInterval"
)
if ($AllowPartialDataset) {
    $arguments += "-AllowPartialDataset"
}
if ($AllowDatasetChange) {
    $arguments += "-AllowDatasetChange"
}

& powershell.exe @arguments
if ($LASTEXITCODE -ne 0) {
    throw "Continued training failed with exit code $LASTEXITCODE"
}
