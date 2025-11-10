# 📖 GitHub Workflow Guide for Claude Code
## Complete Beginner's Guide - No Git Knowledge Required!

---

## 🎯 What This Guide Covers

This guide explains the **complete automated GitHub workflow** for working with Claude Code. After this setup, you'll only need to run two commands - everything else is automatic!

**What you'll learn:**
- How the automation works
- What each script does
- How to use the workflow
- Troubleshooting common issues
- Advanced customization

---

## 🌟 Overview: The Two-Script Workflow

### The Big Picture

```
┌─────────────────────────────────────────────────────────┐
│  START OF DAY: claude-start.ps1                         │
│  ├─ Syncs with GitHub                                   │
│  ├─ Updates your main branch                            │
│  ├─ Cleans up old merged branches                       │
│  └─ Shows you current status                            │
└─────────────────────────────────────────────────────────┘
                         ⬇️
┌─────────────────────────────────────────────────────────┐
│  WORK: Use Claude Code all day                          │
│  └─ Optional: claude-quick-commit.ps1 for quick saves   │
└─────────────────────────────────────────────────────────┘
                         ⬇️
┌─────────────────────────────────────────────────────────┐
│  END OF DAY: claude-end.ps1                             │
│  ├─ Commits all your changes                            │
│  ├─ Pushes to GitHub                                    │
│  ├─ Creates Pull Request                                │
│  └─ Auto-merges when tests pass                         │
└─────────────────────────────────────────────────────────┘
```

---

## 📚 The Scripts Explained

### 1️⃣ `claude-start.ps1` - Start Your Session

**When to use**: At the START of every Claude Code session

**What it does**:
1. **Fetches latest changes** from GitHub
2. **Creates/updates main branch** if it doesn't exist locally
3. **Handles uncommitted changes** (offers to stash them)
4. **Cleans up merged branches** (asks for confirmation)
5. **Shows status report** so you know what's happening

**Example**:
```powershell
.\scripts\claude-start.ps1
```

**Output you'll see**:
```
╔═══════════════════════════════════════════════════════════╗
║         🚀 CLAUDE CODE SESSION - STARTING UP 🚀          ║
╚═══════════════════════════════════════════════════════════╝

STEP 1: Syncing with GitHub
✅ Fetched from origin
✅ Main branch updated

STEP 2: Cleaning up merged branches
Found 3 merged branches:
  - claude/old-feature-123
  - claude/another-feature-456
  - claude/fix-bug-789
Delete these branches? (y/n): y
✅ Cleanup complete!

STEP 3: Status Report
Current Branch: main
✅ MERGED TO MAIN (Safe to delete): (none)
🔄 NOT YET MERGED (May need PRs): (none)

╔═══════════════════════════════════════════════════════════╗
║              ✅ READY TO CODE WITH CLAUDE! ✅            ║
╚═══════════════════════════════════════════════════════════╝
```

---

### 2️⃣ `claude-end.ps1` - End Your Session

**When to use**: At the END of every Claude Code session

**What it does**:
1. **Checks current branch** (prevents committing to main)
2. **Detects changes** in your working directory
3. **Commits all changes** with a timestamp or custom message
4. **Pushes to GitHub** with retry logic (handles network issues)
5. **Creates Pull Request** automatically using GitHub CLI
6. **Enables auto-merge** (PR merges when tests pass)

**Example**:
```powershell
# With auto-generated message
.\scripts\claude-end.ps1

# With custom message
.\scripts\claude-end.ps1 -Message "Add new betting analysis feature"

# Just push, don't create PR
.\scripts\claude-end.ps1 -NoPR
```

**Output you'll see**:
```
╔═══════════════════════════════════════════════════════════╗
║         🏁 CLAUDE CODE SESSION - WRAPPING UP 🏁          ║
╚═══════════════════════════════════════════════════════════╝

STEP 1: Checking current branch
Current branch: claude/new-feature-XYZ123

STEP 2: Checking for changes
Found uncommitted changes:
  M  scripts/analyze.ps1
  A  tests/test_new_feature.py

STEP 3: Committing changes
Generated message: Update existing files
✅ Changes committed successfully!

STEP 4: Pushing to GitHub
Pushing to origin/claude/new-feature-XYZ123...
✅ Pushed to GitHub successfully!

STEP 5: Creating Pull Request
Creating PR with gh CLI...
✅ Pull Request created successfully!
🔗 PR URL: https://github.com/omalleyandy/billy-walters-sports-analyzer/pull/14

╔═══════════════════════════════════════════════════════════╗
║               🎉 SESSION COMPLETE! 🎉                    ║
╚═══════════════════════════════════════════════════════════╝

✅ Your changes are backed up to GitHub!
✅ Ready for code review and merging!
```

---

### 3️⃣ `claude-quick-commit.ps1` - Quick Save During Work

**When to use**: During your session when you want to save progress

**What it does**:
1. **Commits changes** with timestamp
2. **Pushes immediately** to GitHub
3. **Gets you back to work** ASAP!

**Example**:
```powershell
# Auto-generated message
.\scripts\claude-quick-commit.ps1

# Custom message
.\scripts\claude-quick-commit.ps1 -Message "WIP: testing new algorithm"
```

**Why use it?**
- Save progress without ending your session
- Backup your work to GitHub frequently
- Faster than running full claude-end.ps1

---

## 🔧 The Supporting Scripts

These scripts are used internally by `claude-start.ps1` but can also be run independently:

### `sync-before-chat.ps1`
Syncs your local repository with GitHub.

**Features**:
- Creates main branch if missing
- Handles uncommitted changes (stash option)
- Network retry logic (4 attempts with exponential backoff)
- Shows recent commits

### `cleanup-merged-branches.ps1`
Safely deletes branches that are already merged to main.

**Features**:
- Asks for confirmation before deleting
- Won't delete current or main branch
- Updates main before checking
- Reports success/failure counts

### `show-branch-status.ps1`
Displays comprehensive branch information.

**Features**:
- Shows current branch
- Lists merged branches (safe to delete)
- Lists unmerged branches (may need PRs)
- Shows uncommitted changes warning
- Works even if main branch doesn't exist

---

## 🤖 GitHub Actions Auto-Merge

### What Happens After You Create a PR

```
1. PR Created (by claude-end.ps1)
         ⬇️
2. CI Tests Run (pytest, etc.)
         ⬇️
3. Auto-merge Enabled
         ⬇️
4. ✅ All Tests Pass?
    YES ➡️ PR Merges Automatically
    NO  ➡️ Manual review needed
```

### The Workflow File

Location: `.github/workflows/auto-merge.yml`

**What it does**:
- Triggers on PRs from `claude/*` branches only
- Waits for CI tests to complete
- Enables auto-merge with squash commit
- Merges automatically when all checks pass

**Benefits**:
- Zero manual clicking in GitHub
- Only merges if tests pass
- Keeps commit history clean (squash merge)
- You get notified when merged

---

## 📖 Step-by-Step: Your First Session

### Initial Setup (One Time Only)

1. **Ensure PowerShell execution policy allows scripts**:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. **Install GitHub CLI** (optional but recommended for PR creation):
   ```powershell
   winget install --id GitHub.cli
   ```

3. **Authenticate GitHub CLI**:
   ```powershell
   gh auth login
   ```

### Daily Workflow

#### Morning: Start Session
```powershell
cd C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer
.\scripts\claude-start.ps1
```

**What happens**:
- Syncs with GitHub
- Cleans up old branches
- Shows status
- You're ready to code!

#### During Work: Code with Claude
Use Claude Code normally. Optionally save progress:
```powershell
.\scripts\claude-quick-commit.ps1
```

#### Evening: End Session
```powershell
.\scripts\claude-end.ps1
```

**What happens**:
- Commits all changes
- Pushes to GitHub
- Creates PR
- PR auto-merges when tests pass

#### Next Morning: Repeat!
```powershell
.\scripts\claude-start.ps1
```
- Gets latest changes (including yesterday's merged PR)
- Cleans up yesterday's branch
- Ready to go!

---

## 🔍 Understanding Branch Names

### The Pattern: `claude/<description>-<session-id>`

**Examples**:
- `claude/github-automation-scripts-011CUqm5iLJ9VtvT83iDjjSC`
- `claude/fix-powershell-syntax-errors-011CUpcuFEfXyePYhUVq9tiK`

**Why this matters**:
- **Security**: Branches must start with `claude/` for proper permissions
- **Auto-merge**: Only `claude/*` branches get auto-merged
- **Session tracking**: Session ID helps track which Claude session created what

**Claude Code creates these automatically** - you don't need to think about it!

---

## 🛠️ Troubleshooting

### "Execution of scripts is disabled"

**Problem**: PowerShell won't run scripts

**Solution**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### "gh: command not found"

**Problem**: GitHub CLI not installed

**Solutions**:
1. Install it:
   ```powershell
   winget install --id GitHub.cli
   ```
2. Or use `-NoPR` flag and create PRs manually:
   ```powershell
   .\scripts\claude-end.ps1 -NoPR
   ```

### "Failed to fetch from origin after multiple attempts"

**Problem**: Network issues

**What the script does**:
- Retries 4 times
- Waits 2, 4, 8, 16 seconds between retries

**If still failing**:
1. Check your internet connection
2. Check GitHub status: https://www.githubstatus.com/
3. Try again later

### "You have uncommitted changes"

**Problem**: Trying to sync/cleanup with unsaved work

**Solutions**:
1. **Recommended**: Let the script stash them (answer 'y')
2. Commit them first:
   ```powershell
   .\scripts\claude-quick-commit.ps1
   ```
3. Cancel and deal with them manually

### "Branch doesn't start with 'claude/'"

**Problem**: You're on a branch that doesn't match the naming convention

**Solution**: Usually this is fine, but if push fails:
```powershell
# Create a properly named branch
git checkout -b claude/your-feature-name-<session-id>
```

### "PR creation failed"

**Problem**: gh CLI couldn't create PR

**Solutions**:
1. Check gh authentication:
   ```powershell
   gh auth status
   ```
2. Create PR manually:
   - Go to your GitHub repo
   - Click "Compare & pull request"
   - Fill in details and create

---

## 🚀 Advanced Usage

### Skip Cleanup

If you're in a hurry and want to skip branch cleanup:
```powershell
.\scripts\claude-start.ps1 -SkipCleanup
```

### Custom Commit Messages

Always use descriptive messages for important commits:
```powershell
.\scripts\claude-end.ps1 -Message "Implement Billy Walters edge detection algorithm"
```

### Just Push, No PR

If you want to push but not create a PR yet:
```powershell
.\scripts\claude-end.ps1 -NoPR
```

### Check Status Anytime

```powershell
.\scripts\show-branch-status.ps1
```

### Manual Cleanup

```powershell
.\scripts\cleanup-merged-branches.ps1
```

---

## 📦 Copy to New Projects

### Use the Setup Script

```powershell
.\scripts\setup-new-project.ps1 -ProjectPath "C:\path\to\new\project" -GitHubRepo "https://github.com/yourusername/newrepo.git"
```

**What it copies**:
- All automation scripts
- GitHub Actions workflows
- Documentation (this file included!)

**What it does**:
- Creates scripts directory
- Copies workflows
- Initializes git (optional)
- Creates initial commit

### Manual Copy

If you prefer manual control:

1. Copy `scripts/` folder
2. Copy `.github/workflows/` folder
3. Copy documentation:
   - `QUICK_START.md`
   - `GITHUB_WORKFLOW_GUIDE.md`
   - `scripts/README.md`

---

## 💡 Best Practices

### Do's ✅

- ✅ Run `claude-start.ps1` every morning
- ✅ Run `claude-end.ps1` every evening
- ✅ Use `claude-quick-commit.ps1` to save progress
- ✅ Let scripts handle git operations
- ✅ Read the output - it tells you what's happening
- ✅ Use custom commit messages for important changes

### Don'ts ❌

- ❌ Don't commit directly to main branch
- ❌ Don't skip `claude-start.ps1` - you might miss updates
- ❌ Don't force push (let scripts handle retries)
- ❌ Don't manually merge PRs (let auto-merge do it)
- ❌ Don't delete branches manually (use cleanup script)

---

## 🎓 Git Concepts (Optional Reading)

You don't need to understand these, but if you're curious:

### Branches
Think of branches like parallel universes for your code. You work in one, merge it back to main when done.

### Commits
Snapshots of your code at a point in time. Like save points in a video game.

### Pull Requests (PRs)
A request to merge your branch into main. Allows for code review and automated testing.

### Merge
Combining changes from one branch into another.

### Squash Merge
Combines all commits from a branch into a single commit. Keeps history clean.

### Stash
Temporarily saves your changes without committing. Like a clipboard for code.

**The scripts handle all of this automatically!**

---

## 🤔 FAQ

### Q: What if I forget to run claude-end.ps1?

**A**: No problem! Run it anytime. It will commit and push all changes since your last commit.

### Q: Can I use regular git commands?

**A**: Yes, but the scripts handle everything you need. Using them ensures consistency and safety.

### Q: What if tests fail on my PR?

**A**: The PR won't auto-merge. Check the GitHub Actions tab to see what failed. Fix it, commit, and push again.

### Q: Can I work on multiple features at once?

**A**: Yes! Create different branches:
```powershell
git checkout -b claude/feature-1-XYZ123
# work on feature 1
git checkout -b claude/feature-2-ABC456
# work on feature 2
```

### Q: What if I want to undo changes?

**A**: Before committing:
```powershell
git restore <filename>  # Undo changes to specific file
git restore .           # Undo all changes
```

After committing but before pushing:
```powershell
git reset HEAD~1  # Undo last commit, keep changes
```

After pushing: Create a new PR with the fix!

### Q: How do I update the scripts?

**A**: Pull the latest changes:
```powershell
.\scripts\claude-start.ps1  # This syncs everything
```

Or manually:
```powershell
git checkout main
git pull origin main
```

---

## 🎉 Conclusion

You now have a **completely automated GitHub workflow**!

**What you do**:
- `claude-start.ps1` (morning)
- Work with Claude Code
- `claude-end.ps1` (evening)

**What happens automatically**:
- Syncing with GitHub
- Branch management
- Commits and pushes
- PR creation
- Auto-merging when tests pass

**No more**:
- Manual git commands
- Forgetting to commit
- Lost work
- Confusing merge conflicts
- Manual PR creation

---

## 📞 Need Help?

- **Quick Reference**: See [QUICK_START.md](QUICK_START.md)
- **Script Details**: See [scripts/README.md](scripts/README.md)
- **GitHub Issues**: Report problems at your repo's Issues tab

---

**Happy coding, partner! 🤠🚀**
