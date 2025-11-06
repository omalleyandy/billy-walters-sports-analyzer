# Show Branch Status - PowerShell Script
# Displays comprehensive branch information

Write-Host "📊 Branch Status Report" -ForegroundColor Cyan
Write-Host "======================" -ForegroundColor Cyan

# Show current branch
$currentBranch = git rev-parse --abbrev-ref HEAD
Write-Host "`nCurrent Branch: $currentBranch" -ForegroundColor Green

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
        Write-Host "  - $_ ($lastCommit)" -ForegroundColor Gray
    }
}

# Show remote branch count
$remoteBranches = (git branch -r | Measure-Object).Count
Write-Host "`n📡 Remote branches: $remoteBranches" -ForegroundColor Cyan

Write-Host "`n✅ Report complete!" -ForegroundColor Green
