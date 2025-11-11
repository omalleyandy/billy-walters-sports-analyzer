Fetch and update power ratings for all NFL teams.

Usage: /power-ratings [week] [source]

Examples:
- /power-ratings (current week, all sources)
- /power-ratings 11 massey
- /power-ratings 11 all

This command will:
1. Scrape Massey Ratings for current NFL power ratings
2. Update team power ratings based on Billy Walters 90/10 formula
3. Adjust for off-season changes (draft picks, coaching, free agency)
4. Calculate predicted spreads based on power differential
5. Store ratings in database for historical tracking

Billy Walters Power Rating System:
- Scale: 70-100 (average team = 85)
- Elite teams: 90-100 (Chiefs, Bills, 49ers)
- Good teams: 85-89
- Average teams: 80-85
- Below average: 75-79
- Poor teams: 70-74

Update Formula (90/10 Rule):
- New Rating = (0.90 × Old Rating) + (0.10 × Current Performance)
- Accounts for regression to mean while incorporating recent performance
- Prevents overreaction to single game results

Off-Season Adjustments:
- Draft picks: +0.5 to +2.0 points per high-value pick
- Coaching changes: -1.0 to +1.6 points
- Free agency acquisitions: +0.5 to +1.8 points per key player
- Free agency losses: -0.5 to -3.9 points per key departure
- Player development: +0.5 to +2.2 points for expected improvement

Data Sources:
- Massey Ratings (composite of 100+ ranking systems)
- ESPN Power Rankings
- Sagarin Ratings
- Custom Billy Walters formula

Output includes:
- Current power rating for each team
- Week-over-week change
- Offensive rating component
- Defensive rating component
- Special teams adjustment
- Home field advantage value (team-specific)
- Predicted spread vs average opponent
- Confidence interval
