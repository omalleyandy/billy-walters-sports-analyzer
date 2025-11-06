# Setup New Project - Copy automation to a new project
# Use this to set up the same GitHub workflow automation in a new project
#
# Usage:
#   .\scripts\setup-new-project.ps1 -ProjectPath "C:\path\to\new\project"
#
# What it does:
#   1. Copies all automation scripts to the new project
#   2. Copies GitHub Actions workflows
#   3. Creates documentation
#   4. Initializes git if needed
#   5. You're ready to go!

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectPath,

    [string]$GitHubRepo = "",  # Optional: GitHub repo URL to set as origin

    [switch]$SkipGitInit  # Skip git initialization
)

$ErrorActionPreference = "Stop"

Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║       📦 SETTING UP NEW PROJECT WITH AUTOMATION 📦       ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

# Resolve paths
$ProjectPath = Resolve-Path -LiteralPath $ProjectPath -ErrorAction SilentlyContinue
if (-not $ProjectPath) {
    Write-Error "Project path does not exist: $ProjectPath"
    exit 1
}

$sourceDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourceRoot = Split-Path -Parent $sourceDir

Write-Host "`nSource: $sourceRoot" -ForegroundColor Gray
Write-Host "Target: $ProjectPath" -ForegroundColor Gray

# Step 1: Copy scripts directory
Write-Host "`n" + ("═" * 60) -ForegroundColor Cyan
Write-Host "STEP 1: Copying automation scripts" -ForegroundColor Cyan
Write-Host ("═" * 60) -ForegroundColor Cyan

$targetScriptsDir = Join-Path $ProjectPath "scripts"
if (-not (Test-Path $targetScriptsDir)) {
    New-Item -ItemType Directory -Path $targetScriptsDir | Out-Null
    Write-Host "Created scripts directory" -ForegroundColor Green
}

# Copy all PowerShell scripts
$scriptsToCopy = @(
    "claude-start.ps1",
    "claude-end.ps1",
    "claude-quick-commit.ps1",
    "sync-before-chat.ps1",
    "cleanup-merged-branches.ps1",
    "show-branch-status.ps1"
)

foreach ($script in $scriptsToCopy) {
    $sourcePath = Join-Path $sourceDir $script
    $targetPath = Join-Path $targetScriptsDir $script

    if (Test-Path $sourcePath) {
        Copy-Item -Path $sourcePath -Destination $targetPath -Force
        Write-Host "✅ Copied: $script" -ForegroundColor Green
    } else {
        Write-Warning "⚠️  Not found: $script"
    }
}

# Step 2: Copy GitHub Actions workflows
Write-Host "`n" + ("═" * 60) -ForegroundColor Cyan
Write-Host "STEP 2: Copying GitHub Actions workflows" -ForegroundColor Cyan
Write-Host ("═" * 60) -ForegroundColor Cyan

$sourceWorkflowsDir = Join-Path $sourceRoot ".github\workflows"
$targetWorkflowsDir = Join-Path $ProjectPath ".github\workflows"

if (Test-Path $sourceWorkflowsDir) {
    if (-not (Test-Path $targetWorkflowsDir)) {
        New-Item -ItemType Directory -Path $targetWorkflowsDir -Force | Out-Null
    }

    $workflowFiles = Get-ChildItem -Path $sourceWorkflowsDir -Filter "*.yml"
    foreach ($file in $workflowFiles) {
        $targetPath = Join-Path $targetWorkflowsDir $file.Name
        Copy-Item -Path $file.FullName -Destination $targetPath -Force
        Write-Host "✅ Copied workflow: $($file.Name)" -ForegroundColor Green
    }
} else {
    Write-Warning "⚠️  No workflows found to copy"
}

# Step 3: Copy documentation
Write-Host "`n" + ("═" * 60) -ForegroundColor Cyan
Write-Host "STEP 3: Copying documentation" -ForegroundColor Cyan
Write-Host ("═" * 60) -ForegroundColor Cyan

$docsToCopy = @(
    "scripts\README.md",
    "GITHUB_WORKFLOW_GUIDE.md",
    "QUICK_START.md"
)

foreach ($doc in $docsToCopy) {
    $sourcePath = Join-Path $sourceRoot $doc
    $targetPath = Join-Path $ProjectPath $doc

    if (Test-Path $sourcePath) {
        $targetDir = Split-Path -Parent $targetPath
        if (-not (Test-Path $targetDir)) {
            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        }
        Copy-Item -Path $sourcePath -Destination $targetPath -Force
        Write-Host "✅ Copied: $doc" -ForegroundColor Green
    }
}

# Step 4: Initialize git if requested
if (-not $SkipGitInit) {
    Write-Host "`n" + ("═" * 60) -ForegroundColor Cyan
    Write-Host "STEP 4: Initializing git" -ForegroundColor Cyan
    Write-Host ("═" * 60) -ForegroundColor Cyan

    Push-Location $ProjectPath
    try {
        $isGitRepo = Test-Path ".git"
        if (-not $isGitRepo) {
            Write-Host "Initializing git repository..." -ForegroundColor Yellow
            git init
            Write-Host "✅ Git initialized" -ForegroundColor Green

            if ($GitHubRepo) {
                Write-Host "Adding remote origin: $GitHubRepo" -ForegroundColor Yellow
                git remote add origin $GitHubRepo
                Write-Host "✅ Remote added" -ForegroundColor Green
            }

            # Create initial commit
            git add .
            git commit -m "Initial commit with GitHub automation"
            Write-Host "✅ Initial commit created" -ForegroundColor Green

            if ($GitHubRepo) {
                Write-Host "`nTo push to GitHub, run:" -ForegroundColor Yellow
                Write-Host "  git push -u origin main" -ForegroundColor Gray
            }
        } else {
            Write-Host "✅ Git already initialized" -ForegroundColor Green
        }
    } finally {
        Pop-Location
    }
}

# Final message
Write-Host "`n╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║            ✅ NEW PROJECT SETUP COMPLETE! ✅             ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Green

Write-Host "`n📋 Next steps:" -ForegroundColor Cyan
Write-Host "  1. cd $ProjectPath" -ForegroundColor Gray
Write-Host "  2. .\scripts\claude-start.ps1  # Start your first session" -ForegroundColor Gray
Write-Host "  3. Work with Claude Code" -ForegroundColor Gray
Write-Host "  4. .\scripts\claude-end.ps1    # Commit, push, create PR" -ForegroundColor Gray

Write-Host "`n📚 Documentation:" -ForegroundColor Cyan
Write-Host "  - QUICK_START.md - Quick reference" -ForegroundColor Gray
Write-Host "  - GITHUB_WORKFLOW_GUIDE.md - Complete guide" -ForegroundColor Gray
Write-Host "  - scripts\README.md - Script details" -ForegroundColor Gray

Write-Host "`n🎉 Happy coding!" -ForegroundColor Green
