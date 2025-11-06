# Branch Management Scripts

These PowerShell scripts help automate branch management and keep your repo in sync.

## Scripts

### 1. `sync-before-chat.ps1`
**Run before starting a new Claude Code session**
```powershell
.\scripts\sync-before-chat.ps1
```

What it does:
- Fetches latest changes from GitHub
- Updates your main branch
- Shows current status and recent commits

---

### 2. `cleanup-merged-branches.ps1`
**Clean up branches that are already merged to main**
```powershell
.\scripts\cleanup-merged-branches.ps1
```

What it does:
- Identifies branches merged to main
- Asks for confirmation before deleting
- Safely removes merged branches

---

### 3. `show-branch-status.ps1`
**Get a comprehensive branch status report**
```powershell
.\scripts\show-branch-status.ps1
```

What it does:
- Shows which branches are merged (safe to delete)
- Shows which branches are unmerged (may need PRs)
- Displays branch ages and counts

---

## Quick Commands for PowerShell

### Clean up merged branches manually
```powershell
# Get list of merged branches (excluding main)
git branch --merged main | Where-Object { $_ -notmatch '^\*' -and $_ -notmatch 'main' } | ForEach-Object { $_.Trim() }

# Delete a specific branch
git branch -d branch-name

# Delete multiple branches at once
git branch --merged main | Where-Object { $_ -notmatch '^\*' -and $_ -notmatch 'main' } | ForEach-Object { git branch -d $_.Trim() }
```

### Check branch status
```powershell
# See merged branches
git branch --merged main

# See unmerged branches
git branch --no-merged main

# See all local branches
git branch

# See all remote branches
git branch -r
```

### Typical workflow
```powershell
# Before starting work
.\scripts\sync-before-chat.ps1

# During work - create a new branch for your task
git checkout -b claude/your-feature-name

# After PR is merged
.\scripts\cleanup-merged-branches.ps1

# Check status anytime
.\scripts\show-branch-status.ps1
```

## Troubleshooting

### "Execution of scripts is disabled"
If you get this error, run PowerShell as Administrator and execute:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Scripts not found
Make sure you're in the project root directory:
```powershell
cd C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer
```
