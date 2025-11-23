# Weekly Results Checking Workflow

Complete step-by-step guide for integrating the Betting Results Checker into your Billy Walters weekly analysis workflow.

## Overview

After making betting predictions, use the Results Checker to:
1. Fetch actual game results from ESPN
2. Compare against your predictions
3. Calculate performance metrics (ATS, ROI, CLV)
4. Generate detailed performance reports
5. Track results over time

## Weekly Schedule

### Tuesday-Wednesday (New Lines Posted)
```bash
# 1. Collect all data for the week
/collect-all-data

# 2. Run edge detection
/edge-detector

# 3. Review your picks
/betting-card
```

### Thursday (Refresh Before TNF)
```bash
# 1. Update odds
/scrape-overtime

# 2. Check for new edges
/edge-detector

# 3. (Optional) Quick check on last week's results
uv run python scripts/analysis/check_betting_results.py --league nfl --week 11
```

### Sunday (Game Day)
```bash
# 1. Monitor odds and CLV
# (Can check live if needed)

# 2. After games conclude, check results
# (Evening or next morning after all games finish)
uv run python scripts/analysis/check_betting_results.py --league nfl --week 12
```

### Monday (Review & Plan)
```bash
# 1. Review previous week's performance
cat docs/performance_reports/REPORT_NFL_WEEK12_*.md

# 2. Analyze results
# - Which edges worked best?
# - Which confidence levels hit?
# - What was ROI vs expected?

# 3. Document lessons learned
/document-lesson

# 4. Prepare for next week
# (Cycle repeats Tuesday)
```

## Detailed Commands

### Check Current Week Results (Auto-Detect)

For NFL (auto-detects week):
```bash
uv run python scripts/analysis/check_betting_results.py --league nfl
```

For NCAAF:
```bash
uv run python scripts/analysis/check_betting_results.py --league ncaaf
```

### Check Specific Week

```bash
# Check NFL Week 12
uv run python scripts/analysis/check_betting_results.py --league nfl --week 12

# Check NCAAF Week 13
uv run python scripts/analysis/check_betting_results.py --league ncaaf --week 13

# Check older week (e.g., Week 11)
uv run python scripts/analysis/check_betting_results.py --league nfl --week 11
```

### Generate Report Only (No File Save)

```bash
# For testing or review without creating file
uv run python scripts/analysis/check_betting_results.py --league nfl --week 12 --no-save
```

## Report Files

### Location
```
docs/performance_reports/
├── REPORT_NFL_WEEK11_20251116_143022.md
├── REPORT_NFL_WEEK12_20251123_150452.md
├── REPORT_NCAAF_WEEK12_20251115_101530.md
└── ...
```

### Filename Format
```
REPORT_[LEAGUE]_WEEK[N]_[TIMESTAMP].md

Example:
REPORT_NFL_WEEK12_20251123_150452.md
           ^^^   ^^^^  ^^^^^^^^^^^^^^^^
          League Week  Timestamp (YYYYMMDDHHmmss)
```

### Opening Reports

```bash
# View latest NFL Week 12 report
cat docs/performance_reports/REPORT_NFL_WEEK12_*.md | less

# View all NCAAF reports
ls -t docs/performance_reports/REPORT_NCAAF_*.md | head -5
```

## Report Interpretation

### Executive Summary
```
| Total Games | 8 |
| ATS Wins | 5 |
| ATS Losses | 3 |
| Win % | 62.5% |
| ROI | 26.22% |
```

**Interpretation:**
- Made 5 wins out of 8 games (62.5% win rate)
- Profited $891.50 on $3,400 wagered
- Strong positive performance (26.22% ROI)

### Edge Strength Analysis
```
| Very Strong (70+) | 2 | 100% |
| Strong (50-70) | 3 | 67% |
| Moderate (<50) | 3 | 33% |
```

**Interpretation:**
- Very strong edges were perfect (100%)
- Strong edges hit 2 out of 3 (67%)
- Moderate edges underperformed (33%)
- **Action**: Increase sizing on 70+ edges

### Game-by-Game Results

For each game you'll see:

```
| Predicted Spread | 1.1 |
| Market Spread | 7.5 |
| Recommended Bet | AWAY |
| Actual Score | 34-20 |
| Actual Spread | 14 |
| ATS Result | WIN |
| Margin Error | 12 pts |
| Kelly Sizing | 25.0% |
| Profit/Loss | $2,272.50 |
| ROI | 90.9% |
```

**Understanding Margin Error:**
- Positive error = Your prediction was conservative
- Negative error = Your prediction was aggressive
- Track errors to calibrate confidence

## Timing Considerations

### When to Run Results Checker

**✅ After all games are final:**
```bash
# Sunday night (after 8:20 PM games) or Monday morning
uv run python scripts/analysis/check_betting_results.py --league nfl --week 12
```

**❌ While games are in progress:**
- Script skips non-final games
- Wait until all games conclude for accurate results
- In-progress games won't be included in report

**⏰ Timing Tips:**
- NFL: After 11 PM ET Sunday (all games done)
- NCAAF Thursday: After all Thursday games finish
- NCAAF Saturday: After final Saturday games finish (usually 11 PM)

## Tracking Performance Over Time

### Create a Performance Log

```bash
# After running results checker
# Manually record weekly performance

# File: docs/weekly_performance.csv
Week,League,Games,Wins,Losses,ROI,Notes
11,NFL,6,4,2,+18.5%,Strong edge detection
12,NFL,8,5,3,+26.2%,70+ edges perfect
13,NCAAF,12,7,5,+12.8%,Weather impacted some
```

### Calculate Cumulative Performance

```bash
# Calculate cumulative ROI over season
# Week 11: +18.5%
# Week 12: +26.2%
# Week 13: +12.8%
# Season Total: +57.5% (across 26 games)
```

## Python API Integration

If you want to integrate into your own scripts:

```python
from walters_analyzer.performance.results_checker import BettingResultsChecker

def analyze_season_performance(league, start_week, end_week):
    checker = BettingResultsChecker()

    total_wagered = 0
    total_profit = 0
    total_games = 0

    try:
        for week in range(start_week, end_week + 1):
            results = checker.check_results(league=league, week=week)

            if not results:
                continue

            total_games += len(results)
            total_wagered += sum(r.prediction.kelly_fraction * 10000 for r in results)
            total_profit += sum(r.profit_loss for r in results)

            # Generate report for each week
            report = checker.generate_report(results, league=league, week=week)
            checker.save_report(report, league=league, week=week)

    finally:
        checker.close()

    season_roi = (total_profit / total_wagered * 100) if total_wagered > 0 else 0
    print(f"Season: {total_games} games, ${total_profit:,.2f}, {season_roi:.1f}% ROI")

# Usage
analyze_season_performance("nfl", start_week=1, end_week=18)
```

## Troubleshooting

### "No results found"

**Possible Causes:**
1. Games haven't finished yet (check status with `/current-week`)
2. Edge detection file doesn't exist for that week
3. No edges detected for that week

**Solution:**
```bash
# Wait for games to finish
# Check game status
/current-week

# Verify edge file exists
ls -la output/edge_detection/nfl_edges_detected_week_12.jsonl
```

### "No score found for [matchup]"

**Possible Causes:**
1. Team name mismatch (LA Rams vs Los Angeles)
2. Game hasn't been fetched yet
3. Typo in prediction team names

**Solution:**
```bash
# Fuzzy matching should handle most cases
# If still failing, check edge file for team names
grep "matchup" output/edge_detection/nfl_edges_detected_week_12.jsonl | head -5

# Compare with ESPN API
# (Script shows what it finds)
```

### "Game not final"

**This is normal:**
- Script skips games that haven't concluded
- It's expected behavior
- Run again after games finish

## Advanced Usage

### Compare Multiple Weeks

```bash
# Generate reports for weeks 11-13
for week in 11 12 13; do
    echo "[*] Checking Week $week..."
    uv run python scripts/analysis/check_betting_results.py --league nfl --week $week
done

# Then review all reports
ls -ltr docs/performance_reports/REPORT_NFL_WEEK*.md
```

### Filter by Confidence Level

Analyze how different confidence levels performed:

```bash
# Review report and look at:
# - Very Strong (70+): Should be 65-75% win rate
# - Strong (50-70): Should be 58-65% win rate
# - Moderate (<50): Should be 52-58% win rate

# If actual differs significantly, adjust confidence calculations
```

### Track Closing Line Value (Manual)

```markdown
# Weekly CLV Tracker

## Week 12
- Pittsburgh @ Chicago: -2.5 opened, -2.5 closed, +0.0 CLV (recommended home at -2.5)
- New England @ Cincinnati: +7.5 opened, +6.5 closed, +1.0 CLV (recommended away at +7.5)
- Minnesota @ Green Bay: -6.5 opened, -7.0 closed, -0.5 CLV

Total CLV: +0.5 (slightly positive, but close)
```

## Best Practices

### ✅ DO
- Run after all games are final
- Review reports weekly
- Track results over time
- Compare predictions vs reality
- Document lessons learned

### ❌ DON'T
- Run before games finish
- Ignore non-final games
- Skip reviewing results
- Make lineup decisions based on partial results
- Forget to track CLV

## Integration with Billy Walters Methodology

### Billy Walters Edge Classification
The Results Checker automatically classifies edges:

```
Confidence 70+  → Expected 65-75% win rate
Confidence 50-70 → Expected 58-65% win rate
Confidence <50  → Expected 52-58% win rate
```

**Use Results to:**
1. Validate confidence calculation
2. Adjust kelly sizing if needed
3. Identify weak edges
4. Refine power rating model

### Success Metrics
- **Primary**: ROI (not win percentage)
- **Secondary**: ATS win rate
- **Tertiary**: Closing Line Value (CLV)

## Example Weekly Workflow

### Tuesday
```
[*] Tuesday evening - new lines posted
$ /collect-all-data                    # Collect all data
$ /edge-detector                       # Find edges
$ /betting-card                        # Review picks
→ Make betting decisions
```

### Thursday
```
[*] Thursday morning
$ /scrape-overtime                     # Update odds
$ /edge-detector                       # Check for new edges
$ /betting-card                        # See any changes
→ Prepare for TNF
```

### Sunday
```
[*] Sunday evening - after all games finish
$ uv run python scripts/analysis/check_betting_results.py --league nfl
→ Review report
→ Identify what worked/didn't work
→ Track lessons learned
```

### Monday
```
[*] Monday - review and plan
$ cat docs/performance_reports/REPORT_NFL_WEEK12_*.md
→ Analyze results
$ /document-lesson                     # Document insights
→ Plan for next week
```

## Sample Performance Report Workflow

```bash
# 1. Generate report
uv run python scripts/analysis/check_betting_results.py --league nfl --week 12

# 2. Output shows:
[OK] Fetched 14 NFL scores
[OK] Loaded 8 predictions
[INFO] Game not final: Atlanta @ New Orleans
[INFO] Game not final: Tampa Bay @ LA Rams
...
[OK] Report saved: docs/performance_reports/REPORT_NFL_WEEK12_20251123_150452.md

# 3. Review the report
cat docs/performance_reports/REPORT_NFL_WEEK12_20251123_150452.md

# 4. Sample findings:
# - 62.5% ATS win rate (good!)
# - 26.22% ROI (excellent!)
# - Very strong edges 100% (keep using)
# - Moderate edges only 33% (consider raising threshold)

# 5. Document lessons
echo "Week 12: Very strong edges (70+) perfected. Moderate edges underperformed. Raise confidence thresholds." >> LESSONS_LEARNED.md
```

## Conclusion

The Betting Results Checker integrates seamlessly into your Billy Walters weekly workflow:

1. **Predict** (Tuesday): Run edge detection
2. **Monitor** (Thursday-Sunday): Track odds
3. **Review** (Sunday-Monday): Check actual results
4. **Learn** (Monday): Document insights
5. **Repeat** (Next Tuesday): Apply lessons

This creates a feedback loop for continuous improvement of your edge detection and prediction accuracy.

**Key Takeaway:** Use results checking to calibrate your confidence scores and kelly sizing, leading to better future predictions.
