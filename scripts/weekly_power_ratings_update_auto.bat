@echo off
REM Weekly NFL Power Ratings Update Script (Windows) - AUTO WEEK DETECTION
REM
REM This script automatically determines the current NFL week and updates power ratings.
REM
REM Usage:
REM   scripts\weekly_power_ratings_update_auto.bat          # Auto-detect current week
REM   scripts\weekly_power_ratings_update_auto.bat 9 2024  # Manual week override
REM
REM Schedule with Windows Task Scheduler:
REM   - Trigger: Weekly, every Tuesday at 6:00 AM
REM   - Action: Start a program
REM   - Program: C:\path\to\weekly_power_ratings_update_auto.bat
REM   - No arguments needed (auto-detects)
REM

setlocal enabledelayedexpansion

REM Configuration
set SEASON=%2
if "%SEASON%"=="" set SEASON=2024

REM Auto-detect current week if not provided
set WEEK=%1
if "%WEEK%"=="" (
    echo Detecting current NFL week...

    REM Get current date (format: YYYY-MM-DD)
    for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
    set YEAR=!datetime:~0,4!
    set MONTH=!datetime:~4,2!
    set DAY=!datetime:~6,2!

    REM Simple week calculation based on date
    REM NFL Season 2024: Week 1 starts ~Sept 5, 2024
    REM This is a simplified calculation - adjust as needed

    if !MONTH! GEQ 09 (
        if !MONTH!==09 (
            if !DAY! LEQ 11 set WEEK=1
            if !DAY! GEQ 12 if !DAY! LEQ 18 set WEEK=2
            if !DAY! GEQ 19 if !DAY! LEQ 25 set WEEK=3
            if !DAY! GEQ 26 set WEEK=4
        )
        if !MONTH!==10 (
            if !DAY! LEQ 02 set WEEK=4
            if !DAY! GEQ 03 if !DAY! LEQ 09 set WEEK=5
            if !DAY! GEQ 10 if !DAY! LEQ 16 set WEEK=6
            if !DAY! GEQ 17 if !DAY! LEQ 23 set WEEK=7
            if !DAY! GEQ 24 if !DAY! LEQ 30 set WEEK=8
            if !DAY! GEQ 31 set WEEK=9
        )
        if !MONTH!==11 (
            if !DAY! LEQ 06 set WEEK=9
            if !DAY! GEQ 07 if !DAY! LEQ 13 set WEEK=10
            if !DAY! GEQ 14 if !DAY! LEQ 20 set WEEK=11
            if !DAY! GEQ 21 if !DAY! LEQ 27 set WEEK=12
            if !DAY! GEQ 28 set WEEK=13
        )
        if !MONTH!==12 (
            if !DAY! LEQ 04 set WEEK=13
            if !DAY! GEQ 05 if !DAY! LEQ 11 set WEEK=14
            if !DAY! GEQ 12 if !DAY! LEQ 18 set WEEK=15
            if !DAY! GEQ 19 if !DAY! LEQ 25 set WEEK=16
            if !DAY! GEQ 26 set WEEK=17
        )
    )

    REM Default to Week 9 if detection fails
    if "!WEEK!"=="" set WEEK=9

    echo Detected Week !WEEK! for !SEASON! season
)

REM Get script directory
set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..

echo ============================================
echo   Billy Walters Weekly Power Ratings Update
echo   Week: %WEEK%, Season: %SEASON%
echo   Auto-detected: %date% %time%
echo ============================================
echo.

REM Change to project directory
cd /d "%PROJECT_DIR%"

REM Run weekly update via CLI
echo Running weekly NFL update...
echo.

uv run walters-analyzer weekly-nfl-update --week %WEEK% --season %SEASON%

REM Check exit code
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================
    echo   [SUCCESS] Weekly update completed successfully!
    echo   Week %WEEK% ratings updated on %date% %time%
    echo ============================================

    REM Log success
    echo %date% %time% - Week %WEEK% - SUCCESS >> scripts\update_log.txt
    exit /b 0
) else (
    echo.
    echo ============================================
    echo   [ERROR] Weekly update failed!
    echo   Week %WEEK% failed on %date% %time%
    echo ============================================

    REM Log failure
    echo %date% %time% - Week %WEEK% - FAILED >> scripts\update_log.txt
    exit /b 1
)
