# GitHub Automation Scripts for Claude Code

Complete automation for GitHub workflows with Claude Code. Two main scripts handle everything!

## 🌟 Main Scripts (Start Here!)

### ⭐ `claude-start.ps1`
**Run at the START of every Claude Code session**
```powershell
.\scripts\claude-start.ps1
```

What it does:
- Syncs with GitHub (calls sync-before-chat.ps1)
- Cleans up merged branches (calls cleanup-merged-branches.ps1)
- Shows status report (calls show-branch-status.ps1)
- Gets you ready to work!

**Options**:
```powershell
# Skip cleanup step for faster startup
.\scripts\claude-start.ps1 -SkipCleanup
```

---

### ⭐ `claude-end.ps1`
**Run at the END of every Claude Code session**
```powershell
.\scripts\claude-end.ps1
```

What it does:
- Commits all changes (with auto-generated or custom message)
- Pushes to GitHub (with retry logic)
- Creates Pull Request automatically
- Enables auto-merge when tests pass

**Options**:
```powershell
# Custom commit message
.\scripts\claude-end.ps1 -Message "Add new feature"

# Skip PR creation (just commit and push)
.\scripts\claude-end.ps1 -NoPR
```

---

### ⚡ `claude-quick-commit.ps1`
**Quick save during work - no session end required**
```powershell
.\scripts\claude-quick-commit.ps1
```

What it does:
- Commits all changes with timestamp
- Pushes to GitHub immediately
- Gets you back to work ASAP!

**Options**:
```powershell
# Custom message
.\scripts\claude-quick-commit.ps1 -Message "WIP: testing algorithm"
```

---

## 🔧 Supporting Scripts

These scripts are called by the main scripts but can also be run independently:

### 1. `sync-before-chat.ps1`
**Sync your local repository with GitHub**
```powershell
.\scripts\sync-before-chat.ps1
```

What it does:
- Fetches latest changes from GitHub with retry logic
- Creates main branch if it doesn't exist locally
- Handles uncommitted changes (offers to stash)
- Updates main branch to latest
- Shows current status and recent commits

**Features**:
- Network retry logic (4 attempts with exponential backoff)
- Safe handling of uncommitted work
- Creates missing main branch automatically

---

### 2. `cleanup-merged-branches.ps1`
**Clean up branches that are already merged to main**
```powershell
.\scripts\cleanup-merged-branches.ps1
```

What it does:
- Checks for uncommitted changes first
- Ensures main branch exists
- Identifies branches merged to main
- Asks for confirmation before deleting
- Safely removes merged branches
- Reports success/failure counts

**Features**:
- Safe deletion (only merged branches)
- Confirmation prompt
- Won't delete main or current branch

---

### 3. `show-branch-status.ps1`
**Get a comprehensive branch status report**
```powershell
.\scripts\show-branch-status.ps1
```

What it does:
- Shows current branch
- Lists merged branches (safe to delete)
- Lists unmerged branches (may need PRs)
- Shows uncommitted changes warning
- Displays remote branch count
- Works even if main branch doesn't exist

**Features**:
- Color-coded output for easy reading
- Handles missing main branch gracefully
- Shows last commit dates for unmerged branches

---

## 📦 Project Setup

### `setup-new-project.ps1`
**Copy this automation to a new project**
```powershell
.\scripts\setup-new-project.ps1 -ProjectPath "C:\path\to\new\project"
```

What it does:
- Copies all automation scripts to new project
- Copies GitHub Actions workflows
- Copies documentation (QUICK_START.md, GITHUB_WORKFLOW_GUIDE.md)
- Initializes git if needed
- Sets up remote origin (optional)

**Options**:
```powershell
# With GitHub repo URL
.\scripts\setup-new-project.ps1 -ProjectPath "C:\path\to\new\project" -GitHubRepo "https://github.com/user/repo.git"

# Skip git initialization
.\scripts\setup-new-project.ps1 -ProjectPath "C:\path\to\new\project" -SkipGitInit
```

**Result**: New project ready with same automation in 30 seconds!

---

## 🛠️ Utility Scripts

These scripts help with specific tasks (not part of main workflow):

### `wsl-clean-venv.ps1`
**Clean virtual environment using WSL-safe methods**
```powershell
.\scripts\wsl-clean-venv.ps1 -RepoPath "." -Recreate
```

What it does:
- Stops Python/uv processes
- Removes .venv using WSL if available (handles long paths)
- Falls back to Windows removal
- Optionally recreates venv with uv sync

---

### `repair-venv.ps1`
**Repair virtual environment and test with card dry-run**
```powershell
.\scripts\repair-venv.ps1 -RepoPath "."
```

What it does:
- Calls wsl-clean-venv.ps1 with -Recreate
- Picks newest card file from ./cards
- Runs dry-run to verify environment works
- Confirms health of venv

---

## 🎯 Quick Reference

### Daily Workflow
```powershell
# Morning
.\scripts\claude-start.ps1

# During work (optional quick saves)
.\scripts\claude-quick-commit.ps1

# Evening
.\scripts\claude-end.ps1
```

### That's It!
Everything else is automatic! 🎉

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

---

## 📚 Documentation

For more detailed information, see:

- **[QUICK_START.md](../QUICK_START.md)** - Two-command cheat sheet (print and stick on monitor!)
- **[GITHUB_WORKFLOW_GUIDE.md](../GITHUB_WORKFLOW_GUIDE.md)** - Complete beginner's guide (no Git knowledge required)
- **GitHub Actions** - See `.github/workflows/auto-merge.yml` for auto-merge configuration

---

## 🔧 Troubleshooting

### "Execution of scripts is disabled"
**Problem**: PowerShell won't run scripts

**Solution**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### "gh: command not found"
**Problem**: GitHub CLI not installed (needed for PR creation)

**Solutions**:
1. Install GitHub CLI:
   ```powershell
   winget install --id GitHub.cli
   ```
2. Or use `-NoPR` flag to skip PR creation:
   ```powershell
   .\scripts\claude-end.ps1 -NoPR
   ```

### "Failed to fetch from origin"
**Problem**: Network issues

**What the script does**: Automatically retries 4 times with delays (2s, 4s, 8s, 16s)

**If still failing**: Check internet connection or GitHub status

### "You have uncommitted changes"
**Problem**: Trying to sync with unsaved work

**Solutions**:
1. Let the script stash them (answer 'y')
2. Commit them first: `.\scripts\claude-quick-commit.ps1`
3. Cancel and deal with manually

### Scripts not found
**Problem**: Running from wrong directory

**Solution**: Make sure you're in the project root:
```powershell
cd C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer
```

---

## 🎉 Summary

**Two scripts is all you need**:
1. `claude-start.ps1` - Morning
2. `claude-end.ps1` - Evening

**Everything else is automatic**! 🚀

For questions or issues, see [GITHUB_WORKFLOW_GUIDE.md](../GITHUB_WORKFLOW_GUIDE.md)
