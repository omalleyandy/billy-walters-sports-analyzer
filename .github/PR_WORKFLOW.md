# Pull Request Workflow Guide

## Overview

This guide documents the recommended PR workflow for the Billy Walters Sports Analyzer project going forward.

**Current Status**: Transitioned from direct-to-main commits to PR-based workflow (Nov 12, 2025)

---

## Why Use PRs?

**Benefits**:
- ✅ **Squash and merge** - Clean, linear commit history
- ✅ **CI validation** - All tests must pass before merge
- ✅ **Code review** - Optional but available for collaboration
- ✅ **Rollback friendly** - Easy to revert a single PR
- ✅ **Documentation** - PRs provide context for changes

---

## Recommended Workflow

### 1. Start New Work

```bash
# Always start from updated main
git checkout main
git pull origin main --rebase

# Create descriptive feature branch
git checkout -b feat/your-feature-name
# or: fix/bug-name, docs/update-name, chore/cleanup-name
```

**Branch Naming Convention**:
- `feat/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation only
- `chore/` - Maintenance, cleanup
- `refactor/` - Code refactoring
- `test/` - Test additions/updates

### 2. Make Changes

```bash
# Work on your feature
# Commit often with conventional commit messages

git add .
git commit -m "feat(scope): add new feature"
git commit -m "test(scope): add tests for feature"
git commit -m "docs(scope): update documentation"
```

**Conventional Commit Format**:
```
type(scope): brief description

Optional detailed explanation.

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

### 3. Push and Create PR

```bash
# Push feature branch to GitHub
git push -u origin feat/your-feature-name

# Create pull request
gh pr create --title "feat: Add your feature" --body "$(cat <<'EOF'
## Summary
Brief description of what this PR does.

## Changes
- Key change 1
- Key change 2
- Key change 3

## Testing
- [ ] All tests pass locally
- [ ] Manual testing completed
- [ ] No breaking changes

## Related Issues
Fixes #123 (if applicable)

🤖 Generated with Claude Code
EOF
)"
```

### 4. Wait for CI Checks

GitHub Actions will automatically run:
- ✅ Ruff formatting check
- ✅ Ruff linting
- ✅ Pyright type checking
- ✅ Pytest (146 tests, multi-platform, multi-version)
- ✅ Security scan (pip-audit, TruffleHog)

**If CI fails**:
```bash
# Fix issues locally
uv run ruff format .
uv run ruff check . --fix
uv run pyright
uv run pytest tests/ -v

# Commit fixes
git add .
git commit -m "fix(ci): resolve linting issues"
git push
```

### 5. Squash and Merge

**On GitHub** (when all checks pass):
1. Click **"Squash and merge"** button
2. Edit commit message if needed
3. Confirm merge
4. **Delete branch** after merge

**Locally** (cleanup):
```bash
# Switch back to main
git checkout main

# Pull merged changes
git pull origin main

# Delete local feature branch
git branch -d feat/your-feature-name

# Prune deleted remote branches
git remote prune origin
```

---

## Quick Commands

### Daily Workflow
```bash
# Start of day - sync with GitHub
git checkout main && git pull origin main --rebase

# Create new feature branch
git checkout -b feat/new-feature

# Work... commit... work... commit...

# Push and create PR
git push -u origin feat/new-feature
gh pr create --web  # Opens browser for PR creation

# After PR merged - cleanup
git checkout main && git pull origin main
git branch -d feat/new-feature
```

### Emergency Hotfix
```bash
# Create hotfix branch from main
git checkout main && git pull origin main
git checkout -b fix/critical-bug

# Fix, test, commit
git add . && git commit -m "fix: resolve critical bug"

# Push and create PR with urgency label
git push -u origin fix/critical-bug
gh pr create --title "fix: Critical bug" --label "urgent"
```

---

## Alternative: Direct to Main (Solo Work)

If you prefer to continue committing directly to main:

**When to use**:
- ✅ Small documentation updates
- ✅ Typo fixes
- ✅ Quick configuration changes
- ✅ Solo development with no collaboration

**How to use**:
```bash
# Work on main branch
git checkout main
git pull origin main --rebase

# Make changes and commit
git add .
git commit -m "docs: update README"

# Push directly to main
git push origin main
```

**Note**: Even with direct commits, all CI checks still run on every push to main.

---

## Branch Cleanup

### Manual Cleanup
```bash
# List merged remote branches
gh pr list --state merged --limit 50

# Delete specific remote branch
git push origin --delete branch-name

# Prune local references to deleted remotes
git remote prune origin

# Delete local merged branches
git branch --merged main | grep -v "main" | xargs git branch -d
```

### Automated Cleanup (After PR Merge)
GitHub can auto-delete branches after PR merge:
1. Go to repo **Settings** → **General**
2. Enable **"Automatically delete head branches"**

---

## Best Practices

### Commit Messages
- Use conventional commit format
- Keep first line under 50 characters
- Include detailed explanation if needed
- Reference issues with `Fixes #123`

### PR Size
- **Small PRs** - Easier to review, faster to merge
- **Single concern** - One feature/fix per PR
- **Complete** - Include tests and docs

### Testing
- Always run local validation before pushing
- Check CI status before marking PR ready
- Manual testing for user-facing changes

### Documentation
- Update CLAUDE.md for new patterns
- Update README.md for user-visible changes
- Use LESSONS_LEARNED.md for troubleshooting

---

## GitHub Settings

### Branch Protection (Already Enabled)
- ✅ Require PR reviews: No (solo project)
- ✅ Require status checks: **Yes** (all CI must pass)
- ✅ Require branches up to date: No
- ✅ Cannot force push to main: Yes
- ✅ Cannot delete main: Yes

### Recommended Settings
- Enable auto-delete branches after merge
- Enable Dependabot for dependency updates
- Keep "Squash and merge" as default merge method

---

## Transition Notes

**Previous Workflow** (Pre Nov 12, 2025):
- Direct commits to main
- All commits preserved in history
- 30+ feature branches accumulated

**New Workflow** (Post Nov 12, 2025):
- Feature branches + PRs
- Squash and merge for clean history
- Auto-delete branches after merge

**Cleanup Completed**:
- ✅ Deleted 15 merged remote branches
- ✅ Kept 18 unmerged branches for review
- ✅ All main commits intact and synced

---

## Resources

- GitHub CLI: https://cli.github.com/manual/gh_pr_create
- Conventional Commits: https://www.conventionalcommits.org/
- Git Workflow Guide: `.github/GIT_WORKFLOW_GUIDE.md`
- CI/CD Documentation: `.github/CI_CD.md`

---

**Last Updated**: 2025-11-12
**Status**: ✅ Active workflow
