# Remove old Task Scheduler tasks
$TaskNames = @(
    "BillyWalters-Weekly-NFL-Edges-Tuesday",
    "BillyWalters-Weekly-NCAAF-Edges-Wednesday",
    "BillyWalters-Weekly-CLV-Tracking-Monday"
)

foreach ($TaskName in $TaskNames) {
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop
        Write-Host "[OK] Removed: $TaskName" -ForegroundColor Green
    }
    catch {
        Write-Host "[INFO] Task not found: $TaskName" -ForegroundColor Yellow
    }
}

Write-Host "`nCleanup complete!" -ForegroundColor Green
