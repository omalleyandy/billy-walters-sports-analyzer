# Setup Script for Billy Walters MCP Server
# Run this in PowerShell from the project root

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Billy Walters MCP Server Setup" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to project directory
$projectDir = "C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer"
Set-Location $projectDir

Write-Host "Step 1: Installing package with MCP dependencies..." -ForegroundColor Yellow
uv pip install -e ".[mcp]"

if ($LASTEXITCODE -eq 0) {
    Write-Host "OK - Package installed successfully" -ForegroundColor Green
} else {
    Write-Host "ERROR - Package installation failed" -ForegroundColor Red
    Write-Host "Try manually: uv pip install -e '.[mcp]'" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Step 2: Verifying FastMCP installation..." -ForegroundColor Yellow
python -c "import fastmcp; print(f'FastMCP version: {fastmcp.__version__}')"

if ($LASTEXITCODE -eq 0) {
    Write-Host "OK - FastMCP verified" -ForegroundColor Green
} else {
    Write-Host "ERROR - FastMCP not found" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 3: Verifying walters_analyzer package..." -ForegroundColor Yellow
python -c "from walters_analyzer.core.analyzer import BillyWaltersAnalyzer; print('Package imports successfully')"

if ($LASTEXITCODE -eq 0) {
    Write-Host "OK - Package verified" -ForegroundColor Green
} else {
    Write-Host "ERROR - Package import failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Test the MCP server:"
Write-Host "   npx @modelcontextprotocol/inspector python .claude\walters_mcp_server.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Or use the provided test script:"
Write-Host "   .\test_mcp_server.ps1" -ForegroundColor Cyan
