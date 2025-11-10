#!/bin/bash
# Claude Start - Unified Start Script
# Run this at the START of every Claude Code session
#
# Usage:
#   ./scripts/claude-start.sh
#   ./scripts/claude-start.sh --skip-cleanup  # Skip cleanup step for faster startup
#
# What it does:
#   1. Syncs with GitHub (fetches latest, updates main)
#   2. Cleans up merged branches (with confirmation)
#   3. Shows comprehensive status report
#   4. Gets you ready to work!

set -e  # Exit on error (but we'll handle errors manually for some steps)

# Colors for output
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
GRAY='\033[0;90m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Parse arguments
SKIP_CLEANUP=false
if [[ "$1" == "--skip-cleanup" ]]; then
    SKIP_CLEANUP=true
fi

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
        if eval "$command"; then
            return 0
        else
            if [ $attempt -lt $max_attempts ]; then
                echo -e "${YELLOW}⚠️  Attempt $attempt failed. Retrying in ${delay}s...${NC}"
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
echo -e "${CYAN}║         🚀 CLAUDE CODE SESSION - STARTING UP 🚀          ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"

# Step 1: Sync with GitHub
print_section "STEP 1: Syncing with GitHub"

# Fetch latest changes
echo "📥 Fetching latest changes from GitHub..."
if retry_git_command "git fetch origin"; then
    echo -e "${GREEN}✅ Fetch successful${NC}"
else
    echo -e "${RED}❌ Failed to fetch from GitHub. Please check your connection.${NC}"
    exit 1
fi

# Ensure main branch exists locally
if ! git show-ref --verify --quiet refs/heads/main; then
    echo "🔧 Creating local main branch..."
    if git show-ref --verify --quiet refs/remotes/origin/main; then
        git branch main origin/main
        echo -e "${GREEN}✅ Main branch created from origin/main${NC}"
    else
        echo -e "${YELLOW}⚠️  No main branch found on remote. Skipping main branch creation.${NC}"
    fi
fi

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo -e "📍 Current branch: ${WHITE}$CURRENT_BRANCH${NC}"

# Update main branch if it exists and we're not on it
if git show-ref --verify --quiet refs/heads/main && [ "$CURRENT_BRANCH" != "main" ]; then
    echo "🔄 Updating main branch..."

    # Check for uncommitted changes
    if ! git diff-index --quiet HEAD --; then
        echo -e "${YELLOW}⚠️  You have uncommitted changes. Skipping main branch update.${NC}"
        echo -e "${YELLOW}   Commit or stash your changes if you want to update main.${NC}"
    else
        # Stash current branch state, update main, then return
        RETURN_BRANCH=$CURRENT_BRANCH
        git checkout main 2>/dev/null || true

        if retry_git_command "git pull origin main --ff-only"; then
            echo -e "${GREEN}✅ Main branch updated${NC}"
        else
            echo -e "${YELLOW}⚠️  Could not fast-forward main branch. You may need to resolve conflicts manually.${NC}"
        fi

        # Return to original branch
        git checkout "$RETURN_BRANCH" 2>/dev/null || true
    fi
else
    echo -e "${GRAY}ℹ️  Skipping main branch update (on main or main doesn't exist)${NC}"
fi

# Step 2: Cleanup merged branches (optional)
if [ "$SKIP_CLEANUP" = false ]; then
    print_section "STEP 2: Cleaning up merged branches"

    # Check if main branch exists
    if ! git show-ref --verify --quiet refs/heads/main; then
        echo -e "${YELLOW}⚠️  Main branch doesn't exist. Skipping cleanup.${NC}"
    else
        # Get list of merged branches (excluding main and current branch)
        MERGED_BRANCHES=$(git branch --merged main | grep -v '^\*' | grep -v 'main' | sed 's/^[[:space:]]*//' || true)

        if [ -z "$MERGED_BRANCHES" ]; then
            echo -e "${GREEN}✅ No merged branches to clean up${NC}"
        else
            echo "Found merged branches:"
            echo "$MERGED_BRANCHES" | while read branch; do
                echo -e "  ${GRAY}- $branch${NC}"
            done

            echo -e "\n${YELLOW}Do you want to delete these branches? (y/N)${NC}"
            read -r response

            if [[ "$response" =~ ^[Yy]$ ]]; then
                SUCCESS_COUNT=0
                FAIL_COUNT=0

                echo "$MERGED_BRANCHES" | while read branch; do
                    if [ -n "$branch" ]; then
                        if git branch -d "$branch" 2>/dev/null; then
                            echo -e "${GREEN}✅ Deleted: $branch${NC}"
                            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
                        else
                            echo -e "${RED}❌ Failed to delete: $branch${NC}"
                            FAIL_COUNT=$((FAIL_COUNT + 1))
                        fi
                    fi
                done

                echo -e "\n${GREEN}Cleanup complete!${NC}"
            else
                echo -e "${GRAY}Cleanup cancelled${NC}"
            fi
        fi
    fi
else
    echo -e "\n${YELLOW}⏭️  Skipping cleanup (use without --skip-cleanup to include)${NC}"
fi

# Step 3: Show status report
print_section "STEP 3: Status Report"

echo -e "${CYAN}📍 Current Branch:${NC}"
echo -e "   ${WHITE}$CURRENT_BRANCH${NC}"

# Check for uncommitted changes
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    echo -e "\n${YELLOW}⚠️  Uncommitted Changes:${NC}"
    git status --short | head -10
    CHANGE_COUNT=$(git status --short | wc -l)
    if [ $CHANGE_COUNT -gt 10 ]; then
        echo -e "${GRAY}   ... and $((CHANGE_COUNT - 10)) more${NC}"
    fi
fi

# Show merged branches
if git show-ref --verify --quiet refs/heads/main; then
    MERGED_BRANCHES=$(git branch --merged main | grep -v '^\*' | grep -v 'main' | sed 's/^[[:space:]]*//' || true)
    if [ -n "$MERGED_BRANCHES" ]; then
        echo -e "\n${GREEN}✅ Merged Branches (safe to delete):${NC}"
        echo "$MERGED_BRANCHES" | while read branch; do
            echo -e "   ${GRAY}- $branch${NC}"
        done
    fi

    # Show unmerged branches
    UNMERGED_BRANCHES=$(git branch --no-merged main | grep -v '^\*' | sed 's/^[[:space:]]*//' || true)
    if [ -n "$UNMERGED_BRANCHES" ]; then
        echo -e "\n${YELLOW}🔄 Unmerged Branches (may need PRs):${NC}"
        echo "$UNMERGED_BRANCHES" | while read branch; do
            # Get last commit date
            LAST_COMMIT=$(git log -1 --format="%ar" "$branch" 2>/dev/null || echo "unknown")
            echo -e "   ${YELLOW}- $branch${NC} ${GRAY}(last commit: $LAST_COMMIT)${NC}"
        done
    fi
fi

# Show remote branch count
REMOTE_COUNT=$(git branch -r | grep -v 'HEAD' | wc -l)
echo -e "\n${CYAN}🌐 Remote Branches:${NC} $REMOTE_COUNT"

# Show recent commits
echo -e "\n${CYAN}📝 Recent Commits on $CURRENT_BRANCH:${NC}"
git log --oneline --max-count=5 --color=always | sed 's/^/   /'

# Final message
echo -e "\n${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              ✅ READY TO CODE WITH CLAUDE! ✅            ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"

echo -e "\n${CYAN}ℹ️  When you're done coding, run:${NC}"
echo -e "   ${WHITE}./scripts/claude-end.sh${NC}"
echo -e "   ${GRAY}This will commit, push, and create a PR automatically!${NC}"
