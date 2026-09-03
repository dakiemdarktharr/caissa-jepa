param(
    [ValidateSet("tests", "crawl", "status", "train", "evaluate", "all")]
    [string]$Mode = "status",
    [string]$Python = "D:\chess_robot_app\.venv\Scripts\python.exe",
    [double]$TargetGB = 4.0,
    [int]$Latest = 0,
    [int]$Oldest = 1200,
    [double]$RequestGap = 1.0,
    [int]$Epochs = 5,
    [int]$BatchSize = 64,
    [int]$LatentSize = 96,
    [int]$ValidationPercent = 10,
    [int]$Seed = 20260903,
    [ValidateSet("adversarial-jepa", "policy-value")]
    [string]$Architecture = "adversarial-jepa",
    [switch]$ForegroundCrawl,
    [switch]$AllowPartialDataset
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location -LiteralPath $Root

if (-not (Test-Path -LiteralPath $Python)) {
    $PythonCommand = Get-Command python -ErrorAction Stop
    $Python = $PythonCommand.Source
}

function Invoke-V7Python {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)
    Write-Host ("> {0} -B {1}" -f $Python, ($Arguments -join " "))
    & $Python -B @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed with exit code $LASTEXITCODE"
    }
}

function Get-DatasetManifest {
    $manifestPath = Join-Path $Root "fen_dataset\dataset_manifest.json"
    if (-not (Test-Path -LiteralPath $manifestPath)) {
        return $null
    }
    return Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
}

function Invoke-Tests {
    Invoke-V7Python @("-m", "py_compile", "main.py", "fen_dataset_tool.py", "adversarial_jepa.py", "policy_value_baseline.py", "train_caissa_v7.py", "evaluate_action_ranking.py", "test_core.py", "test_v7.py", "test_gui_v7.py")
    Invoke-V7Python @("test_core.py")
    Invoke-V7Python @("test_v7.py")
    Invoke-V7Python @("test_gui_v7.py")
    Write-Host "V7 TESTS PASSED" -ForegroundColor Green
}

function Start-Crawl {
    $existing = Get-CimInstance Win32_Process | Where-Object {
        $_.Name -match "python" -and
        $_.CommandLine -match "fen_dataset_tool.py" -and
        $_.CommandLine -match "crawl-twic" -and
        $_.CommandLine -match [regex]::Escape($Root)
    }
    if ($existing) {
        Write-Host "Crawler is already running: $($existing.ProcessId -join ', ')"
        return
    }

    $stdout = Join-Path $Root "fen_dataset_crawl.log"
    $stderr = Join-Path $Root "fen_dataset_crawl.err.log"
    $arguments = @(
        "-B", "fen_dataset_tool.py", "crawl-twic",
        "--output", "fen_dataset",
        "--target-gb", "$TargetGB",
        "--shard-mb", "256",
        "--oldest", "$Oldest",
        "--timeout", "45",
        "--retries", "8",
        "--backoff", "2",
        "--request-gap", "$RequestGap"
    )
    if ($Latest -gt 0) {
        $arguments += @("--latest", "$Latest")
    }

    if ($ForegroundCrawl) {
        Invoke-V7Python $arguments
        return
    }

    $process = Start-Process -FilePath $Python -ArgumentList $arguments -WorkingDirectory $Root -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
    Write-Host "Crawler started in background. PID=$($process.Id)"
    Write-Host "Status: .\run_caissa_jepa_v7.ps1 -Mode status"
    Write-Host "Log:    $stdout"
}

function Assert-DatasetReady {
    $manifest = Get-DatasetManifest
    if ($null -eq $manifest) {
        throw "Dataset manifest not found. Run -Mode crawl first."
    }
    if (-not $AllowPartialDataset -and $manifest.status -notin @("TARGET_REACHED", "COMPLETE")) {
        throw "Dataset is not complete (status=$($manifest.status)). Use -AllowPartialDataset only for a deliberate partial experiment."
    }
}

function Invoke-Train {
    Assert-DatasetReady
    $model = "chess_data\caissa_a_jepa_v7.npz"
    $arguments = @(
        "train_caissa_v7.py",
        "--architecture", $Architecture,
        "--dataset", "fen_dataset",
        "--model", $model,
        "--epochs", "$Epochs",
        "--batch-size", "$BatchSize",
        "--latent-size", "$LatentSize",
        "--validation-percent", "$ValidationPercent",
        "--seed", "$Seed"
    )
    if ($AllowPartialDataset) {
        $arguments += "--allow-dataset-change"
    }
    Invoke-V7Python $arguments
    Write-Host "Checkpoint: $(Join-Path $Root $model)" -ForegroundColor Green
}

function Invoke-Evaluate {
    Assert-DatasetReady
    $model = "chess_data\caissa_a_jepa_v7.npz"
    if (-not (Test-Path -LiteralPath (Join-Path $Root $model))) {
        throw "Checkpoint not found. Run -Mode train first."
    }
    Invoke-V7Python @(
        "evaluate_action_ranking.py",
        "--dataset", "fen_dataset",
        "--model", $model,
        "--architecture", $Architecture,
        "--split", "validation",
        "--validation-percent", "$ValidationPercent",
        "--max-positions", "1000"
    )
}

switch ($Mode) {
    "tests"   { Invoke-Tests }
    "crawl"   { Start-Crawl }
    "status"  { Invoke-V7Python @("fen_dataset_tool.py", "status", "--output", "fen_dataset") }
    "train"   { Invoke-Train }
    "evaluate" { Invoke-Evaluate }
    "all" {
        Invoke-Tests
        Start-Crawl
        if ($ForegroundCrawl) {
            Invoke-Train
            Invoke-Evaluate
        } else {
            Write-Host "Crawl is running in background. After status=TARGET_REACHED, run -Mode train and then -Mode evaluate."
        }
    }
}
