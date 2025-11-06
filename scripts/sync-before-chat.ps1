# Sync Before Chat - PowerShell Script
# Run this before starting a new Claude Code chat session

Write-Host "🔄 Syncing with GitHub..." -ForegroundColor Cyan

# Fetch latest changes and prune deleted branches
Write-Host "`nFetching from origin and pruning..." -ForegroundColor Yellow
git fetch origin --prune

# Switch to main and pull latest
Write-Host "`nUpdating main branch..." -ForegroundColor Yellow
git checkout main
git pull origin main

# Show current status
Write-Host "`n✅ Sync complete! Current status:" -ForegroundColor Green
git status

# Show recent commits
Write-Host "`nRecent commits:" -ForegroundColor Yellow
git log --oneline -5

Write-Host "`n✅ Ready to work!" -ForegroundColor Green
