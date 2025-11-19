# MCP Inspector Test Script for Billy Walters Sports Analyzer
# This script helps diagnose and test your MCP server

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "MCP Inspector - Billy Walters Server" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

$projectDir = "C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer"
$serverPath = ".claude\walters_mcp_server.py"

Set-Location $projectDir

Write-Host "Testing MCP Server..." -ForegroundColor Yellow
Write-Host "Server path: $serverPath" -ForegroundColor Gray
Write-Host ""

# Check if npx is available
Write-Host "Checking npx availability..." -ForegroundColor Yellow
$npxVersion = npx --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "OK - npx version: $npxVersion" -ForegroundColor Green
} else {
    Write-Host "ERROR - npx not found. Please install Node.js" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Checking Python availability..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "OK - $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "ERROR - Python not found" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Checking server file..." -ForegroundColor Yellow
if (Test-Path $serverPath) {
    Write-Host "OK - Server file found" -ForegroundColor Green
} else {
    Write-Host "ERROR - Server file not found at $serverPath" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Starting MCP Inspector..." -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "The Inspector will open in your browser." -ForegroundColor Yellow
Write-Host "Test these features:" -ForegroundColor Yellow
Write-Host "  1. Tools tab - analyze_game, calculate_kelly_stake, get_injury_report" -ForegroundColor Cyan
Write-Host "  2. Resources tab - walters://betting-history, walters://system-config" -ForegroundColor Cyan
Write-Host "  3. Check for connection errors in the Notifications pane" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the inspector" -ForegroundColor Gray
Write-Host ""

# Run the inspector
npx @modelcontextprotocol/inspector python $serverPath

Write-Host ""
Write-Host "Inspector stopped." -ForegroundColor Yellow
