# ESPN Roadmap - Quick Start Guide

**Objective**: Get from planning to production in 3 steps
**Time to First Results**: ~15 minutes
**Current Status**: All infrastructure ready, need to activate

---

## Step 1: Activate Automated Collection (5 min)

### Option A: GitHub Actions (Recommended - Runs Every Friday)

1. **Commit the workflow file** (already created in `.github/workflows/espn-collection.yml`)

```bash
git add .github/workflows/espn-collection.yml
git commit -m "ci: add ESPN automated data collection (Friday 9 AM UTC)"
git push origin main
```

2. **Enable Actions in GitHub** (one-time setup)
   - Go to your repo Settings → Actions → General
   - Select "Allow all actions and reusable workflows"
   - Click Save

3. **Verify activation**
   - Go to Actions tab
   - Look for "ESPN Data Collection" workflow
   - Should show "scheduled to run every Friday 9 AM UTC"

✅ **Done!** Collection runs automatically every Friday at 9 AM UTC.

### Option B: Manual Collection (This Week Only)

```bash
# Create necessary directories
mkdir -p data/archive/raw/{nfl,ncaaf}/{team_stats,injuries,schedules}/current
mkdir -p data/metrics/logs

# Collect NFL data (32 teams, ~1 minute)
uv run python scripts/dev/espn_production_orchestrator.py --league nfl

# Collect NCAAF data (136+ teams, ~2-3 minutes)
uv run python scripts/dev/espn_production_orchestrator.py --league ncaaf

# Verify collection
ls -la data/archive/raw/nfl/team_stats/current/
ls -la data/archive/raw/ncaaf/team_stats/current/
```

**Expected Output:**
```
[2025-11-23 15:30:12] ESPN DATA COLLECTION - NFL
[2025-11-23 15:30:15] [team_stats] Collected 32/32 teams (100%)
[2025-11-23 15:30:20] [injuries] Collected 47 injury records
[2025-11-23 15:30:25] [schedules] Collected 16 games
[2025-11-23 15:30:25] Status: ALL COMPONENTS SUCCESSFUL
```

---

## Step 2: Compare Spreads with ESPN Enhancement (5 min)

### Run Spread Comparison

```bash
# Compare ESPN vs Massey-only predictions
uv run python scripts/analysis/compare_espn_impact.py --league nfl --show-comparisons
```

**What This Shows:**
- Current NFL predictions using Massey-only ratings
- Same predictions with ESPN enhancement applied
- Impact of ESPN data on spread predictions
- Which games have the biggest ESPN adjustments

### Typical Output

```
================================================================================
ESPN IMPACT ANALYSIS REPORT
================================================================================
League:                    NFL
Games Analyzed:            16
Average Spread Delta:      +0.32 points
Max Spread Delta:          +2.1 points

Games with Edge Improvement: 9
Average Edge Improvement:  +0.58 points
Largest Improvement:       +1.85 points
Largest Degradation:       -0.92 points
Timestamp:                 2025-11-23T15:35:00

Top 10 Spread Changes:
────────────────────────────────────────────────────────────────────────────

Buffalo @ Kansas City
  Baseline: KC -5.8 (edge: +2.2 vs -8.0 line)
  Enhanced: KC -4.5 (edge: +3.5 vs -8.0 line) ↑+1.3
  Market:   KC -8.0

Denver @ Cleveland
  Baseline: Cleveland -2.1 (edge: -2.1 vs 0.0 line)
  Enhanced: Cleveland -3.2 (edge: -3.2 vs 0.0 line) ↓-1.1
  Market:   PK
```

**Key Insights:**
- ✅ **Edge Improvement** = ESPN made predictions better
- ⬇️ **Spread Delta** = How much ESPN changed the prediction
- 📊 **Market** = What oddsmakers are actually offering

---

## Step 3: Start Tracking Bets (5 min)

### Create CLV Tracking Database

```bash
# This directory stores your tracked bets
mkdir -p data/bets

# Create empty tracking file
touch data/bets/clv_database.jsonl
```

### Example: Track Your First Bet

Let's say you find an edge using ESPN data:

```bash
# Add a bet to tracking (manual entry for now)
# Format: game_id, matchup, selection, opening_line, bet_size

cat >> data/bets/clv_database.jsonl << 'EOF'
{"bet_id": "BET_001", "week": 12, "game_id": "buf_kc", "matchup": "Buffalo @ Kansas City", "bet_type": "Spread", "selection": "Buffalo", "opening_line": 8.0, "opening_price": -110.0, "bet_size": 2.0, "wager_timestamp": "2025-11-23T16:00:00Z", "edge_reason": "ESPN defensive metrics favor Buffalo", "espn_adjustment": +1.3}
EOF

echo "[OK] Bet BET_001 recorded"
```

### Update Bet During Week

```bash
# Thursday (closing line update)
# After checking Overtime.ag for latest line

cat >> data/bets/clv_database.jsonl << 'EOF'
{"bet_id": "BET_001", "closing_line": 7.5, "closing_price": -110.0, "closing_timestamp": "2025-11-27T20:00:00Z"}
EOF

echo "[OK] Closing line updated (line moved from -8.0 to -7.5)"
```

### Record Outcome

```bash
# Sunday after game completes

cat >> data/bets/clv_database.jsonl << 'EOF'
{"bet_id": "BET_001", "final_score_away": 27, "final_score_home": 24, "result": "WIN", "clv": 0.25, "cover": 4.0, "profit_loss": 2.0}
EOF

echo "[OK] Game result recorded - BET_001: WIN, CLV: +0.25"
```

---

## Understanding Your Results

### Spread Delta
- **What**: Change in predicted spread due to ESPN data
- **Good**: Small deltas (+/- 0.5 to 1.5) show ESPN refines predictions
- **Bad**: Large deltas (> 2.0) may indicate over-reliance on ESPN

### Edge Improvement
- **What**: Does ESPN-enhanced prediction create better edge vs market?
- **Good**: Positive edge improvement on most games
- **Bad**: Negative improvement means ESPN is diverging from market

### CLV (Closing Line Value)
- **What**: Did your opening line edge actually exist at closing?
- **Formula**: If you got +7.5 closing vs +8.0 opening, CLV = +0.5
- **Interpretation**:
  - Positive CLV = Market agreed with your analysis
  - Negative CLV = Market disagreed (may still win bet)
  - CLV is the TRUE success metric (not win%)

### Example CLV Calculation

```
Opening Line (your edge detection): Buffalo +8.0
Your bet size: 2.0 units at -110 odds
Closing Line (market at game time): Buffalo +7.5
Game outcome: Buffalo wins by 4 (covers +8.0, covers +7.5)

CLV Calculation:
- You identified edge at +8.0
- Market moved to +7.5 (0.5 points better for Buffalo)
- CLV = (7.5 - 8.0) = -0.5 for your side
- BUT: You still won the bet (4 points is > +8.0)
- Result: WIN with CLV of -0.5 (market disagreed, but you covered)

Billy Walters Success Metric:
- Average CLV > +0.5 = Professional level
- Average CLV > +1.0 = Elite level
- Focus on CLV, NOT on win%
```

---

## What's Happening Behind the Scenes

### The Data Pipeline

```
Friday 9 AM UTC
    ↓
ESPN Production Orchestrator runs automatically
    ├─ Collects 32 NFL teams
    ├─ Collects 136+ NCAAF teams
    ├─ Gets injury reports
    └─ Archives raw data
    ↓
data/archive/raw/{league}/team_stats/current/
    ↓
/edge-detector command loads ESPN data
    ├─ Baseline predictions (Massey-only)
    └─ Enhanced predictions (Massey + ESPN)
    ↓
Spread Comparisons generated automatically
    ├─ Shows edge changes
    ├─ Flags significant divergences
    └─ Recommends bet sizes (Kelly formula)
    ↓
You track bets and outcomes in data/bets/clv_database.jsonl
    ↓
CLV Tracker calculates performance
    ├─ Win rate
    ├─ CLV (key metric)
    └─ ROI
```

### ESPN Enhancement Formula

```python
Enhanced Rating = 0.9 * (Massey Rating) + 0.1 * (ESPN Adjustment)

ESPN Adjustment =
    (PPG - 28.5) * 0.15 +           # Offensive efficiency
    (28.5 - PAPG) * 0.15 +          # Defensive efficiency
    (Turnover Margin) * 0.30        # Ball security
```

**Example: Buffalo Bills Week 12**
```
Massey Rating: 18.5
PPG: 28.3 (avg: 28.5) → -0.03 adjustment
PAPG: 19.2 (avg: 28.5) → +1.43 adjustment
TO Margin: +4 → +1.20 adjustment

ESPN Adjustment = -0.03 + 1.43 + 1.20 = +2.60
Enhanced Rating = 0.9(18.5) + 0.1(2.60) = 16.65 + 0.26 = 16.91

Impact: Massey saw Buffalo at 18.5, ESPN enhancement shows 16.91
(More defensively strong than historical average)
```

---

## Common Questions

### Q: Where does ESPN data come from?

ESPN team statistics come from their public API at `https://www.espn.com/`. The production orchestrator collects:

- **Points Per Game (PPG)**: Offensive efficiency - how many points do they score?
- **Points Allowed Per Game (PAPG)**: Defensive efficiency - how many points do opponents score?
- **Turnover Margin**: Ball security - difference between takeaways and giveaways
- **Injury Reports**: Who's unavailable due to injury?
- **Game Schedules**: When and where games are played

### Q: How often is ESPN data updated?

- **Automatic**: Every Friday 9 AM UTC via GitHub Actions
- **Manual**: Anytime via `uv run python scripts/dev/espn_production_orchestrator.py`
- **Age cutoff**: Data is valid for 7 days before needing refresh

### Q: What if ESPN data is missing for a team?

Graceful degradation:
1. Try to load ESPN team stats from archive
2. If not available, use Massey-only rating
3. Log the failure (noted in metrics/logs)
4. Continue processing other teams

### Q: Can I run collection on demand?

Yes! Anytime you need:

```bash
# NFL only
uv run python scripts/dev/espn_production_orchestrator.py --league nfl

# NCAAF only
uv run python scripts/dev/espn_production_orchestrator.py --league ncaaf

# Both (default)
uv run python scripts/dev/espn_production_orchestrator.py --league both
```

### Q: How do I use this for actual betting?

1. ✅ Run `/edge-detector` on current games
2. ✅ Review spreads enhanced with ESPN data
3. ✅ Identify games with positive edge (predicted spread vs market line)
4. ✅ Place bet at opening line (capture the edge)
5. ✅ Track closing line
6. ✅ Record outcome
7. ✅ Monitor CLV (your success metric)

---

## This Week's Tasks

- [ ] Commit ESPN collection workflow (Step 1)
- [ ] Enable GitHub Actions in repository settings
- [ ] Run first manual collection (Step 2)
- [ ] Compare spreads with ESPN enhancement (Step 3)
- [ ] Create CLV tracking database (Step 3)
- [ ] Review ESPN roadmap document for next phases

---

## Files You're Interacting With

| File | Purpose | You Need To... |
|------|---------|----------------|
| `.github/workflows/espn-collection.yml` | Automated Friday collection | Commit & push |
| `scripts/dev/espn_production_orchestrator.py` | Runs ESPN data collection | Use manually if needed |
| `scripts/analysis/compare_espn_impact.py` | Generates spread comparisons | Run after collection |
| `data/bets/clv_database.jsonl` | Tracks your bets | Create & populate manually |
| `src/walters_analyzer/valuation/espn_integration.py` | ESPN enhancement logic | (No changes needed) |

---

## Next Steps After Quick Start

1. **Week 2-4**: Accumulate 20+ tracked bets
2. **Week 5-8**: Run backtesting analysis
3. **Month 2+**: Optimize weight formula
4. **Ongoing**: Monitor production CLV

See `docs/ESPN_ROADMAP_IMPLEMENTATION_2025.md` for full details.

---

## Support & Questions

- **NFL Week Detection**: `/current-week` command
- **Edge Detector**: `/edge-detector` command (ESPN integrated)
- **ESPN Issues**: Check `data/metrics/logs/` for error messages
- **Feature Requests**: Document in LESSONS_LEARNED.md

---

**Status**: Ready to activate immediately
**Estimated Time to First Results**: 15 minutes
**Estimated Time to 20 Tracked Bets**: 2-3 weeks
**Estimated Time to Statistical Validation**: 6-8 weeks
