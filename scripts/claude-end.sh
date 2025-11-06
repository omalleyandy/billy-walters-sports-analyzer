#!/bin/bash
# Claude End - Unified End Script with PR Creation
# Run this at the END of every Claude Code session
#
# Usage:
#   ./scripts/claude-end.sh
#   ./scripts/claude-end.sh --message "Custom commit message"
#   ./scripts/claude-end.sh --no-pr  # Skip PR creation
#
# What it does:
#   1. Checks for uncommitted changes
#   2. Commits all changes with a descriptive message
#   3. Pushes to GitHub (with retry logic)
#   4. Creates a Pull Request automatically
#   5. Shows the PR URL for review

# Colors for output
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
GRAY='\033[0;90m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Parse arguments
CUSTOM_MESSAGE=""
NO_PR=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --message|-m)
            CUSTOM_MESSAGE="$2"
            shift 2
            ;;
        --no-pr)
            NO_PR=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [--message \"commit message\"] [--no-pr]"
            exit 1
            ;;
    esac
done

# Function to print section headers
print_section() {
    echo -e "\n${CYAN}$(printf '═%.0s' {1..60})${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}$(printf '═%.0s' {1..60})${NC}"
}

# Function to retry git commands with exponential backoff
retry_git_command() {
    local max_attempts=4
    local attempt=1
    local delay=2
    local command="$@"

    while [ $attempt -le $max_attempts ]; do
        echo -e "${GRAY}Executing: git $command${NC}"
        if git $command; then
            return 0
        else
            if [ $attempt -lt $max_attempts ]; then
                echo -e "${YELLOW}⚠️  Command failed (attempt $attempt/$max_attempts). Retrying in ${delay}s...${NC}"
                sleep $delay
                delay=$((delay * 2))
                attempt=$((attempt + 1))
            else
                echo -e "${RED}❌ Command failed after $max_attempts attempts${NC}"
                return 1
            fi
        fi
    done
}

# Banner
echo -e "${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║         🏁 CLAUDE CODE SESSION - WRAPPING UP 🏁          ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"

# Step 1: Check current branch
print_section "STEP 1: Checking current branch"

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to get current branch.${NC}"
    exit 1
fi

echo -e "${GREEN}Current branch: $CURRENT_BRANCH${NC}"

# Validate branch name (must start with claude/ for proper permissions)
if [ "$CURRENT_BRANCH" = "main" ]; then
    echo -e "${RED}❌ You're on the main branch! Please create a feature branch first.${NC}"
    echo -e "\n${YELLOW}To create a branch, run:${NC}"
    echo -e "${GRAY}  git checkout -b claude/your-feature-name-<session-id>${NC}"
    exit 1
fi

if [[ ! "$CURRENT_BRANCH" =~ ^claude/ ]]; then
    echo -e "${YELLOW}⚠️  Branch doesn't start with 'claude/' - push may fail due to permissions.${NC}"
    echo -e "${YELLOW}Branch name should be: claude/<description>-<session-id>${NC}"
fi

# Step 2: Check for changes
print_section "STEP 2: Checking for changes"

STATUS=$(git status --porcelain)
if [ -z "$STATUS" ]; then
    echo -e "${GREEN}✅ No uncommitted changes found.${NC}"
    echo -e "\n${YELLOW}Checking if branch is ahead of remote...${NC}"

    git fetch origin "$CURRENT_BRANCH" --quiet 2>/dev/null
    LOCAL_COMMIT=$(git rev-parse "$CURRENT_BRANCH" 2>/dev/null)
    REMOTE_COMMIT=$(git rev-parse "origin/$CURRENT_BRANCH" 2>/dev/null)

    if [ "$LOCAL_COMMIT" = "$REMOTE_COMMIT" ]; then
        echo -e "${GREEN}✅ Branch is up to date with remote. Nothing to push.${NC}"
        exit 0
    else
        echo -e "${YELLOW}📤 Branch has unpushed commits. Proceeding to push...${NC}"
    fi
else
    # Show what's changed
    echo -e "${YELLOW}Found uncommitted changes:${NC}"
    git status --short

    # Step 3: Commit changes
    print_section "STEP 3: Committing changes"

    # Generate or use provided commit message
    if [ -n "$CUSTOM_MESSAGE" ]; then
        COMMIT_MESSAGE="$CUSTOM_MESSAGE"
        echo -e "${GREEN}Using provided message: $COMMIT_MESSAGE${NC}"
    else
        # Generate message based on changes
        echo -e "${YELLOW}Generating commit message based on changes...${NC}"

        ADDED_FILES=$(git ls-files --others --exclude-standard)
        MODIFIED_FILES=$(git diff --name-only)
        DELETED_FILES=$(git diff --name-only --diff-filter=D)

        # Simple message generation
        CHANGES=()
        if [ -n "$ADDED_FILES" ]; then
            CHANGES+=("Add new files")
        fi
        if [ -n "$MODIFIED_FILES" ]; then
            CHANGES+=("Update existing files")
        fi
        if [ -n "$DELETED_FILES" ]; then
            CHANGES+=("Remove files")
        fi

        if [ ${#CHANGES[@]} -eq 0 ]; then
            COMMIT_MESSAGE="Update project files"
        else
            COMMIT_MESSAGE=$(IFS=', '; echo "${CHANGES[*]}")
        fi

        echo -e "${GREEN}Generated message: $COMMIT_MESSAGE${NC}"
        echo -e "\n${GRAY}To use a custom message next time, run:${NC}"
        echo -e "${GRAY}  ./scripts/claude-end.sh --message 'Your message here'${NC}"
    fi

    # Stage all changes
    echo -e "\n${YELLOW}Staging all changes...${NC}"
    if ! git add -A; then
        echo -e "${RED}❌ Failed to stage changes.${NC}"
        exit 1
    fi

    # Commit
    echo -e "${YELLOW}Creating commit...${NC}"
    if ! git commit -m "$COMMIT_MESSAGE"; then
        echo -e "${RED}❌ Failed to create commit.${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ Changes committed successfully!${NC}"
fi

# Step 4: Push to GitHub
print_section "STEP 4: Pushing to GitHub"

echo -e "${YELLOW}Pushing to origin/$CURRENT_BRANCH...${NC}"
if ! retry_git_command "push -u origin $CURRENT_BRANCH"; then
    echo -e "${RED}❌ Failed to push after multiple attempts.${NC}"
    echo -e "\n${YELLOW}Possible issues:${NC}"
    echo -e "${GRAY}  1. Network connectivity problems${NC}"
    echo -e "${GRAY}  2. Branch name doesn't match required pattern (claude/*-<session-id>)${NC}"
    echo -e "${GRAY}  3. Authentication issues${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Pushed to GitHub successfully!${NC}"

# Step 5: Create Pull Request (if gh is available and --no-pr not set)
if [ "$NO_PR" = true ]; then
    echo -e "\n${YELLOW}⏭️  Skipping PR creation (use without --no-pr to create PR)${NC}"
else
    print_section "STEP 5: Creating Pull Request"

    # Check if gh CLI is available
    if ! command -v gh &> /dev/null; then
        echo -e "${YELLOW}⚠️  GitHub CLI (gh) is not installed.${NC}"
        echo -e "\n${YELLOW}To create a PR manually:${NC}"
        echo -e "${GRAY}  1. Go to: https://github.com/omalleyandy/billy-walters-sports-analyzer${NC}"
        echo -e "${GRAY}  2. Click 'Compare & pull request' for branch: $CURRENT_BRANCH${NC}"
        echo -e "\n${YELLOW}Or install gh CLI:${NC}"
        echo -e "${GRAY}  See: https://cli.github.com/manual/installation${NC}"
    else
        echo -e "${YELLOW}Creating PR with gh CLI...${NC}"

        # Generate PR title from commit messages
        PR_TITLE=$(git log origin/main..HEAD --pretty=format:"%s" | head -1)
        if [ -z "$PR_TITLE" ]; then
            PR_TITLE="$COMMIT_MESSAGE"
        fi

        # Generate PR body from all commits
        COMMITS=$(git log origin/main..HEAD --pretty=format:"- %s")
        PR_BODY="## Changes
$COMMITS

## Testing
- [ ] Code builds successfully
- [ ] Tests pass
- [ ] Functionality verified

---
*Created automatically by claude-end.sh*"

        # Create PR
        if echo "$PR_BODY" | gh pr create --title "$PR_TITLE" --body-file - --base main; then
            echo -e "${GREEN}✅ Pull Request created successfully!${NC}"

            # Get PR URL
            PR_URL=$(gh pr view --json url --jq .url 2>/dev/null)
            if [ -n "$PR_URL" ]; then
                echo -e "\n${CYAN}🔗 PR URL: $PR_URL${NC}"
            fi
        else
            echo -e "${YELLOW}⚠️  Failed to create PR automatically.${NC}"
            echo -e "\n${YELLOW}Create PR manually at:${NC}"
            echo -e "${GRAY}  https://github.com/omalleyandy/billy-walters-sports-analyzer/compare/$CURRENT_BRANCH${NC}"
        fi
    fi
fi

# Final message
echo -e "\n${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║               🎉 SESSION COMPLETE! 🎉                    ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"

echo -e "\n${GREEN}✅ Your changes are backed up to GitHub!${NC}"
echo -e "${GREEN}✅ Ready for code review and merging!${NC}"
