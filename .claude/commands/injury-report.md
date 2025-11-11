Fetch and analyze injury reports with Billy Walters point value impact calculations.

Usage: /injury-report [team_name] [league]

Examples:
- /injury-report "Kansas City Chiefs" nfl
- /injury-report "Georgia Bulldogs" ncaaf
- /injury-report nfl (all teams)

This command will:
1. Fetch current injury reports from ESPN API
2. Parse player injury status and descriptions
3. Calculate Billy Walters point value impact for each injury
4. Assess team-level injury severity
5. Provide betting adjustments based on injuries

Injury Status Types:
- OUT: Player will not play (100% impact)
- DOUBTFUL: Unlikely to play (75-90% impact)
- QUESTIONABLE: May or may not play (8-25% impact)
- PROBABLE: Likely to play (2-8% impact)
- Injured Reserve (IR): Out for season

Billy Walters Position Value System:
- QB: 6-9 points (elite QBs up to 12 points)
- RB (workhorse): 3-4 points
- WR (WR1): 2-3 points
- OL (Pro Bowl): 1.5-2 points per starter
- Edge rusher: 2-3 points
- CB (shutdown): 1.5-2 points
- MLB: 1-1.5 points

Injury Type Impact Multipliers:
- ACL/Achilles: Season-ending, 100% impact
- High ankle sprain: 6-8 weeks, 80-100% immediate impact
- Hamstring: 2-4 weeks, 50-75% immediate impact, lingering effects
- Concussion: Protocol dependent, 30-50% immediate impact
- Shoulder (throwing): 40-60% impact for QB/WR
- Knee sprain: 30-50% impact, position-dependent
- Ankle sprain: 20-40% impact, recovery timeline varies

Recovery Timeline Tracking:
- Immediate impact: First week after injury
- Recovery phase: Progressive improvement
- Lingering effects: 2 weeks post-recovery
- Re-injury risk: 30 days elevated risk period

Output includes:
- Complete injury list by team
- Player-by-player point value impact
- Position-specific analysis
- Total team injury impact (points)
- Injury severity rating (CRITICAL/MAJOR/MODERATE/MINOR)
- Confidence level for impact assessment
- Betting recommendations:
  - Spread adjustment
  - Total adjustment
  - Key player dependencies
- Historical injury trends for team

Billy Walters Injury Analysis Principles:
1. Value key positions heavily (QB, OL, Edge)
2. Account for depth chart quality (backup impact)
3. Consider injury timing (fresh vs late season)
4. Factor in recovery timelines
5. Adjust for re-injury risk
6. Weight situational performance (home/away)
7. Consider opponent's ability to exploit weakness
