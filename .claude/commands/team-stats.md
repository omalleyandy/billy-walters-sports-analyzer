Fetch and analyze team statistics for NFL/NCAAF teams.

Usage: /team-stats [team_name] [league]

Examples:
- /team-stats "Kansas City Chiefs" nfl
- /team-stats "Georgia Bulldogs" ncaaf
- /team-stats "Buffalo" nfl

This command will:
1. Fetch current season team statistics from ESPN API
2. Parse offensive and defensive performance metrics
3. Calculate key Billy Walters analytics (rushing vs passing efficiency)
4. Compare team stats against league averages
5. Identify statistical edges and weaknesses

NFL Statistics Retrieved:
- Points per game (offense/defense)
- Total yards per game
- Passing yards per game
- Rushing yards per game
- Turnovers (given/taken)
- Third down conversion rate
- Red zone efficiency
- Time of possession
- Sacks (offensive line protection / defensive pressure)

NCAAF Statistics Retrieved:
- Points per game (offense/defense)
- Total offense/defense yards
- Rushing vs passing balance
- Turnover margin
- Third/fourth down conversions
- Red zone scoring percentage
- Home vs away splits
- Conference record

Billy Walters Analytics:
- Offensive power rating components
- Defensive power rating components
- Situational performance (home/away, conference)
- Injury-adjusted performance trends
- Weather-dependent performance (outdoor teams)
- Strength of schedule adjustments

Output includes:
- Team overview (record, ranking, conference)
- Offensive statistics with league rank
- Defensive statistics with league rank
- Key statistical edges
- Billy Walters power rating factors
- Betting insights based on statistical profile
