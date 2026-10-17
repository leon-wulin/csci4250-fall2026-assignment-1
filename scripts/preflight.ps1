# Validate the existing local environment; never install packages or create environments.
[CmdletBinding()]
param([string]$CondaExe)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $CondaExe) {
    $condaCommand = Get-Command conda -ErrorAction SilentlyContinue
    if ($condaCommand) {
        $CondaExe = $condaCommand.Name
    } else {
        # Verified from the installed Anaconda registration on this machine.
        $CondaExe = 'C:\ProgramData\anaconda3\Scripts\conda.exe'
    }
}
if (-not (Get-Command $CondaExe -ErrorAction SilentlyContinue)) {
    throw 'Conda is unavailable. Supply a verified -CondaExe path; do not use system Python.'
}

Push-Location -LiteralPath $projectRoot
try {
    Write-Host "Project root: $projectRoot"
    Write-Host "Conda command: $CondaExe"
    & $CondaExe --version
    if ($LASTEXITCODE -ne 0) { throw 'Conda version check failed.' }
    $environmentJson = & $CondaExe env list --json
    if ($LASTEXITCODE -ne 0) { throw 'Conda environment listing failed.' }
    $environmentPaths = ($environmentJson -join "`n" | ConvertFrom-Json).envs
    $matchingEnvironments = @($environmentPaths | Where-Object { (Split-Path $_ -Leaf) -eq 'fons-a1' })
    if ($matchingEnvironments.Count -ne 1) { throw 'Expected one registered fons-a1 environment; inspect conda env list.' }
    Write-Host "Registered fons-a1: $($matchingEnvironments[0])"

    & $CondaExe run -n fons-a1 --no-capture-output python scripts/check_environment.py
    if ($LASTEXITCODE -ne 0) { throw 'Python environment preflight failed.' }
    & $CondaExe run -n fons-a1 --no-capture-output python -m pip --version
    if ($LASTEXITCODE -ne 0) { throw 'Environment pip is unavailable.' }
    & $CondaExe run -n fons-a1 --no-capture-output python -m pip check
    if ($LASTEXITCODE -ne 0) { throw 'Dependency consistency check failed.' }
    Write-Host 'PASS: Local startup preflight completed.'
} finally {
    Pop-Location
}
