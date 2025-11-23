# CI/CD Prevention Guide

**Last Updated:** 2025-11-23
**Related Issues:** Formatting violations causing workflow failures
**See Also:** [CLAUDE.md CI/CD Section](../../CLAUDE.md#cicd-pipeline), [CI_CD.md](../../.github/CI_CD.md)

---

## Overview

This guide documents common CI/CD failures and prevention strategies to keep your workflow green. Learn from past failures to avoid repeating them.

### Quick Facts

- **Most Common Failure:** Code formatting violations (ruff)
- **Average Detection Time:** < 2 minutes (fast fail, not stalled)
- **Fix Time:** 30 seconds (auto-format and push)
- **Prevention:** Run validation commands before every commit

---

## Incident Summary (2025-11-23)

### What Happened

**Symptom:** CI workflow failing on "Lint and Format" job across all 10 recent runs

**Root Cause:** Formatting violation introduced in commit `71bbe09`
- File: `tests/integration/test_sfactor_integration.py`
- Line 232-234: Function signature unnecessarily split across 3 lines
- Developer modified file but didn't run `ruff format` before committing

**Impact:**
- All CI checks blocked (failed before reaching type check and tests)
- Tests were passing (270 passing, 0 failing) but never ran in CI
- Fixed with single commit: `4ffb499`

**Resolution Time:** < 5 minutes

### What We Fixed

1. **Formatted test file** with `uv run ruff format tests/integration/test_sfactor_integration.py`
2. **Updated codecov config** in `.github/workflows/ci.yml` (changed `file:` to `files:`)
3. **Pushed and verified** all checks pass

---

## Prevention Checklist

### ✅ Before Every Commit

Run these commands in order (all must pass):

```bash
# 1. Format code (fixes formatting automatically)
uv run ruff format .

# 2. Check formatting (verify it worked)
uv run ruff format --check .

# 3. Run linter
uv run ruff check .

# 4. Run type checker
uv run pyright

# 5. Run tests with coverage
uv run pytest tests/ -v --cov=. --cov-report=term
```

**Time Required:** ~2-3 minutes
**Best Practice:** Run before every commit, not just before pushing

### ✅ Before Every Push

```bash
# Quick status check
git status

# View what you're about to push
git log origin/main..HEAD --oneline

# Verify no uncommitted changes
git diff --cached
```

### ✅ Optional: Local Pre-Commit Hook

Automate the validation check. Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Pre-commit hook: Check formatting before allowing commit

echo "Running pre-commit checks..."

# Check formatting
uv run ruff format --check . || {
    echo ""
    echo "[ERROR] Code formatting check failed!"
    echo "Run: uv run ruff format ."
    echo "Then stage the changes and try committing again."
    exit 1
}

# Quick lint check (optional, can slow down commits)
# uv run ruff check . || {
#     echo "[ERROR] Linting failed!"
#     exit 1
# }

echo "[OK] Pre-commit checks passed!"
exit 0
```

**Installation:**
```bash
# Copy template to git hooks
cp docs/guides/ci_cd_prevention_guide.md .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

---

## Common CI/CD Failures

### 1. Formatting Violation (E501, Ruff)

**Symptoms:**
- CI job: "Lint and Format" fails within 1-2 minutes
- Error: `would reformat` or format check exits with code 1
- All other jobs may not run (depends on workflow configuration)

**Root Causes:**
- Didn't run `ruff format .` before committing
- Long lines exceed 88 character limit
- Unnecessary line breaks in code

**Fix:**
```bash
# Auto-fix formatting
uv run ruff format .

# Verify fix
uv run ruff format --check .

# Stage and commit
git add -A
git commit --amend --no-edit
git push origin main --force-with-lease  # Only if not yet pushed
```

**Prevention:**
- Always run `ruff format .` before committing
- Set up pre-commit hook (see above)
- Use editor integration if available

---

### 2. Type Checking Failures (Pyright)

**Symptoms:**
- CI job: "Type Check" fails
- Error: `error: No overloads for "..." match the provided arguments`
- Issues with Optional types, type narrowing

**Root Causes:**
- Missing type hints on new code
- Calling function with wrong argument type
- Not checking for None on Optional values
- Type mismatch in assignments

**Fix:**
```bash
# Run type checker locally
uv run pyright

# Review errors (they're sorted by file/line)
# Add type hints or narrow types as needed
# See CLAUDE.md "Type Checking" section for patterns

# Verify fix
uv run pyright
```

**Prevention:**
- Add type hints to all new functions
- Use `Optional[T]` with explicit None checks
- Follow existing code patterns for type narrowing
- Run `pyright` before committing

---

### 3. Test Failures

**Symptoms:**
- CI job: "Test Python X.Y (Platform)" fails
- Error: AssertionError, ImportError, or test-specific error
- May differ between platforms (Windows vs Ubuntu)

**Root Causes:**
- Broke existing functionality with code changes
- Test has environment-specific assumptions
- Missing dependencies or imports
- Async/await issues in test

**Fix:**
```bash
# Run full test suite locally
uv run pytest tests/ -v --cov=. --cov-report=term

# Run specific failing test for details
uv run pytest tests/path/to/test_file.py::test_function -v

# Fix the issue, then re-run
uv run pytest tests/ -v
```

**Prevention:**
- Write tests for new functionality
- Run tests locally before committing
- Test on both Windows and Ubuntu if possible
- Fix deprecated dependencies quickly

---

### 4. Security Scan Failures

**Symptoms:**
- CI job: "Security Scan" fails
- Error: Secret detection, vulnerability found
- TruffleHog warning about exposed credentials

**Root Causes:**
- Accidentally committed `.env` file with API keys
- Hardcoded credentials in code
- Known vulnerable dependency version

**Fix:**
```bash
# If you committed secrets
git filter-branch --force --index-filter \
  'git rm -r --cached --ignore-unmatch .env' \
  --prune-empty --tag-name-filter cat -- --all

# Rotate the exposed secret immediately!
# Update .env.example (without actual values)

# Then push
git push origin --force --all
```

**Prevention:**
- `.env` should be in `.gitignore` (it is)
- Never hardcode API keys
- Use environment variables always
- Run `git diff --cached` before committing to spot secrets

---

### 5. Codecov/Coverage Issues

**Symptoms:**
- Coverage upload step has warnings or fails
- "Unexpected input(s)" warning from codecov action

**Root Causes:**
- Deprecated codecov action parameters (`file` vs `files`)
- Coverage report not generated properly
- Network issue uploading to codecov

**Fix:**
```bash
# Update codecov action in .github/workflows/ci.yml
# Change: file: ./coverage.xml
# To:     files: ./coverage.xml

# Verify coverage generation locally
uv run pytest tests/ --cov=. --cov-report=xml

# Check coverage.xml exists
ls -lh coverage.xml
```

**Prevention:**
- Keep GitHub Actions up-to-date
- Review action warnings in CI logs
- Test coverage locally before pushing

---

## How to Debug CI Failures Locally

### 1. Check What CI Ran

```bash
# List recent CI runs
gh run list --workflow=ci.yml --limit 5

# View details of specific run
gh run view <run-id> --log-failed
```

### 2. Replicate CI Environment

```bash
# Reset to the commit that failed
git checkout <failing-commit-hash>

# Install dependencies fresh
uv sync --all-extras --dev

# Run the exact commands CI uses
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest tests/ -v --cov=. --cov-report=xml
```

### 3. Watch CI Run in Real-Time

```bash
# List recent runs
gh run list --workflow=ci.yml --limit 1

# Watch the latest run
gh run watch <run-id>

# View specific job logs
gh run view <run-id> --log
```

---

## Workflow Job Dependencies

Understanding the CI workflow structure helps you debug faster:

```
┌─────────────────────────────────────────────────────┐
│ Push to main / Pull Request                         │
└────────────────────┬────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
         ▼           ▼           ▼
    ┌────────┐  ┌───────┐  ┌──────────┐
    │  Test  │  │ Lint  │  │  Type    │
    │(4 jobs)│  │Format │  │  Check   │
    └────────┘  └───────┘  └──────────┘
         │           │           │
         └───────────┼───────────┘
                     │
              ┌──────▼─────┐
              │  Security  │
              │   Scan     │
              └────────────┘
                     │
              ┌──────▼──────────┐
              │ All checks pass?│
              └──────┬──────────┘
                     │
           ┌─────────┴─────────┐
           │                   │
          YES                  NO
           │                   │
           ▼                   ▼
    ┌─────────────┐      ┌──────────┐
    │ Ready to    │      │ Workflow │
    │ Merge (PRs) │      │  Failed  │
    └─────────────┘      └──────────┘
```

**Key Points:**
- All jobs run in parallel (not sequentially)
- If any job fails, entire workflow fails
- Tests run on 4 combinations: Ubuntu/Windows × Python 3.11/3.12
- Lint/Format typically fails fastest (< 1 minute)

---

## Quick Reference: Most Common Fixes

| Issue | Fix | Time |
|-------|-----|------|
| Formatting | `uv run ruff format .` | 10s |
| Line too long | `uv run ruff format .` | 10s |
| Type error | Add type hint or None check | 1-5m |
| Test failure | Fix code or test | 2-10m |
| Secret detected | Rotate key, remove from git | 5-10m |
| Coverage warning | Update codecov action | 1m |

---

## Escalation Path

**If CI keeps failing:**

1. Read the specific error message in `gh run view <run-id> --log-failed`
2. Check [LESSONS_LEARNED.md](../../LESSONS_LEARNED.md) for similar issues
3. Review [CI_CD.md](../../.github/CI_CD.md) for deeper technical details
4. Replicate locally using steps in "How to Debug CI Failures Locally" section above
5. Document new patterns in this guide and LESSONS_LEARNED.md

---

## Related Documentation

- **Quick Start:** [CLAUDE.md CI/CD Section](../../CLAUDE.md#cicd-pipeline)
- **Technical Details:** [.github/CI_CD.md](../../.github/CI_CD.md)
- **Troubleshooting:** [LESSONS_LEARNED.md](../../LESSONS_LEARNED.md)
- **Git Workflow:** [.github/GIT_WORKFLOW_GUIDE.md](../../.github/GIT_WORKFLOW_GUIDE.md)
- **Validation Commands:** [CLAUDE.md Quick Reference](../../CLAUDE.md#quick-reference)

---

## Session History

### 2025-11-23: Formatting Violation Fixed

**Issue:** Formatting violation in `test_sfactor_integration.py` (line 232-234)
**Cause:** Didn't run `ruff format` before committing
**Fix:** Applied formatting, updated codecov config
**Prevention:** Document checklist and pre-commit hook template
**Commit:** `4ffb499 fix(ci): apply ruff formatting and update codecov config`

This incident led to creation of this prevention guide.

---

## Feedback & Updates

Found a new CI/CD pattern or fix? Please:
1. Document it in this guide
2. Add session summary to LESSONS_LEARNED.md
3. Update CLAUDE.md if it's a common issue
4. Commit with clear message

Keep this guide current to help prevent future issues!
