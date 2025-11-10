# Cleanup Merged Branches - PowerShell Script
# Safely deletes local branches that are already merged to main

$ErrorActionPreference = "Continue"

Write-Host "🧹 Cleaning up merged branches..." -ForegroundColor Cyan

# Check for uncommitted changes
Write-Host "`nChecking for uncommitted changes..." -ForegroundColor Yellow
$status = git status --porcelain
if ($status) {
    Write-Warning "⚠️  You have uncommitted changes. Please commit or stash them first."
    git status --short
    Write-Host "`n❌ Cleanup cancelled." -ForegroundColor Red
    exit 1
}

# Ensure main branch exists locally
Write-Host "`nEnsuring main branch exists..." -ForegroundColor Yellow
$mainExists = git show-ref --verify --quiet refs/heads/main
if ($LASTEXITCODE -ne 0) {
    Write-Host "Local main branch not found. Creating from origin/main..." -ForegroundColor Yellow
    git fetch origin main
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to fetch origin/main."
        exit 1
    }
    git checkout -b main origin/main
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create main branch from origin/main."
        exit 1
    }
    Write-Host "✅ Main branch created" -ForegroundColor Green
}

# Make sure we're on main
Write-Host "`nSwitching to main branch..." -ForegroundColor Yellow
git checkout main
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to checkout main branch."
    exit 1
}

# Update main to latest
Write-Host "Updating main branch..." -ForegroundColor Yellow
git pull origin main --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to update main branch. Continuing with local version..."
}

# Get list of merged branches (excluding main and current branch)
$mergedBranches = git branch --merged main |
    Where-Object { $_ -notmatch '^\*' -and $_ -notmatch 'main' } |
    ForEach-Object { $_.Trim() }

if ($mergedBranches.Count -eq 0) {
    Write-Host "`n✅ No merged branches to clean up!" -ForegroundColor Green
    exit 0
}

Write-Host "`nFound $($mergedBranches.Count) merged branch(es):" -ForegroundColor Yellow
$mergedBranches | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }

# Ask for confirmation
$response = Read-Host "`nDelete these branches? (y/n)"
if ($response -eq 'y' -or $response -eq 'Y') {
    $successCount = 0
    $failCount = 0
    foreach ($branch in $mergedBranches) {
        Write-Host "Deleting $branch..." -ForegroundColor Yellow
        git branch -d $branch
        if ($LASTEXITCODE -eq 0) {
            $successCount++
        } else {
            $failCount++
            Write-Warning "Failed to delete $branch"
        }
    }
    Write-Host "`n✅ Cleanup complete! Deleted: $successCount, Failed: $failCount" -ForegroundColor Green
} else {
    Write-Host "`n❌ Cleanup cancelled." -ForegroundColor Red
}
