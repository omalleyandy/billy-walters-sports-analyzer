@echo off
REM Billy Walters MCP Server - Simple Test (No Node.js required)
echo =====================================
echo Billy Walters Analyzer - Simple Test
echo =====================================
echo.

cd /d "C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer"

REM Check for virtual environment
if exist ".venv\Scripts\python.exe" (
    echo [OK] Found virtual environment
    set PYTHON=.venv\Scripts\python.exe
) else (
    echo [WARNING] No virtual environment found, using system Python
    set PYTHON=python
)

echo.
echo Testing Python...
%PYTHON% --version
if errorlevel 1 (
    echo [ERROR] Python not found
    pause
    exit /b 1
)

echo.
echo Running analyzer test...
echo.
%PYTHON% test_analyzer_simple.py
if errorlevel 1 (
    echo.
    echo [ERROR] Test failed. Check errors above.
    echo.
    echo Common fixes:
    echo   1. Install package: uv pip install -e .
    echo   2. Install dependencies: uv pip install -e ".[mcp]"
    echo.
) else (
    echo.
    echo [SUCCESS] Analyzer test passed!
    echo.
)

pause
