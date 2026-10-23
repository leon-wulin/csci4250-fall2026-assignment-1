# Build Assignment 1 PDF from the LaTeX sources on Windows.
# Requirement: a LaTeX distribution such as MiKTeX with pdflatex available in PATH.
[CmdletBinding()]
param([string]$PdfLatexPath = 'pdflatex')

$ErrorActionPreference = 'Stop'
$texRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $texRoot
try {
    $compiler = Get-Command $PdfLatexPath -CommandType Application -ErrorAction SilentlyContinue
    if (-not $compiler) {
        throw 'pdflatex not found. Reopen a MiKTeX-enabled terminal or pass -PdfLatexPath with a verified executable path.'
    }
    $compilerPath = $compiler.Source
    $compilerArguments = @('-disable-installer', '-disable-write18', '-interaction=nonstopmode', '-halt-on-error', '-file-line-error', '-output-directory=build', 'main.tex')
    New-Item -ItemType Directory -Path 'build' -Force | Out-Null
    for ($i = 1; $i -le 2; $i++) {
        # Keep the executable separate from arguments, including paths with spaces.
        $latexProcess = Start-Process -FilePath $compilerPath -WorkingDirectory $texRoot -ArgumentList $compilerArguments -WindowStyle Hidden -Wait -PassThru
        if ($latexProcess.ExitCode -ne 0) {
            throw "LaTeX compilation failed on pass $i. See build/main.log."
        }
        Write-Host "LaTeX pass $i succeeded."
    }
    Copy-Item -Path 'build/main.pdf' -Destination 'report.pdf' -Force
    Write-Host "Built: $texRoot\report.pdf"
}
finally {
    Pop-Location
}
