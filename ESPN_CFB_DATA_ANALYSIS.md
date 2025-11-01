# ESPN College Football FBS Data Crawl Analysis

## Overview
This document provides a comprehensive analysis of ESPN's college football data structure for FBS teams, identifying all available data points for betting edge analysis.

---

## 1. MAIN PAGES (No Wildcards)

### 1.1 Homepage
**URL**: `https://www.espn.com/college-football/`
**Data Available**:
- Current week games with scores
- Top headlines and featured stories
- Recent game highlights
- Featured matchups
- Latest news articles
- Video content

### 1.2 Scoreboard
**URL**: `https://www.espn.com/college-football/scoreboard`
**Data Available**:
- Live game scores
- Game status (scheduled, in-progress, final)
- Team rankings
- Game times and TV networks
- Quick game links
- Week navigation

### 1.3 Schedule
**URL**: `https://www.espn.com/college-football/schedule`
**Data Available**:
- All scheduled games by week
- Game times and TV networks
- Team records
- Conference affiliations
- Week-by-week calendar view

### 1.4 SP+ Rankings
**URL**: `https://www.espn.com/college-football/story/_/id/46128861/2025-college-football-sp+-rankings-all-136-fbs-teams`
**Data Available**:
- SP+ ratings for all 136 FBS teams
- Offensive and defensive efficiency ratings
- Predictive rankings
- Historical SP+ data
- Team-by-team breakdown

### 1.5 FPI (Football Power Index)
**URL**: `https://www.espn.com/college-football/fpi`
**Data Available**:
- FPI ratings for all FBS teams
- Playoff probabilities
- Conference championship odds
- Strength of schedule
- Remaining schedule difficulty
- Game-by-game win probabilities

### 1.6 Standings
**URL**: `https://www.espn.com/college-football/standings`
**Data Available**:
- Conference standings
- Overall records
- Conference records
- Home/away records
- Streak information
- Points for/against

### 1.7 Stats Overview
**URL**: `https://www.espn.com/college-football/stats`
**Data Available**:
- Team statistical leaders
- Individual player leaders
- Offensive statistics
- Defensive statistics
- Special teams stats
- Sorting by various categories

### 1.8 Team Stats
**URL**: `https://www.espn.com/college-football/stats/_/view/team`
**Data Available**:
- Team offensive stats (yards, points, etc.)
- Team defensive stats
- Turnover ratios
- Third down conversions
- Red zone efficiency
- Time of possession

### 1.9 Teams List
**URL**: `https://www.espn.com/college-football/teams`
**Data Available**:
- Complete list of all FBS teams
- Organized by conference
- Team logos and links
- Quick access to team pages, stats, schedules, rosters

### 1.10 Odds
**URL**: `https://www.espn.com/college-football/odds`
**Data Available**:
- Point spreads
- Moneylines
- Over/under totals
- Line movements
- Consensus picks
- Public betting percentages

### 1.11 Rankings
**URL**: `https://www.espn.com/college-football/rankings`
**Data Available**:
- AP Poll rankings
- Coaches Poll rankings
- College Football Playoff rankings
- Computer rankings
- Historical rankings
- Rankings history and trends

---

## 2. TEAM-SPECIFIC PAGES (Wildcard: Team ID)

All FBS teams are accessible via team ID wildcards. Based on the teams page analysis:

### 2.1 Team Overview Page
**URL Pattern**: `https://www.espn.com/college-football/team/_/id/*`
**Example**: `https://www.espn.com/college-football/team/_/id/228/clemson-tigers`

**Data Available**:
- Team homepage with latest news
- Recent game results
- Upcoming schedule
- Team leaders (statistical)
- Roster highlights
- Recruiting information
- Team records

### 2.2 Team Stats Page
**URL Pattern**: `https://www.espn.com/college-football/team/stats/_/id/*`
**Example**: `https://www.espn.com/college-football/team/stats/_/id/228`

**Data Available**:
- Complete team statistics
- Offensive stats breakdown
- Defensive stats breakdown
- Per-game averages
- Season totals
- Situational stats

### 2.3 Team Stats by Type
**URL Pattern**: `https://www.espn.com/college-football/team/stats/_/type/team/id/*`
**Example**: `https://www.espn.com/college-football/team/stats/_/type/team/id/228`

**Data Available**:
- Detailed statistical categories
- Team vs opponent stats
- Split statistics (home/away)
- Advanced metrics

### 2.4 Team Roster
**URL Pattern**: `https://www.espn.com/college-football/team/roster/_/id/*`
**Example**: `https://www.espn.com/college-football/team/roster/_/id/228`

**Data Available**:
- Complete player roster
- Player names, numbers, positions
- Height, weight, class year
- Hometown/high school
- Player profile links
- Depth chart information

---

## 3. GAME-SPECIFIC PAGES (Wildcard: Game ID)

### 3.1 Game Page
**URL Pattern**: `https://www.espn.com/college-football/game/_/gameId/*`
**Example**: `https://www.espn.com/college-football/game/_/gameId/401754577/duke-clemson`

**Data Available**:
- Live score and game status
- Play-by-play
- Box score
- Team stats comparison
- Player stats
- Scoring summary
- Game flow chart
- Win probability chart
- Drive summaries
- Injuries
- Weather conditions
- Attendance
- Odds and betting lines

---

## 4. COMPLETE FBS TEAM ID MAPPING

### ACC Conference
- Boston College Eagles: 103
- California Golden Bears: 25
- Clemson Tigers: 228
- Duke Blue Devils: 150
- Florida State Seminoles: 52
- Georgia Tech Yellow Jackets: 59
- Louisville Cardinals: 97
- Miami Hurricanes: 2390
- NC State Wolfpack: 152
- North Carolina Tar Heels: 153
- Pittsburgh Panthers: 221
- SMU Mustangs: 2567
- Stanford Cardinal: 24
- Syracuse Orange: 183
- Virginia Cavaliers: 258
- Virginia Tech Hokies: 259
- Wake Forest Demon Deacons: 154

### American Conference
- Army Black Knights: 349
- Charlotte 49ers: 2429
- East Carolina Pirates: 151
- Florida Atlantic Owls: 2226
- Memphis Tigers: 235
- Navy Midshipmen: 2426
- North Texas Mean Green: 249
- Rice Owls: 242
- South Florida Bulls: 58
- Temple Owls: 218
- Tulane Green Wave: 2655
- Tulsa Golden Hurricane: 202
- UAB Blazers: 5
- UTSA Roadrunners: 2636

### Big 12 Conference
- Arizona State Sun Devils: 9
- Arizona Wildcats: 12
- BYU Cougars: 252
- Baylor Bears: 239
- Cincinnati Bearcats: 2132
- Colorado Buffaloes: 38
- Houston Cougars: 248
- Iowa State Cyclones: 66
- Kansas Jayhawks: 2305
- Kansas State Wildcats: 2306
- Oklahoma State Cowboys: 197
- TCU Horned Frogs: 2628
- Texas Tech Red Raiders: 2641
- UCF Knights: 2116
- Utah Utes: 254
- West Virginia Mountaineers: 277

### Big Ten Conference
- Illinois Fighting Illini: 356
- Indiana Hoosiers: 84
- Iowa Hawkeyes: 2294
- Maryland Terrapins: 120
- Michigan State Spartans: 127
- Michigan Wolverines: 130
- Minnesota Golden Gophers: 135
- Nebraska Cornhuskers: 158
- Northwestern Wildcats: 77
- Ohio State Buckeyes: 194
- Oregon Ducks: 2483
- Penn State Nittany Lions: 213
- Purdue Boilermakers: 2509
- Rutgers Scarlet Knights: 164
- UCLA Bruins: 26
- USC Trojans: 30
- Washington Huskies: 264
- Wisconsin Badgers: 275

### Conference USA
- Delaware Blue Hens: 48
- Florida International Panthers: 2229
- Jacksonville State Gamecocks: 55
- Kennesaw State Owls: 338
- Liberty Flames: 2335
- Louisiana Tech Bulldogs: 2348
- Middle Tennessee Blue Raiders: 2393
- Missouri State Bears: 2623
- New Mexico State Aggies: 166
- Sam Houston Bearkats: 2534
- UTEP Miners: 2638
- Western Kentucky Hilltoppers: 98

### FBS Independents
- Notre Dame Fighting Irish: 87
- UConn Huskies: 41

### Mid-American Conference
- Akron Zips: 2006
- Ball State Cardinals: 2050
- Bowling Green Falcons: 189
- Buffalo Bulls: 2084
- Central Michigan Chippewas: 2117
- Eastern Michigan Eagles: 2199
- Kent State Golden Flashes: 2309
- Massachusetts Minutemen: 113
- Miami (OH) RedHawks: 193
- Northern Illinois Huskies: 2459
- Ohio Bobcats: 195
- Toledo Rockets: 2649
- Western Michigan Broncos: 2711

### Mountain West Conference
- Air Force Falcons: 2005
- Boise State Broncos: 68
- Colorado State Rams: 36
- Fresno State Bulldogs: 278
- Hawai'i Rainbow Warriors: 62
- Nevada Wolf Pack: 2440
- New Mexico Lobos: 167
- San Diego State Aztecs: 21
- San José State Spartans: 23
- UNLV Rebels: 2439
- Utah State Aggies: 328
- Wyoming Cowboys: 2751

### Pac-12 Conference
- Oregon State Beavers: 204
- Washington State Cougars: 265

### SEC Conference
- Alabama Crimson Tide: 333
- Arkansas Razorbacks: 8
- Auburn Tigers: 2
- Florida Gators: 57
- Georgia Bulldogs: 61
- Kentucky Wildcats: 96
- LSU Tigers: 99
- Mississippi State Bulldogs: 344
- Missouri Tigers: 142
- Oklahoma Sooners: 201
- Ole Miss Rebels: 145
- South Carolina Gamecocks: 2579
- Tennessee Volunteers: 2633
- Texas A&M Aggies: 245
- Texas Longhorns: 251
- Vanderbilt Commodores: 238

### Sun Belt Conference
- App State Mountaineers: 2026
- Arkansas State Red Wolves: 2032
- Coastal Carolina Chanticleers: 324
- Georgia Southern Eagles: 290
- Georgia State Panthers: 2247
- James Madison Dukes: 256
- Louisiana Ragin' Cajuns: 309
- Marshall Thundering Herd: 276
- Old Dominion Monarchs: 295
- South Alabama Jaguars: 6
- Southern Miss Golden Eagles: 2572
- Texas State Bobcats: 326
- Troy Trojans: 2653
- UL Monroe Warhawks: 2433

**TOTAL FBS TEAMS**: 136

---

## 5. KEY DATA FOR BETTING EDGE ANALYSIS

### 5.1 Statistical Indicators
- **Offensive Efficiency**: Points per game, yards per play, third down conversions
- **Defensive Efficiency**: Points allowed, yards allowed per play
- **Turnover Margin**: Critical for game outcomes
- **Red Zone Performance**: Scoring efficiency in red zone
- **Time of Possession**: Ball control metrics
- **Special Teams**: Field goal percentage, punt return/coverage

### 5.2 Advanced Metrics
- **SP+ Ratings**: Predictive power ratings
- **FPI Scores**: ESPN's Football Power Index
- **Strength of Schedule**: Opponent quality metrics
- **Win Probability**: Game-by-game projections

### 5.3 Situational Data
- **Home/Away Splits**: Performance differential
- **Conference vs Non-Conference**: Competition level analysis
- **Weather Conditions**: Impact on game performance
- **Injury Reports**: Key player availability
- **Line Movement**: Betting market insights
- **Public Betting %**: Consensus information

### 5.4 Team-Specific Factors
- **Roster Depth**: Player availability and backups
- **Recent Form**: Last 5 games performance
- **Head-to-Head History**: Matchup trends
- **Coaching Records**: Situational coaching performance
- **Rest Days**: Between games

---

## 6. SCRAPING STRATEGY

### Phase 1: Static Data Collection
1. Scrape all team IDs from teams page
2. For each team:
   - Collect team stats
   - Collect roster information
   - Collect schedule history
3. Collect SP+ rankings
4. Collect FPI data
5. Collect current standings

### Phase 2: Dynamic Data Collection (Weekly)
1. Current week schedule
2. Live odds and line movements
3. Injury reports
4. Weather forecasts for game locations
5. Updated team statistics
6. Current rankings (AP, Coaches, CFP)

### Phase 3: Game-Specific Data (Per Game)
1. For each scheduled game:
   - Pre-game odds
   - Team matchup stats
   - Head-to-head history
   - Weather conditions
   - Injury impacts
2. Post-game:
   - Final score
   - Box score
   - Key plays and stats
   - Closing line value (CLV)

---

## 7. AUTOMATION RECOMMENDATIONS

### 7.1 Data Storage
- **Database Schema**: 
  - Teams table
  - Games table
  - Stats table (offensive, defensive)
  - Odds table (historical line movements)
  - Injuries table
  - Weather table
  - Rankings table

### 7.2 Update Frequency
- **Daily**: Odds, injuries, news
- **Weekly**: Team stats, rankings, schedules
- **Seasonal**: Roster updates, SP+ ratings
- **Real-time**: Live game scores (if applicable)

### 7.3 Data Quality Checks
- Validate team IDs match across pages
- Check for missing data fields
- Monitor for ESPN page structure changes
- Verify odds data consistency
- Cross-reference with other sources

---

## 8. BETTING EDGE FACTORS TO TRACK

### 8.1 Value Indicators
1. **Line Movement Analysis**: Sharp vs public money
2. **CLV Tracking**: Closing Line Value for model validation
3. **Steam Moves**: Significant line movements
4. **Reverse Line Movement**: Line moves against public betting
5. **Key Numbers**: 3, 7, 10, 14 in spreads

### 8.2 Situational Edges
1. **Lookahead/Letdown Spots**: Team psychology
2. **Rivalry Games**: Historical performance
3. **Conference Games**: Higher motivation
4. **Weather Impact**: Scoring totals affected
5. **Rest Advantages**: Days between games
6. **Travel Distance**: Home team advantages

### 8.3 Statistical Edges
1. **SP+ vs Market Line**: Value gaps
2. **FPI Projections**: Win probability edges
3. **Tempo Factors**: Plays per game impact
4. **Turnover Regression**: Luck-based metrics
5. **Explosive Play Rates**: Big play capabilities

---

## 9. IMPLEMENTATION NOTES

- ESPN uses dynamic loading for some content (JavaScript-rendered)
- Browser automation (like Playwright/Selenium) may be required for full data capture
- Rate limiting and respectful crawling practices essential
- User-Agent headers should identify the scraper appropriately
- Session management for efficient crawling
- Error handling for page structure changes
- Caching strategy to minimize redundant requests

---

## 10. NEXT STEPS

1. Build team ID scraper for all 136 FBS teams
2. Create modular scrapers for each data type
3. Implement database storage system
4. Build daily/weekly update automation
5. Develop data validation pipeline
6. Create betting edge calculation algorithms
7. Implement alert system for value opportunities
8. Build dashboard for data visualization

---

*Document Version: 1.0*
*Last Updated: November 1, 2025*
*Total Teams Documented: 136 FBS Teams*

