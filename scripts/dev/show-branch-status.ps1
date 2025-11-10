# Show Branch Status - PowerShell Script
# Displays comprehensive branch information

$ErrorActionPreference = "Continue"

Write-Host "📊 Branch Status Report" -ForegroundColor Cyan
Write-Host "======================" -ForegroundColor Cyan

# Show current branch
$currentBranch = git rev-parse --abbrev-ref HEAD
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to get current branch."
    exit 1
}
Write-Host "`nCurrent Branch: $currentBranch" -ForegroundColor Green

# Check if main branch exists
Write-Host "`nChecking main branch..." -ForegroundColor Yellow
$mainExists = git show-ref --verify --quiet refs/heads/main
if ($LASTEXITCODE -ne 0) {
    Write-Warning "⚠️  Local main branch does not exist."
    Write-Host "Run sync-before-chat.ps1 to create it, or run:" -ForegroundColor Yellow
    Write-Host "  git checkout -b main origin/main" -ForegroundColor Gray
    Write-Host "`nShowing status without main branch reference..." -ForegroundColor Yellow

    # Show all local branches
    Write-Host "`n📋 LOCAL BRANCHES:" -ForegroundColor Cyan
    $allBranches = git branch | ForEach-Object { $_.Trim() }
    $allBranches | ForEach-Object {
        if ($_ -match '^\*') {
            Write-Host "  $_ (current)" -ForegroundColor Green
        } else {
            Write-Host "  $_" -ForegroundColor Gray
        }
    }

    # Show remote branch count
    $remoteBranches = (git branch -r | Measure-Object).Count
    Write-Host "`n📡 Remote branches: $remoteBranches" -ForegroundColor Cyan

    Write-Host "`n✅ Report complete!" -ForegroundColor Green
    exit 0
}

# Show merged branches
Write-Host "`n✅ MERGED TO MAIN (Safe to delete):" -ForegroundColor Green
$mergedBranches = git branch --merged main |
    Where-Object { $_ -notmatch '^\*' -and $_ -notmatch 'main' } |
    ForEach-Object { $_.Trim() }

if ($mergedBranches.Count -eq 0) {
    Write-Host "  (none)" -ForegroundColor Gray
} else {
    $mergedBranches | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }
}

# Show unmerged branches
Write-Host "`n🔄 NOT YET MERGED (May need PRs):" -ForegroundColor Yellow
$unmergedBranches = git branch --no-merged main |
    Where-Object { $_ -notmatch '^\*' -and $_ -notmatch 'main' } |
    ForEach-Object { $_.Trim() }

if ($unmergedBranches.Count -eq 0) {
    Write-Host "  (none)" -ForegroundColor Gray
} else {
    $unmergedBranches | ForEach-Object {
        # Get last commit date for each branch
        $lastCommit = git log -1 --format="%cr" $_
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  - $_ ($lastCommit)" -ForegroundColor Gray
        } else {
            Write-Host "  - $_" -ForegroundColor Gray
        }
    }
}

# Show uncommitted changes warning
$status = git status --porcelain
if ($status) {
    $changeCount = ($status | Measure-Object).Count
    Write-Host "`n⚠️  UNCOMMITTED CHANGES: $changeCount file(s)" -ForegroundColor Yellow
}

# Show remote branch count
$remoteBranches = (git branch -r | Measure-Object).Count
Write-Host "`n📡 Remote branches: $remoteBranches" -ForegroundColor Cyan

Write-Host "`n✅ Report complete!" -ForegroundColor Green
