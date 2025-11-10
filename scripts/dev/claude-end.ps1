# Claude End - Unified End Script with PR Creation
# Run this at the END of every Claude Code session
#
# Usage:
#   .\scripts\claude-end.ps1 [-Message "Custom commit message"]
#
# What it does:
#   1. Checks for uncommitted changes
#   2. Commits all changes with a descriptive message
#   3. Pushes to GitHub (with retry logic)
#   4. Creates a Pull Request automatically
#   5. Shows the PR URL for review

param(
    [string]$Message = "",  # Optional custom commit message
    [switch]$NoPR           # Skip PR creation if you just want to push
)

$ErrorActionPreference = "Continue"

Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║         🏁 CLAUDE CODE SESSION - WRAPPING UP 🏁          ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

# Function to retry git operations with exponential backoff
function Invoke-GitWithRetry {
    param(
        [string]$Command,
        [int]$MaxRetries = 4
    )
    $delays = @(2, 4, 8, 16)
    for ($i = 0; $i -lt $MaxRetries; $i++) {
        Write-Host "Executing: git $Command" -ForegroundColor Gray
        Invoke-Expression "git $Command"
        if ($LASTEXITCODE -eq 0) {
            return $true
        }
        if ($i -lt ($MaxRetries - 1)) {
            $delay = $delays[$i]
            Write-Warning "Command failed (attempt $($i + 1)/$MaxRetries). Retrying in $delay seconds..."
            Start-Sleep -Seconds $delay
        }
    }
    return $false
}

# Step 1: Check current branch
Write-Host "`n" + ("═" * 60) -ForegroundColor Cyan
Write-Host "STEP 1: Checking current branch" -ForegroundColor Cyan
Write-Host ("═" * 60) -ForegroundColor Cyan

$currentBranch = git rev-parse --abbrev-ref HEAD
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to get current branch."
    exit 1
}

Write-Host "Current branch: $currentBranch" -ForegroundColor Green

# Validate branch name (must start with claude/ for proper permissions)
if ($currentBranch -eq "main") {
    Write-Error "You're on the main branch! Please create a feature branch first."
    Write-Host "`nTo create a branch, run:" -ForegroundColor Yellow
    Write-Host "  git checkout -b claude/your-feature-name-<session-id>" -ForegroundColor Gray
    exit 1
}

if ($currentBranch -notmatch '^claude/') {
    Write-Warning "⚠️  Branch doesn't start with 'claude/' - push may fail due to permissions."
    Write-Host "Branch name should be: claude/<description>-<session-id>" -ForegroundColor Yellow
}

# Step 2: Check for changes
Write-Host "`n" + ("═" * 60) -ForegroundColor Cyan
Write-Host "STEP 2: Checking for changes" -ForegroundColor Cyan
Write-Host ("═" * 60) -ForegroundColor Cyan

$status = git status --porcelain
if (-not $status) {
    Write-Host "✅ No uncommitted changes found." -ForegroundColor Green
    Write-Host "`nChecking if branch is ahead of remote..." -ForegroundColor Yellow

    git fetch origin $currentBranch --quiet 2>$null
    $localCommit = git rev-parse $currentBranch 2>$null
    $remoteCommit = git rev-parse "origin/$currentBranch" 2>$null

    if ($localCommit -eq $remoteCommit) {
        Write-Host "✅ Branch is up to date with remote. Nothing to push." -ForegroundColor Green
        exit 0
    } else {
        Write-Host "📤 Branch has unpushed commits. Proceeding to push..." -ForegroundColor Yellow
    }
} else {
    # Show what's changed
    Write-Host "Found uncommitted changes:" -ForegroundColor Yellow
    git status --short

    # Step 3: Commit changes
    Write-Host "`n" + ("═" * 60) -ForegroundColor Cyan
    Write-Host "STEP 3: Committing changes" -ForegroundColor Cyan
    Write-Host ("═" * 60) -ForegroundColor Cyan

    # Generate or use provided commit message
    if ($Message) {
        $commitMessage = $Message
        Write-Host "Using provided message: $commitMessage" -ForegroundColor Green
    } else {
        # Generate message based on changes
        Write-Host "Generating commit message based on changes..." -ForegroundColor Yellow

        $addedFiles = git diff --cached --name-only --diff-filter=A
        $modifiedFiles = git diff --cached --name-only --diff-filter=M
        $deletedFiles = git diff --cached --name-only --diff-filter=D
        $untrackedFiles = git ls-files --others --exclude-standard

        # Simple message generation
        $changes = @()
        if ($untrackedFiles) { $changes += "Add new files" }
        if ($modifiedFiles) { $changes += "Update existing files" }
        if ($deletedFiles) { $changes += "Remove files" }

        if ($changes.Count -eq 0) {
            $commitMessage = "Update project files"
        } else {
            $commitMessage = $changes -join ", "
        }

        Write-Host "Generated message: $commitMessage" -ForegroundColor Green
        Write-Host "`nTo use a custom message next time, run:" -ForegroundColor Gray
        Write-Host "  .\scripts\claude-end.ps1 -Message 'Your message here'" -ForegroundColor Gray
    }

    # Stage all changes
    Write-Host "`nStaging all changes..." -ForegroundColor Yellow
    git add -A
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to stage changes."
        exit 1
    }

    # Commit
    Write-Host "Creating commit..." -ForegroundColor Yellow
    git commit -m $commitMessage
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create commit."
        exit 1
    }

    Write-Host "✅ Changes committed successfully!" -ForegroundColor Green
}

# Step 4: Push to GitHub
Write-Host "`n" + ("═" * 60) -ForegroundColor Cyan
Write-Host "STEP 4: Pushing to GitHub" -ForegroundColor Cyan
Write-Host ("═" * 60) -ForegroundColor Cyan

Write-Host "Pushing to origin/$currentBranch..." -ForegroundColor Yellow
if (-not (Invoke-GitWithRetry "push -u origin $currentBranch")) {
    Write-Error "Failed to push after multiple attempts."
    Write-Host "`nPossible issues:" -ForegroundColor Yellow
    Write-Host "  1. Network connectivity problems" -ForegroundColor Gray
    Write-Host "  2. Branch name doesn't match required pattern (claude/*-<session-id>)" -ForegroundColor Gray
    Write-Host "  3. Authentication issues" -ForegroundColor Gray
    exit 1
}

Write-Host "✅ Pushed to GitHub successfully!" -ForegroundColor Green

# Step 5: Create Pull Request (if gh is available and -NoPR not set)
if ($NoPR) {
    Write-Host "`n⏭️  Skipping PR creation (use without -NoPR to create PR)" -ForegroundColor Yellow
} else {
    Write-Host "`n" + ("═" * 60) -ForegroundColor Cyan
    Write-Host "STEP 5: Creating Pull Request" -ForegroundColor Cyan
    Write-Host ("═" * 60) -ForegroundColor Cyan

    # Check if gh CLI is available
    $ghAvailable = Get-Command gh -ErrorAction SilentlyContinue
    if (-not $ghAvailable) {
        Write-Warning "⚠️  GitHub CLI (gh) is not installed."
        Write-Host "`nTo create a PR manually:" -ForegroundColor Yellow
        Write-Host "  1. Go to: https://github.com/omalleyandy/billy-walters-sports-analyzer" -ForegroundColor Gray
        Write-Host "  2. Click 'Compare & pull request' for branch: $currentBranch" -ForegroundColor Gray
        Write-Host "`nOr install gh CLI:" -ForegroundColor Yellow
        Write-Host "  winget install --id GitHub.cli" -ForegroundColor Gray
    } else {
        Write-Host "Creating PR with gh CLI..." -ForegroundColor Yellow

        # Generate PR title from commit messages
        $prTitle = git log origin/main..HEAD --pretty=format:"%s" | Select-Object -First 1
        if (-not $prTitle) {
            $prTitle = $commitMessage
        }

        # Generate PR body from all commits
        $commits = git log origin/main..HEAD --pretty=format:"- %s" | Out-String
        $prBody = @"
## Changes
$commits

## Testing
- [ ] Code builds successfully
- [ ] Tests pass
- [ ] Functionality verified

---
*Created automatically by claude-end.ps1*
"@

        # Create PR
        gh pr create --title $prTitle --body $prBody --base main
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Pull Request created successfully!" -ForegroundColor Green

            # Get PR URL
            $prUrl = gh pr view --json url --jq .url
            if ($prUrl) {
                Write-Host "`n🔗 PR URL: $prUrl" -ForegroundColor Cyan
            }
        } else {
            Write-Warning "Failed to create PR automatically."
            Write-Host "`nCreate PR manually at:" -ForegroundColor Yellow
            Write-Host "  https://github.com/omalleyandy/billy-walters-sports-analyzer/compare/$currentBranch" -ForegroundColor Gray
        }
    }
}

# Final message
Write-Host "`n╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║               🎉 SESSION COMPLETE! 🎉                    ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Green

Write-Host "`n✅ Your changes are backed up to GitHub!" -ForegroundColor Green
Write-Host "✅ Ready for code review and merging!" -ForegroundColor Green
