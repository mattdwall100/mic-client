$clientRoot = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = Join-Path $clientRoot "src"

Push-Location $clientRoot
try {
    python -m windows_mic_client.main
}
finally {
    Pop-Location
}
