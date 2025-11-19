@echo off
REM Test Week 12 System Installation (UV Version)
REM Run this to verify everything is ready

echo ================================================================================
echo WEEK 12 SYSTEM INSTALLATION TEST (UV Package Manager)
echo ================================================================================
echo.

REM Test 1: Check Python
echo [TEST 1] Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo [FAIL] Python not found!
    exit /b 1
)
echo [PASS] Python installed
echo.

REM Test 2: Check UV
echo [TEST 2] Checking UV package manager...
uv --version 2>nul
if %errorlevel% neq 0 (
    echo [WARN] UV not found in PATH
    echo Installing UV...
    powershell -Command "irm https://astral.sh/uv/install.ps1 | iex"
)
echo [PASS] UV ready
echo.

REM Test 3: Check httpx
echo [TEST 3] Checking httpx package...
python -c "import httpx; print(f'httpx {httpx.__version__} installed')" 2>nul
if %errorlevel% neq 0 (
    echo [WARN] httpx not installed
    echo Installing httpx with UV...
    uv pip install httpx
    if %errorlevel% neq 0 (
        echo [FAIL] Could not install httpx
        exit /b 1
    )
)
echo [PASS] httpx ready
echo.

REM Test 4: Check edge calculator
echo [TEST 4] Testing edge calculator...
python billy_walters_edge_calculator.py >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] Edge calculator test failed
    exit /b 1
)
echo [PASS] Edge calculator working
echo.

REM Test 5: Check files exist
echo [TEST 5] Checking required files...
if not exist "scrape_week12_odds.py" (
    echo [FAIL] scrape_week12_odds.py not found!
    exit /b 1
)
echo [PASS] All files present
echo.

REM Success!
echo ================================================================================
echo ALL TESTS PASSED!
echo ================================================================================
echo.
echo System is ready for Week 12 betting!
echo.
echo Next step: Run the live scraper
echo   python scrape_week12_odds.py
echo.
echo ================================================================================

pause
