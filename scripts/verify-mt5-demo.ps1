[CmdletBinding()]
param(
    [string]$BaseUrl = $env:SMART_SIGNALS_API_URL,
    [string]$ApiToken = $env:SMART_SIGNALS_API_TOKEN,
    [string]$Symbol = "EURUSD",
    [ValidateSet("M5", "M15")]
    [string]$Timeframe = "M5"
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($BaseUrl)) {
    throw "Set SMART_SIGNALS_API_URL to the HTTPS API origin, for example https://signals.example.com."
}
if ([string]::IsNullOrWhiteSpace($ApiToken)) {
    throw "Set SMART_SIGNALS_API_TOKEN to the backend bearer token."
}
if ($BaseUrl -notmatch '^https://') {
    throw "The demo verification script requires an HTTPS API URL."
}
$BaseUrl = $BaseUrl.TrimEnd('/')
$headers = @{ Authorization = "Bearer $ApiToken" }

function Invoke-ApiGet([string]$Path) {
    Invoke-RestMethod -Method Get -Uri "$BaseUrl$Path" -Headers $headers -TimeoutSec 20
}

Write-Host "Checking public API health..."
$health = Invoke-ApiGet "/health"
if ($health.status -ne "ok") { throw "API health check failed." }

Write-Host "Checking authenticated MT5 terminal connection..."
$terminal = Invoke-ApiGet "/api/v1/terminal"
if ($terminal.status -ne "connected" -or -not $terminal.available) {
    throw "MT5 is not connected/available. Open the Windows MT5 terminal, sign in to the demo account, and rerun this check."
}

Write-Host "Checking symbol $Symbol..."
$symbols = Invoke-ApiGet "/api/v1/symbols"
$symbolMatch = @($symbols.items | Where-Object { $_.name -eq $Symbol } | Select-Object -First 1)
if ($symbolMatch.Count -eq 0) {
    throw "Symbol $Symbol is not available in MT5. Confirm the broker's exact symbol name (including suffix) and rerun with -Symbol."
}

$encodedSymbol = [uri]::EscapeDataString($Symbol)
Write-Host "Checking recent closed $Timeframe candles..."
$candles = Invoke-ApiGet "/api/v1/candles?symbol=$encodedSymbol&timeframe=$Timeframe&limit=60"
if ($candles.count -lt 50 -or $candles.timezone -ne "UTC") {
    throw "Closed-candle check failed: expected at least 50 candles and UTC timestamps; received $($candles.count)."
}

Write-Host "Checking indicators and read-only signal endpoint..."
$indicators = Invoke-ApiGet "/api/v1/indicators?symbol=$encodedSymbol&timeframe=$Timeframe&limit=100"
if ($null -eq $indicators.values.ema_fast -or $null -eq $indicators.values.ema_slow -or
    $null -eq $indicators.values.rsi -or $null -eq $indicators.values.atr) {
    throw "Indicator check failed: one or more values are missing."
}
$signal = Invoke-ApiGet "/api/v1/signals?symbol=$encodedSymbol&timeframe=$Timeframe"
if ($signal.direction -notin @("BUY", "SELL", "NO_SIGNAL") -or -not $signal.data_valid) {
    throw "Signal endpoint did not return valid market analysis."
}

Write-Host "PASS: API, authenticated MT5 demo connection, $Symbol, closed candles, indicators, and signal endpoint are working."
Write-Host "Signal direction: $($signal.direction); last closed candle: $($signal.last_closed_candle_time)."
Write-Host "This check only reads market data and generates analysis; it does not submit or modify orders."
