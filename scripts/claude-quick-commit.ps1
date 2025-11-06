# Claude Quick Commit - Fast save during work
# Use this to quickly save your progress without ending the session
#
# Usage:
#   .\scripts\claude-quick-commit.ps1
#   .\scripts\claude-quick-commit.ps1 -Message "WIP: adding new feature"
#
# What it does:
#   1. Commits all changes with a timestamp
#   2. Pushes to GitHub
#   3. Gets you back to work ASAP!

param(
    [string]$Message = ""  # Optional custom message
)

$ErrorActionPreference = "Continue"

Write-Host "⚡ Quick Commit - Saving progress..." -ForegroundColor Cyan

# Function to retry git push with exponential backoff
function Invoke-GitPushWithRetry {
    param(
        [string]$Branch,
        [int]$MaxRetries = 4
    )
    $delays = @(2, 4, 8, 16)
    for ($i = 0; $i -lt $MaxRetries; $i++) {
        Write-Host "Pushing to origin/$Branch..." -ForegroundColor Gray
        git push -u origin $Branch
        if ($LASTEXITCODE -eq 0) {
            return $true
        }
        if ($i -lt ($MaxRetries - 1)) {
            $delay = $delays[$i]
            Write-Warning "Push failed (attempt $($i + 1)/$MaxRetries). Retrying in $delay seconds..."
            Start-Sleep -Seconds $delay
        }
    }
    return $false
}

# Get current branch
$currentBranch = git rev-parse --abbrev-ref HEAD
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to get current branch."
    exit 1
}

# Don't allow commits on main
if ($currentBranch -eq "main") {
    Write-Error "Cannot commit directly to main branch!"
    exit 1
}

# Check for changes
$status = git status --porcelain
if (-not $status) {
    Write-Host "✅ No changes to commit." -ForegroundColor Green
    exit 0
}

# Show what's changed
Write-Host "Changes:" -ForegroundColor Yellow
git status --short

# Generate commit message
if ($Message) {
    $commitMessage = $Message
} else {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
    $commitMessage = "WIP: Quick save at $timestamp"
}

Write-Host "`nCommit message: $commitMessage" -ForegroundColor Green

# Stage and commit
git add -A
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to stage changes."
    exit 1
}

git commit -m $commitMessage
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to commit."
    exit 1
}

Write-Host "✅ Committed!" -ForegroundColor Green

# Push with retry
Write-Host "`nPushing to GitHub..." -ForegroundColor Yellow
if (-not (Invoke-GitPushWithRetry -Branch $currentBranch)) {
    Write-Error "Failed to push after multiple attempts."
    exit 1
}

Write-Host "`n✅ Quick commit complete! Keep coding!" -ForegroundColor Green
