# 🚀 Quick Start - GitHub Automation for Claude Code

## 🌟 THE ONLY TWO SCRIPTS YOU NEED

### ⭐ `claude-start.ps1`
**Run this at the START of every Claude Code session:**

```powershell
cd C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer
.\scripts\claude-start.ps1
```

**What it does:**
- ✅ Syncs with GitHub
- ✅ Updates main branch
- ✅ Cleans up old branches
- ✅ Shows you what's ready

---

### ⭐ `claude-end.ps1`
**Run this at the END of every Claude Code session:**

```powershell
.\scripts\claude-end.ps1
```

**What it does:**
- ✅ Commits all your changes
- ✅ Pushes to GitHub
- ✅ Creates Pull Request automatically
- ✅ Everything is backed up!

---

## 📋 Quick Reference Card

**Print this and stick it on your monitor:**

```
═══════════════════════════════════════
   CLAUDE CODE + GITHUB CHEAT SHEET
═══════════════════════════════════════

START SESSION:
  .\scripts\claude-start.ps1

END SESSION:
  .\scripts\claude-end.ps1

QUICK SAVE:
  .\scripts\claude-quick-commit.ps1

═══════════════════════════════════════
That's all you need to remember! 🚀
═══════════════════════════════════════
```

---

## 🔥 Bonus: Quick Save During Work

If you want to save progress **without ending your session:**

```powershell
.\scripts\claude-quick-commit.ps1
```

This commits and pushes your changes, then gets you right back to work!

---

## 🤖 What Happens Automatically

1. **You run**: `.\scripts\claude-end.ps1`
2. **Script does**: Commits, pushes, creates PR
3. **GitHub does**: Runs tests automatically
4. **If tests pass**: PR merges automatically ✅
5. **Done!** Your code is in main branch!

**Zero manual work after initial setup!**

---

## 🎯 Typical Workflow

```powershell
# Morning - Start session
.\scripts\claude-start.ps1

# Work all day with Claude Code
# ... coding ... coding ... coding ...

# Optional: Quick save during work
.\scripts\claude-quick-commit.ps1

# ... more coding ...

# Evening - End session
.\scripts\claude-end.ps1
```

**That's it!** Everything else is automatic! 🎉

---

## 🆕 For Your Next Project

Want to copy this automation to a new project?

```powershell
.\scripts\setup-new-project.ps1 -ProjectPath "C:\path\to\new\project"
```

Boom! New project has the same automation in 30 seconds! 🚀

---

## 🎓 What You Don't Need to Learn

You DON'T need to understand:

- ❌ Git commands
- ❌ Branches
- ❌ Commits
- ❌ Pull Requests
- ❌ Merging
- ❌ GitHub workflows

**The scripts handle ALL of it!** You just code. 🤠

---

## 📚 More Information

- **Complete Guide**: See [GITHUB_WORKFLOW_GUIDE.md](GITHUB_WORKFLOW_GUIDE.md)
- **Script Details**: See [scripts/README.md](scripts/README.md)
- **Help**: Having issues? Check the complete guide!

---

## 💡 Pro Tips

### Forgot to Run End Script?
No problem! Run it anytime:
```powershell
.\scripts\claude-end.ps1
```

### Forgot to Commit?
The end script will remind you!

### Something Broke?
Run `claude-start.ps1` to get back to a clean state!

### Custom Commit Message?
```powershell
.\scripts\claude-end.ps1 -Message "Add awesome new feature"
```

---

## ⚡ Even Faster

Add these to your PowerShell profile for **one-word commands**:

```powershell
function claude-start { .\scripts\claude-start.ps1 }
function claude-end { .\scripts\claude-end.ps1 }
function claude-save { .\scripts\claude-quick-commit.ps1 }
```

Then just type:
```
claude-start
claude-end
claude-save
```

---

## 🤠 Bottom Line

**Your job**: Run `claude-start.ps1` and `claude-end.ps1`

**My job**: Everything else! 🎉

Happy coding, partner! 🚀
