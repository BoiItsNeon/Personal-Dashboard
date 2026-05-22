$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Streamlit = Join-Path $ProjectDir ".venv\Scripts\streamlit.exe"
$App = Join-Path $ProjectDir "app.py"

if (-not (Test-Path $Streamlit)) {
    Write-Error "Streamlit was not found at $Streamlit. Run dependency setup first."
    exit 1
}

Set-Location $ProjectDir
& $Streamlit run $App --server.port 8501 --server.headless true
