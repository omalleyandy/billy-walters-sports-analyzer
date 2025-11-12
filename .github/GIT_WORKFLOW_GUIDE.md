# Git Workflow Guide - Billy Walters Sports Analyzer

## Quick Start: Daily Git Workflow

### 🌅 Start of Session (ALWAYS DO THIS FIRST)

```bash
# Sync with GitHub to get latest changes
git pull origin main --rebase
```

**Why?** Prevents merge conflicts by getting latest code before you start working.

### 💻 During Development

#### Frequent Small Commits (Every 30-60 minutes)

```bash
# Check what changed
git status

# Stage all changes
git add .

# Commit with descriptive message
git commit -m "type(scope): brief description"

# Push to GitHub
git push origin main
```

#### Commit Message Format

Use **Conventional Commits** for consistency:

```
type(scope): brief description (50 chars max)

Detailed explanation if needed (72 chars per line).

- Key change 1
- Key change 2

Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation only
- `refactor` - Code restructuring (no functionality change)
- `test` - Adding/updating tests
- `chore` - Maintenance (dependencies, configs)
- `style` - Formatting only (no code change)

**Examples:**
```bash
git commit -m "feat(scraper): add retry logic to Overtime API client"
git commit -m "fix(weather): correct AccuWeather HTTPS endpoint"
git commit -m "docs: update CLAUDE.md with new script paths"
git commit -m "refactor(tests): move integration tests to tests/ directory"
git commit -m "chore(deps): update httpx to 0.27.0"
```

### 🌙 End of Session

#### Option A: Let Claude Handle It (Recommended)

Just say: **"Claude, commit and push my changes"**

Claude will:
1. Review all changes
2. Write a comprehensive commit message
3. Commit and push to GitHub
4. Handle any conflicts

#### Option B: Manual Commit

```bash
# Check everything changed today
git status
git diff

# Stage and commit
git add -A
git commit -m "work-in-progress: session summary

- Completed feature X
- Fixed bug Y
- Updated documentation Z

Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to GitHub
git push origin main
```

## 🔧 Helpful Git Aliases

Add these to your Git config for faster workflow:

```bash
# Set up aliases (run once)
git config --global alias.st "status --short"
git config --global alias.co "checkout"
git config --global alias.br "branch"
git config --global alias.last "log -1 HEAD --stat"
git config --global alias.sync "!git pull origin main --rebase && git push origin main"
git config --global alias.save "!git add -A && git commit -m 'work-in-progress: auto-save'"
git config --global alias.undo "reset HEAD~1 --soft"

# Usage examples
git st          # Short status
git sync        # Pull and push in one command
git save        # Quick save of all changes
git undo        # Undo last commit (keeps changes)
git last        # Show last commit details
```

## 📊 Common Scenarios

### Scenario 1: Forgot to Pull, Now Have Conflicts

```bash
# You get "rejected - non-fast-forward" error
git pull origin main --rebase

# If conflicts appear:
# 1. Open conflicted files (VS Code shows them)
# 2. Resolve conflicts (choose which code to keep)
# 3. Stage resolved files
git add <resolved-files>
git rebase --continue

# Push after resolving
git push origin main
```

### Scenario 2: Made a Mistake in Last Commit

```bash
# If you haven't pushed yet:
git reset HEAD~1 --soft  # Undo commit, keep changes
# Fix the issue
git add .
git commit -m "corrected message"

# If you already pushed:
# DON'T use reset - instead make a new commit fixing it
git add .
git commit -m "fix: correct issue from previous commit"
git push origin main
```

### Scenario 3: Want to Abandon All Local Changes

```bash
# Discard ALL uncommitted changes (CAREFUL!)
git reset --hard HEAD

# Discard specific file changes
git checkout -- <file>

# Start fresh from GitHub
git fetch origin
git reset --hard origin/main
```

### Scenario 4: Check What Changed Before Committing

```bash
# See all changes
git diff

# See staged changes
git diff --staged

# See file names that changed
git status --short

# See changes in specific file
git diff <file>
```

### Scenario 5: Need to Work on Feature Without Breaking Main

```bash
# Create and switch to feature branch
git checkout -b feat/my-feature

# Work on feature, commit normally
git add .
git commit -m "feat: work in progress"

# When ready, merge to main
git checkout main
git pull origin main --rebase
git merge feat/my-feature
git push origin main

# Delete feature branch
git branch -d feat/my-feature
```

## 🤖 Claude-Managed Git Workflow

### When to Use Claude for Git Operations

**ALWAYS use Claude for:**
- ✅ End-of-session commits (comprehensive messages)
- ✅ Major feature completion (detailed commit history)
- ✅ Refactoring or reorganization (like we just did)
- ✅ When you want proper conventional commit formatting
- ✅ When you're unsure about commit message wording

**Optional to use Claude for:**
- Small bug fixes (you can handle these quickly)
- Documentation updates (straightforward commits)
- Typo fixes (simple one-liners)

### How to Ask Claude to Commit

**Simple request:**
> "Claude, commit and push my changes"

**With specific message:**
> "Claude, commit these changes as a feature addition for the new scraper"

**Review before committing:**
> "Claude, show me what changed and draft a commit message"

**Multiple commits:**
> "Claude, commit the scraper changes separately from the doc updates"

### What Claude Will Do

1. **Review Changes**: `git status` and `git diff` to understand what changed
2. **Categorize**: Group related changes (features, fixes, docs, etc.)
3. **Draft Message**: Write conventional commit message with details
4. **Stage**: `git add` appropriate files
5. **Commit**: Create commit with proper formatting
6. **Pull**: Sync with GitHub to avoid conflicts
7. **Push**: Push to origin/main
8. **Report**: Tell you commit hash and summary

## 📅 Recommended Commit Frequency

### During Active Development

**Commit every 30-60 minutes when:**
- Working on new feature (save incremental progress)
- Making risky changes (easy to rollback)
- About to test something that might break code
- Switching between different tasks

**Commit immediately when:**
- Bug fix is complete and tested
- Feature is working and tested
- Documentation update is done
- Before taking a break or ending session

### Minimum Commit Schedule

Even if nothing major changed:
- **End of each coding session**: Commit work-in-progress
- **End of day**: Push everything to GitHub (backup)
- **Before major refactoring**: Save current state first
- **After running tests successfully**: Commit passing state

## 🚫 What NOT to Commit

**Never commit these files** (already in `.gitignore`):

```
.env                    # Secrets and API keys
.env.*                  # Environment configs with secrets
*.db                    # SQLite databases with real data
__pycache__/            # Python cache
.venv/                  # Virtual environment
.DS_Store               # Mac system files
*.pyc                   # Compiled Python
node_modules/           # Node dependencies (if any)
```

**Before EVERY commit, verify:**

```bash
# Check for accidentally staged secrets
git diff --cached | grep -i "api_key\|password\|secret\|token"

# Should return nothing - if it finds secrets, STOP and remove them
```

## 🔄 Sync Strategies

### Strategy 1: Always In Sync (Safest)

```bash
# Before starting work
git pull origin main --rebase

# After every commit
git push origin main

# Before ending session
git push origin main
```

**Pros:** GitHub always has your latest work
**Cons:** More frequent network calls

### Strategy 2: Batch Sync (Efficient)

```bash
# Start of session
git pull origin main --rebase

# Commit locally multiple times (no push)
git commit -m "..."
git commit -m "..."
git commit -m "..."

# End of session (push all at once)
git push origin main
```

**Pros:** Fewer network calls
**Cons:** GitHub may be hours behind

### Strategy 3: Hybrid (Recommended)

```bash
# Start of session
git pull origin main --rebase

# Major features/fixes: commit + push immediately
git commit -m "feat: major feature"
git push origin main

# Minor changes: commit locally
git commit -m "style: formatting"

# End of session: push everything
git push origin main
```

**Pros:** Balance between safety and efficiency
**Cons:** Requires judgment on what's "major"

## 📝 Commit Message Templates

### Feature Addition

```
feat(component): add new capability

Implemented [feature] that allows [functionality].

Technical details:
- Added [class/function]
- Integrated with [system]
- Tested with [test approach]

Testing: [test results]

Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Bug Fix

```
fix(component): resolve [specific issue]

Problem: [describe the bug]
Root cause: [what was wrong]
Solution: [what you changed]

Fixes #[issue-number] (if applicable)

Testing: [how you verified the fix]

Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Refactoring

```
refactor(component): improve code organization

Reorganized [component] for better [maintainability/performance/clarity].

Changes:
- Moved [files] to [location]
- Extracted [logic] into [new structure]
- Renamed [old] to [new]

No functionality changes.
All tests passing: [test results]

Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Documentation

```
docs: update [topic] documentation

Updated [documentation] to reflect [changes/improvements].

- Added section on [topic]
- Clarified [confusing point]
- Fixed [errors/outdated info]

Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

## 🎯 Best Practices Summary

### DO ✅

- Pull before starting work every session
- Commit frequently (every 30-60 min)
- Write clear, descriptive commit messages
- Push to GitHub at end of every session
- Use conventional commit format
- Let Claude handle complex commits
- Review changes before committing (`git status`, `git diff`)
- Keep commits focused (one logical change per commit)

### DON'T ❌

- Don't commit secrets or API keys
- Don't push without pulling first
- Don't use vague messages ("fix stuff", "updates")
- Don't commit broken/untested code to main
- Don't force push to main (`git push --force`)
- Don't commit large binary files or data dumps
- Don't batch 3+ days of work into one commit

## 🆘 Emergency Recovery

### Lost Work (Uncommitted Changes)

```bash
# If you accidentally reset/deleted uncommitted work
# Check Git reflog (Git keeps history of everything)
git reflog
git checkout <commit-hash>
```

### Pushed Wrong Commit

```bash
# Create new commit that reverses the bad one
git revert <bad-commit-hash>
git push origin main

# Don't use reset --hard on pushed commits (breaks others' history)
```

### Need to Go Back in Time

```bash
# View commit history
git log --oneline --graph --all

# Create new branch from old commit (safe)
git checkout -b recovery <old-commit-hash>

# If happy with old state, merge back to main
git checkout main
git merge recovery
git push origin main
```

## 🔗 Quick Reference Card

```bash
# DAILY WORKFLOW
git pull origin main --rebase     # Start: sync with GitHub
git add .                          # Stage changes
git commit -m "type: description"  # Commit with message
git push origin main               # Push to GitHub

# CHECKING STATUS
git status                         # What changed?
git diff                          # Show changes
git log --oneline -5              # Recent commits

# UNDO OPERATIONS
git reset HEAD~1 --soft           # Undo last commit, keep changes
git checkout -- <file>            # Discard file changes
git clean -fd                     # Remove untracked files

# BRANCHING
git checkout -b feat/new-feature  # Create branch
git checkout main                 # Switch to main
git merge feat/new-feature        # Merge branch
git branch -d feat/new-feature    # Delete branch

# EMERGENCY
git stash                         # Save work temporarily
git stash pop                     # Restore stashed work
git reflog                        # See all Git history
```

## 📞 When to Ask for Help

**Ask Claude when:**
- Merge conflicts appear (I'll help resolve)
- Commit message is complex (I'll write it)
- Not sure what to commit (I'll review and advise)
- Git error messages are confusing (I'll explain and fix)
- Want to reorganize commit history (I'll help clean up)

**Self-serve when:**
- Simple typo fixes
- Small documentation updates
- Quick formatting changes
- Adding comments to code

---

**Remember:** Git is your safety net. Commit early, commit often. You can always undo commits, but you can't recover uncommitted work!

**Pro Tip:** At the end of every session, ask Claude: "Review my changes and commit everything with a good message." This ensures your GitHub repo is always current and well-documented.
