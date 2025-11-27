@echo off
echo =====================================
echo Billy Walters MCP Server - Quick Test
echo =====================================
echo.

cd /d "C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer"

echo Step 1: Testing Python imports...
python -c "import sys; print('Python:', sys.version)"
if errorlevel 1 (
    echo [ERROR] Python not found
    pause
    exit /b 1
)
echo [OK] Python available
echo.

echo Step 2: Testing FastMCP...
python -c "import fastmcp; print('FastMCP version:', fastmcp.__version__)" 2>nul
if errorlevel 1 (
    echo [WARNING] FastMCP not installed
    echo Installing FastMCP...
    uv pip install fastmcp
) else (
    echo [OK] FastMCP installed
)
echo.

echo Step 3: Testing walters_analyzer package...
python -c "import sys; sys.path.insert(0, 'src'); from walters_analyzer.core.analyzer import BillyWaltersAnalyzer; print('[OK] Package imports successfully')" 2>nul
if errorlevel 1 (
    echo [WARNING] Package not installed
    echo Installing package...
    uv pip install -e ".[mcp]"
) else (
    echo [OK] Package available
)
echo.

echo Step 4: Starting MCP Inspector...
echo.
echo The Inspector will open in your browser.
echo Press Ctrl+C to stop the server.
echo.
echo Server location: .claude\walters_mcp_server.py
echo.
pause
npx @modelcontextprotocol/inspector python .claude\walters_mcp_server.py

echo.
echo =====================================
echo Inspector stopped.
echo =====================================
pause
