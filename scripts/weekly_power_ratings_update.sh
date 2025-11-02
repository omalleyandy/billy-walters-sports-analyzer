#!/bin/bash
#
# Weekly NFL Power Ratings Update Script
#
# This script automates the Billy Walters power ratings weekly update cycle:
# 1. Scrape latest week's NFL games from ESPN API
# 2. Update power ratings from game results
# 3. Display top-rated teams
#
# Usage:
#   ./scripts/weekly_power_ratings_update.sh 9     # Update for Week 9
#   ./scripts/weekly_power_ratings_update.sh 9 2024  # Specific season
#
# Schedule with cron (runs every Tuesday at 6 AM):
#   0 6 * * 2 cd /path/to/billy-walters-sports-analyzer && ./scripts/weekly_power_ratings_update.sh $(date +\%V)
#

set -e  # Exit on error

# Configuration
WEEK=${1:-$(date +%V)}  # Default to current week number
SEASON=${2:-2025}        # Default to 2025 season
PROJECT_DIR=$(cd "$(dirname "$0")/.." && pwd)

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Billy Walters Weekly Power Ratings Update${NC}"
echo -e "${BLUE}  Week: $WEEK, Season: $SEASON${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Change to project directory
cd "$PROJECT_DIR"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source .venv/bin/activate
fi

# Run weekly update via CLI
echo -e "${GREEN}Running weekly NFL update...${NC}"
echo ""

uv run walters-analyzer weekly-nfl-update --week "$WEEK" --season "$SEASON"

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}  ✅ Weekly update completed successfully!${NC}"
    echo -e "${GREEN}============================================${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}============================================${NC}"
    echo -e "${RED}  ❌ Weekly update failed!${NC}"
    echo -e "${RED}============================================${NC}"
    exit 1
fi
