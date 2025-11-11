Scrape Massey Ratings for NFL/NCAAF power ratings.

Usage: /scrape-massey [sport] [season]

Examples:
- /scrape-massey nfl (current season)
- /scrape-massey ncaaf 2025
- /scrape-massey both

This command will:
1. Scrape Massey Ratings composite rankings
2. Extract team power ratings (70-100 scale)
3. Parse offensive and defensive sub-ratings
4. Calculate schedule strength
5. Store historical ratings for trend analysis

Massey Ratings Benefits:
- Composite of 100+ ranking systems
- Statistical aggregation reduces bias
- Updated daily during season
- Historical data back to 1997
- Free public access

Billy Walters Usage:
- Starting point for preseason power ratings
- Weekly validation against own ratings
- Identification of rating discrepancies
- Market inefficiency detection

Data Retrieved:
- Overall team rating (70-100 scale)
- Offensive rating
- Defensive rating
- Special teams rating
- Schedule strength (past and future)
- Conference rank
- National rank
- Rating trend (up/down arrows)

Output Format:
```json
{
  "sport": "NFL",
  "season": 2025,
  "updated": "2025-11-13T14:30:00",
  "source": "Massey Ratings",
  "teams": [
    {
      "name": "Kansas City Chiefs",
      "rating": 92.5,
      "rank": 1,
      "offense": 94.2,
      "defense": 91.8,
      "schedule_strength": 0.52,
      "conference_rank": 1,
      "trend": "up"
    },
    ...
  ]
}
```

Saved to: data/current/massey_ratings_nfl_2025.json

Integration:
- First step in Billy Walters workflow
- Feeds into power rating calculator
- Historical tracking for regression analysis
