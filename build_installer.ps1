param(
    [string]$Python = "D:\chess_robot_app\.venv\Scripts\python.exe",
    [string]$OutputDir = "dist",
    [string]$InnoCompiler = "",
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
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
# Do not let unrelated tools on PATH inject their ICU/OpenSSL/UCRT DLLs.
# In particular, Poppler's ICU has versioned exports incompatible with Qt's
# Windows ICU dependency. Keep this environment local to the build process.
$pythonBase = (& $Python -c "import sys; print(sys.base_prefix)").Trim()
$qtDirectory = (& $Python -c "from pathlib import Path; import PySide6; print(Path(PySide6.__file__).parent)").Trim()
$isolatedBuildPath = ((Split-Path -Parent $Python), $pythonBase, $qtDirectory, "$env:WINDIR\System32", $env:WINDIR) -join ';'
$buildTools = Join-Path $Root 'build\build-tools'
if (Test-Path -LiteralPath $buildTools) { $env:PYTHONPATH = "$buildTools;$env:PYTHONPATH" }
& $Python -B (Join-Path $Root 'release_manifest.py')
if ($LASTEXITCODE -ne 0) { throw 'Build manifest failed' }
& $Python -c "import PyInstaller" 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller is not installed. Run: $Python -m pip install -r requirements-build.txt"
}
$pyinstallerArgs = @(
    "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed",
    "--name", "Caissa-JEPA", "--distpath", $distRoot,
    "--workpath", $workDir, "--specpath", $specDir,
    "--add-data", "$Root\assets;assets",
    "--add-data", "$Root\build\build_manifest.json;.",
    "--hidden-import", "numpy",
    "--copy-metadata", "numpy", "--copy-metadata", "PySide6", "--copy-metadata", "shiboken6",
    (Join-Path $Root "app_entry.py")
)
$previousBuildPath = $env:PATH
try {
    $env:PATH = $isolatedBuildPath
    & $Python @pyinstallerArgs
}
finally { $env:PATH = $previousBuildPath }
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE"
}
# Python 3.9 ships VC 14.29, while modern Qt requires newer exported symbols.
# The bootloader loads root DLLs first, so copying only Qt's private runtime
# leaves a successfully built executable that cannot import QtWidgets.
$qtDirectory = (& $Python -c "from pathlib import Path; import PySide6; print(Path(PySide6.__file__).parent)").Trim()
foreach ($runtimeDll in @('VCRUNTIME140.dll', 'VCRUNTIME140_1.dll', 'MSVCP140.dll', 'MSVCP140_1.dll', 'MSVCP140_2.dll')) {
    $runtimeSource = Join-Path $qtDirectory $runtimeDll
    if (Test-Path -LiteralPath $runtimeSource) {
        Copy-Item -LiteralPath $runtimeSource -Destination (Join-Path $bundleDir '_internal') -Force
    }
}
$smokeReceipt = Join-Path $Root 'build\release-smoke.json'
$probe = Start-Process -FilePath (Join-Path $bundleDir 'Caissa-JEPA.exe') -ArgumentList @('--self-test', ('"' + $smokeReceipt + '"')) -WindowStyle Hidden -PassThru
$probeDeadline = (Get-Date).AddMinutes(3)
while (-not $probe.WaitForExit(1000)) {
    if ((Get-Date) -gt $probeDeadline) {
        Stop-Process -Id $probe.Id
        throw 'Frozen application self-test timed out. Installer was not produced.'
    }
}
if ($probe.ExitCode -ne 0) { throw "Frozen self-test failed; inspect $smokeReceipt" }
$receipt = Get-Content -LiteralPath $smokeReceipt -Raw | ConvertFrom-Json
if ($receipt.status -ne 'PASSED' -or -not $receipt.frozen) { throw 'Frozen test receipt did not pass' }
if (-not $SkipInstaller) {
    $programFilesX86 = [Environment]::GetEnvironmentVariable("ProgramFiles(x86)")
    $innoCandidates = @(@($InnoCompiler, (Join-Path $Root 'build\inno\ISCC.exe')) | Where-Object { $_ })
    if ($programFilesX86) {
        $innoCandidates += Join-Path $programFilesX86 "Inno Setup 6\ISCC.exe"
    }
    if ($env:ProgramFiles) {
        $innoCandidates += Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe"
    }
    $iscc = $innoCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if ($null -eq $iscc) {
        throw "Inno Setup was not found. Pass -InnoCompiler or explicitly use -SkipInstaller for a portable-only build."
    }
    else {
        & $iscc "/DAppBuildDir=$bundleDir" (Join-Path $Root "installer\Caissa-JEPA.iss")
        if ($LASTEXITCODE -ne 0) {
            throw "Inno Setup failed with exit code $LASTEXITCODE"
        }
    }
}
Write-Output "Desktop bundle ready: $bundleDir"
