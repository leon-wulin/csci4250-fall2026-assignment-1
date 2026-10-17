# Run from the project root in PowerShell: .\init_folders.ps1
# Safe to re-run: creates missing directories only; never deletes or overwrites course files.
$folders = @(
    'data/raw', 'data/processed', 'src', 'tests',
    'results/tables', 'results/plots', 'results/gephi', 'report'
)
foreach ($folder in $folders) {
    New-Item -ItemType Directory -Force -Path (Join-Path $PSScriptRoot $folder) | Out-Null
}
Write-Host 'Assignment 1 folders are ready. Read README.md for Python setup.'
