# Cleanup Merged Branches - PowerShell Script
# Safely deletes local branches that are already merged to main

Write-Host "🧹 Cleaning up merged branches..." -ForegroundColor Cyan

# Make sure we're on main
git checkout main

# Get list of merged branches (excluding main and current branch)
$mergedBranches = git branch --merged main |
    Where-Object { $_ -notmatch '^\*' -and $_ -notmatch 'main' } |
    ForEach-Object { $_.Trim() }

if ($mergedBranches.Count -eq 0) {
    Write-Host "`n✅ No merged branches to clean up!" -ForegroundColor Green
    exit 0
}

Write-Host "`nFound $($mergedBranches.Count) merged branch(es):" -ForegroundColor Yellow
$mergedBranches | ForEach-Object { Write-Host "  - $_" }

# Ask for confirmation
$response = Read-Host "`nDelete these branches? (y/n)"
if ($response -eq 'y' -or $response -eq 'Y') {
    foreach ($branch in $mergedBranches) {
        Write-Host "Deleting $branch..." -ForegroundColor Yellow
        git branch -d $branch
    }
    Write-Host "`n✅ Cleanup complete!" -ForegroundColor Green
} else {
    Write-Host "`n❌ Cleanup cancelled." -ForegroundColor Red
}
