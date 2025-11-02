@echo off
REM Weekly NFL Power Ratings Update Script (Windows)
REM
REM This script automates the Billy Walters power ratings weekly update cycle:
REM 1. Scrape latest week's NFL games from ESPN API
REM 2. Update power ratings from game results
REM 3. Display top-rated teams
REM
REM Usage:
REM   scripts\weekly_power_ratings_update.bat 9        # Update for Week 9
REM   scripts\weekly_power_ratings_update.bat 9 2024  # Specific season
REM
REM Schedule with Windows Task Scheduler:
REM   - Trigger: Weekly, every Tuesday at 6:00 AM
REM   - Action: Start a program
REM   - Program: C:\path\to\billy-walters-sports-analyzer\scripts\weekly_power_ratings_update.bat
REM   - Arguments: 9 (or current week number)
REM

setlocal enabledelayedexpansion

REM Configuration
set WEEK=%1
set SEASON=%2

REM Default values
if "%WEEK%"=="" set WEEK=9
if "%SEASON%"=="" set SEASON=2025

REM Get script directory
set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..

echo ============================================
echo   Billy Walters Weekly Power Ratings Update
echo   Week: %WEEK%, Season: %SEASON%
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
    echo ============================================
    exit /b 0
) else (
    echo.
    echo ============================================
    echo   [ERROR] Weekly update failed!
    echo ============================================
    exit /b 1
)
