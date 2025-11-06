# Sync Before Chat - PowerShell Script
# Run this before starting a new Claude Code chat session

$ErrorActionPreference = "Continue"

Write-Host "🔄 Syncing with GitHub..." -ForegroundColor Cyan

# Function to retry git operations with exponential backoff
function Invoke-GitWithRetry {
    param(
        [string]$Command,
        [int]$MaxRetries = 4
    )
    $delays = @(2, 4, 8, 16)
    for ($i = 0; $i -lt $MaxRetries; $i++) {
        Write-Host "Executing: git $Command" -ForegroundColor Gray
        Invoke-Expression "git $Command"
        if ($LASTEXITCODE -eq 0) {
            return $true
        }
        if ($i -lt ($MaxRetries - 1)) {
            $delay = $delays[$i]
            Write-Warning "Command failed (attempt $($i + 1)/$MaxRetries). Retrying in $delay seconds..."
            Start-Sleep -Seconds $delay
        }
    }
    return $false
}

# Check for uncommitted changes
Write-Host "`nChecking for uncommitted changes..." -ForegroundColor Yellow
$status = git status --porcelain
if ($status) {
    Write-Warning "⚠️  You have uncommitted changes:"
    git status --short
    $response = Read-Host "`nStash changes and continue? (y/n)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        Write-Host "Stashing changes..." -ForegroundColor Yellow
        git stash push -m "Auto-stash before sync-before-chat $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to stash changes. Aborting."
            exit 1
        }
        Write-Host "✅ Changes stashed successfully" -ForegroundColor Green
    } else {
        Write-Host "`n❌ Sync cancelled. Please commit or stash your changes first." -ForegroundColor Red
        exit 1
    }
}

# Fetch latest changes and prune deleted branches with retry
Write-Host "`nFetching from origin and pruning..." -ForegroundColor Yellow
if (-not (Invoke-GitWithRetry "fetch origin --prune")) {
    Write-Error "Failed to fetch from origin after multiple attempts."
    exit 1
}

# Ensure main branch exists locally
Write-Host "`nEnsuring main branch exists..." -ForegroundColor Yellow
$mainExists = git show-ref --verify --quiet refs/heads/main
if ($LASTEXITCODE -ne 0) {
    Write-Host "Local main branch not found. Creating from origin/main..." -ForegroundColor Yellow
    git checkout -b main origin/main
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create main branch from origin/main."
        exit 1
    }
    Write-Host "✅ Main branch created" -ForegroundColor Green
}

# Switch to main and pull latest with retry
Write-Host "`nSwitching to main branch..." -ForegroundColor Yellow
git checkout main
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to checkout main branch."
    exit 1
}

Write-Host "Pulling latest changes..." -ForegroundColor Yellow
if (-not (Invoke-GitWithRetry "pull origin main")) {
    Write-Error "Failed to pull from origin/main after multiple attempts."
    exit 1
}

# Show current status
Write-Host "`n✅ Sync complete! Current status:" -ForegroundColor Green
git status

# Show recent commits
Write-Host "`nRecent commits:" -ForegroundColor Yellow
git log --oneline -5

Write-Host "`n✅ Ready to work!" -ForegroundColor Green
