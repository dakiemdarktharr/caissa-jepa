param(
    [string]$Python = "D:\chess_robot_app\.venv\Scripts\python.exe",
    [string]$OutputDir = "dist",
    [switch]$SkipInstaller
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location -LiteralPath $Root
if (-not (Test-Path -LiteralPath $Python)) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $pythonCommand) {
        throw "Python was not found. Pass -Python with the project virtual-environment interpreter."
    }
    $Python = $pythonCommand.Source
}
$distRoot = Join-Path $Root $OutputDir
$bundleDir = Join-Path $distRoot "Caissa-JEPA"
$workDir = Join-Path $Root "build\pyinstaller"
$specDir = Join-Path $Root "build\spec"
New-Item -ItemType Directory -Force -Path $distRoot, $workDir, $specDir | Out-Null
& $Python -c "import PyInstaller" 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller is not installed. Run: $Python -m pip install -r requirements-build.txt"
}
$pyinstallerArgs = @(
    "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed",
    "--name", "Caissa-JEPA", "--distpath", $distRoot,
    "--workpath", $workDir, "--specpath", $specDir,
    "--add-data", "$Root\assets;assets",
    "--collect-all", "PySide6", "--hidden-import", "numpy",
    (Join-Path $Root "main.py")
)
& $Python @pyinstallerArgs
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE"
}
if (-not $SkipInstaller) {
    $programFilesX86 = [Environment]::GetEnvironmentVariable("ProgramFiles(x86)")
    $innoCandidates = @()
    if ($programFilesX86) {
        $innoCandidates += Join-Path $programFilesX86 "Inno Setup 6\ISCC.exe"
    }
    if ($env:ProgramFiles) {
        $innoCandidates += Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe"
    }
    $iscc = $innoCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if ($null -eq $iscc) {
        Write-Warning "Inno Setup 6 was not found. The PyInstaller bundle is ready at $bundleDir."
        Write-Warning "Install Inno Setup 6, then rerun this script to produce the EXE installer."
    }
    else {
        & $iscc "/DAppBuildDir=$bundleDir" (Join-Path $Root "installer\Caissa-JEPA.iss")
        if ($LASTEXITCODE -ne 0) {
            throw "Inno Setup failed with exit code $LASTEXITCODE"
        }
    }
}
Write-Output "Desktop bundle ready: $bundleDir"