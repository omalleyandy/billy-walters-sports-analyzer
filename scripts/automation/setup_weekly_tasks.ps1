# Windows Task Scheduler Setup for Billy Walters Weekly Workflow
#
# This script configures automated weekly tasks for:
# - NFL data collection and edge detection (Tuesday 2:00 PM)
# - NCAAF data collection and edge detection (Wednesday 2:00 PM)
# - Results checking and CLV tracking (Monday 3:00 PM)
#
# Requirements:
# - Run as Administrator
# - Python 3.11+ with uv installed
# - Project directory set up correctly
#
# Usage:
#   PS> Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope CurrentUser
#   PS> .\setup_weekly_tasks.ps1
#

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$ProjectRoot = "C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer",

    [Parameter(Mandatory=$false)]
    [string]$PythonExe = "C:\Users\omall\AppData\Local\Programs\Python\Python312\python.exe",

    [Parameter(Mandatory=$false)]
    [switch]$Remove
)

# Configuration
$TaskPrefix = "BillyWalters"
$Tasks = @(
    @{
        Name = "Weekly-NFL-Edges-Tuesday"
        Description = "Collect NFL data and detect betting edges (Tuesday 2 PM)"
        Day = "Tuesday"
        Time = "14:00:00"
        Script = "python scripts/analysis/edge_detector_production.py --nfl --full"
    },
    @{
        Name = "Weekly-NCAAF-Edges-Wednesday"
        Description = "Collect NCAAF data and detect betting edges (Wednesday 2 PM)"
        Day = "Wednesday"
        Time = "14:00:00"
        Script = "python scripts/analysis/edge_detector_production.py --ncaaf --full"
    },
    @{
        Name = "Weekly-CLV-Tracking-Monday"
        Description = "Check results from previous week and track CLV metrics (Monday 3 PM)"
        Day = "Monday"
        Time = "15:00:00"
        Script = "python scripts/analysis/check_betting_results.py --league nfl && python scripts/analysis/check_betting_results.py --league ncaaf"
    }
)

# Helper functions
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Create-TaskSchedulerTask {
    param(
        [string]$TaskName,
        [string]$Description,
        [string]$Day,
        [string]$Time,
        [string]$ProjectPath,
        [string]$PythonPath,
        [string]$Command
    )

    # Parse time
    $TimeParts = $Time -split ":"
    $Hour = [int]$TimeParts[0]
    $Minute = [int]$TimeParts[1]

    # Create trigger
    $Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $Day -At "$($Hour):$($Minute)"

    # Create action
    $Action = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -Command `"cd '$ProjectPath'; $Command`""

    # Create settings
    $Settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -MultipleInstances IgnoreNew `
        -RunOnlyIfNetworkAvailable

    # Register task
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Trigger $Trigger `
        -Action $Action `
        -Settings $Settings `
        -Description $Description `
        -Force `
        -ErrorAction Stop

    Write-Host "[OK] Task created: $TaskName" -ForegroundColor Green
}

function Remove-TaskSchedulerTask {
    param([string]$TaskName)

    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "[OK] Task removed: $TaskName" -ForegroundColor Green
    }
}

# Main execution
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Billy Walters Weekly Task Scheduler Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check admin privileges
if (-not (Test-Administrator)) {
    Write-Host "[ERROR] This script must be run as Administrator" -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator and try again." -ForegroundColor Yellow
    exit 1
}

# Validate project directory
if (-not (Test-Path $ProjectRoot)) {
    Write-Host "[ERROR] Project directory not found: $ProjectRoot" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Project directory: $ProjectRoot" -ForegroundColor Green

# Validate Python
if (-not (Test-Path $PythonExe)) {
    Write-Host "[WARNING] Python executable not found at $PythonExe" -ForegroundColor Yellow
    Write-Host "         Using system Python instead..."
}

Write-Host ""

# Remove existing tasks if requested
if ($Remove) {
    Write-Host "Removing existing tasks..." -ForegroundColor Yellow
    foreach ($Task in $Tasks) {
        $FullTaskName = "$TaskPrefix-$($Task.Name)"
        Remove-TaskSchedulerTask -TaskName $FullTaskName
    }
    Write-Host ""
    Write-Host "All tasks removed successfully!" -ForegroundColor Green
    exit 0
}

# Create tasks
Write-Host "Creating scheduled tasks..." -ForegroundColor Yellow
Write-Host ""

foreach ($Task in $Tasks) {
    $FullTaskName = "$TaskPrefix-$($Task.Name)"
    $Command = $Task.Script

    try {
        Create-TaskSchedulerTask `
            -TaskName $FullTaskName `
            -Description $Task.Description `
            -Day $Task.Day `
            -Time $Task.Time `
            -ProjectPath $ProjectRoot `
            -PythonPath $PythonExe `
            -Command $Command
    }
    catch {
        Write-Host "[ERROR] Failed to create task: $FullTaskName" -ForegroundColor Red
        Write-Host "        $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Task Scheduler Configuration Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Scheduled Tasks:"
Write-Host "  1. NFL Edges:        Tuesday 2:00 PM"
Write-Host "  2. NCAAF Edges:      Wednesday 2:00 PM"
Write-Host "  3. CLV Tracking:     Monday 3:00 PM"
Write-Host ""
Write-Host "View tasks:"
Write-Host "  PS> Get-ScheduledTask -TaskName 'BillyWalters-*'"
Write-Host ""
Write-Host "Trigger a task manually:"
Write-Host "  PS> Start-ScheduledTask -TaskName 'BillyWalters-Weekly-NFL-Edges-Tuesday'"
Write-Host ""
