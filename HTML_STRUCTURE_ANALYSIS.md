# overtime.ag HTML Structure Analysis

## ✅ Successfully Scraped Page!

**Status**: Page loaded correctly, CloudFlare bypass successful
**Data Present**: Yes - NFL Week 11 games visible
**Next Step**: Implement parsing logic

---

## HTML Structure Discovered

### Game Container

```html
<div ng-repeat="league in Selections">
    <span class="game_line_comments">NFL WEEK 11 (BYES: INDIANAPOLIS, NEW ORLEANS)</span>
    
    <!-- Each game has two rows: Team2 (away) and Team1 (home) -->
    <div class="row">
        <!-- Team2 (Away Team) -->
        <div class="col-sm-5">
            <img src="/sports/assets_core/sport_types/Buffalo_Bills.png">
            <span class="line-rot-num">456</span>
            <span>Buffalo Bills</span>
        </div>
        
        <!-- Odds for Away Team -->
        <div class="col-sm-7">
            <!-- Spread -->
            <offering-button bind="gameLine.Spread2" sub-type="S">
                <span>-6  -110</span>
            </offering-button>
            
            <!-- Moneyline -->
            <offering-button bind="gameLine.MoneyLine2" sub-type="M">
                <span>-275</span>
            </offering-button>
            
            <!-- Total -->
            <offering-button bind="gameLine.TotalPoints" sub-type="L">
                <span>O 43½  -110</span>
            </offering-button>
        </div>
    </div>
</div>
```

### Key Elements Found

**Team Information**:
- Team Name: `<span ng-bind="Translate(gameLine.Team2ID)">Buffalo Bills</span>`
- Rotation Number: `<span class="line-rot-num">456</span>`
- Team Logo: `<img ng-src="/sports/assets_core/sport_types/Buffalo_Bills.png">`

**Betting Lines**:
- Spread: `<span ng-bind="bind | formatLine">-6  -110</span>` (inside `<offering-button sub-type="S">`)
- Moneyline: `<span ng-bind="bind | formatLine">-275</span>` (inside `<offering-button sub-type="M">`)
- Total: `<span ng-bind="bind | formatLine">O 43½  -110</span>` (inside `<offering-button sub-type="L">`)

**Team Totals** (separate view):
- Team1 Total: `<span>O 21½  +110</span>`
- Team2 Total: `<span>U 21½  -130</span>`

---

## Parsing Strategy

### Option 1: Playwright Selector-Based (Recommended)

**Why**: AngularJS has fully rendered the content, so we can use Playwright selectors

```python
async def parse_nfl_games(page: Page) -> List[BettingLine]:
    games = []
    
    # Wait for games to load
    await page.wait_for_selector('.game_line_comments', timeout=10000)
    
    # Get all game containers
    game_rows = await page.query_selector_all('.row')
    
    for row in game_rows:
        try:
            # Extract team name
            team_elem = await row.query_selector('span.ng-binding')
            if not team_elem:
                continue
            team_name = await team_elem.inner_text()
            
            # Extract rotation number
            rot_elem = await row.query_selector('.line-rot-num')
            rot_num = await rot_elem.inner_text() if rot_elem else None
            
            # Extract spread
            spread_btn = await row.query_selector('offering-button[sub-type="S"] span.ng-binding')
            spread_text = await spread_btn.inner_text() if spread_btn else None
            
            # Extract moneyline
            ml_btn = await row.query_selector('offering-button[sub-type="M"] span.ng-binding')
            ml_text = await ml_btn.inner_text() if ml_btn else None
            
            # Extract total
            total_btn = await row.query_selector('offering-button[sub-type="L"] span.ng-binding')
            total_text = await total_btn.inner_text() if total_btn else None
            
            # Parse and create BettingLine object
            if spread_text and ml_text:
                game = parse_betting_line(team_name, rot_num, spread_text, ml_text, total_text)
                games.append(game)
                
        except Exception as e:
            print(f"Error parsing row: {e}")
            continue
    
    return games
```

### Option 2: BeautifulSoup HTML Parsing (Alternative)

```python
from bs4 import BeautifulSoup

def parse_html_content(html: str) -> List[BettingLine]:
    soup = BeautifulSoup(html, 'html.parser')
    games = []
    
    # Find all game containers
    game_containers = soup.find_all('div', {'ng-repeat': re.compile('league in Selections')})
    
    for container in game_containers:
        # Extract team names
        teams = container.find_all('span', class_='ng-binding')
        
        # Extract betting lines
        spread_buttons = container.find_all('offering-button', {'sub-type': 'S'})
        # ... parse odds
        
    return games
```

---

## Data Patterns Observed

### Spread Format
```
Examples:
- "-6  -110" (favorite by 6, -110 odds)
- "+3  -115" (underdog by 3, -115 odds)
- "pk  -110" (pick'em)

Parse with regex: r'([+-]?\d+\.?\d*)\s+([+-]\d+)'
```

### Moneyline Format
```
Examples:
- "-275" (favorite)
- "+230" (underdog)

Parse with regex: r'([+-]\d+)'
```

### Total Format
```
Examples:
- "O 43½  -110" (over 43.5, -110 odds)
- "U 43½  -110" (under 43.5, -110 odds)

Parse with regex: r'([OU])\s+([\d½]+)\s+([+-]\d+)'
```

### Team Total Format
```
Examples:
- "O 21½  +110" (team over 21.5)
- "U 21½  -130" (team under 21.5)
```

---

## Implementation Plan

### Phase 1: Basic Parsing (Today)

1. ✅ Page loads successfully
2. ⏳ Extract team names
3. ⏳ Extract rotation numbers
4. ⏳ Parse spread lines
5. ⏳ Parse moneylines
6. ⏳ Parse totals

### Phase 2: Data Validation (Tomorrow)

1. Verify team name normalization
2. Cross-check with Massey Ratings teams
3. Validate odds format
4. Handle missing/unavailable lines

### Phase 3: Game Matching (Tomorrow)

1. Pair Team1 (home) with Team2 (away)
2. Extract game date/time
3. Identify sport (NFL vs NCAAF)
4. Generate unique game IDs

---

## Specific Parsing Functions Needed

### 1. Parse Spread Line

```python
def parse_spread(spread_text: str) -> Tuple[float, int]:
    """
    Parse spread line like '-6  -110'
    
    Returns:
        (spread, price) e.g., (-6.0, -110)
    """
    pattern = r'([+-]?\d+\.?\d*)\s+([+-]\d+)'
    match = re.search(pattern, spread_text)
    if match:
        spread = float(match.group(1))
        price = int(match.group(2))
        return (spread, price)
    return (None, None)
```

### 2. Parse Moneyline

```python
def parse_moneyline(ml_text: str) -> int:
    """
    Parse moneyline like '-275'
    
    Returns:
        moneyline as int, e.g., -275
    """
    pattern = r'([+-]\d+)'
    match = re.search(pattern, ml_text)
    if match:
        return int(match.group(1))
    return None
```

### 3. Parse Total

```python
def parse_total(total_text: str) -> Tuple[str, float, int]:
    """
    Parse total line like 'O 43½  -110'
    
    Returns:
        (direction, total, price) e.g., ('O', 43.5, -110)
    """
    # Convert ½ to .5
    total_text = total_text.replace('½', '.5')
    
    pattern = r'([OU])\s+([\d.]+)\s+([+-]\d+)'
    match = re.search(pattern, total_text)
    if match:
        direction = match.group(1)
        total = float(match.group(2))
        price = int(match.group(3))
        return (direction, total, price)
    return (None, None, None)
```

### 4. Normalize Team Names

```python
TEAM_NAME_MAP = {
    'Buffalo Bills': 'BUF',
    'Kansas City Chiefs': 'KC',
    'Cincinnati Bengals': 'CIN',
    'Baltimore Ravens': 'BAL',
    'Detroit Lions': 'DET',
    # ... add all teams
}

def normalize_team_name(full_name: str) -> str:
    """Convert full team name to abbreviation"""
    return TEAM_NAME_MAP.get(full_name, full_name)
```

---

## Next Steps

### Immediate (Today):

1. **Update `overtime_ag_scraper.py`** with parsing logic
2. **Test with real data** from the HTML file
3. **Validate extracted lines** match what's visible

### This Week:

1. **Handle both Team1 and Team2** (home/away pairing)
2. **Extract game date/time** from page
3. **Add NCAAF support** (same structure, different sport)
4. **Error handling** for missing/unavailable lines

### Integration:

1. **Save to data/odds/** in standard format
2. **Load into power rating comparison**
3. **Calculate edges** using Massey ratings
4. **Generate weekly tracker** with opportunities

---

## Code Example: Complete Implementation

```python
async def scrape_betting_lines(self, sport: str = 'nfl') -> List[BettingLine]:
    """
    Scrape betting lines from overtime.ag
    """
    lines = []
    
    try:
        # Wait for games to load
        await self.page.wait_for_selector('.game_line_comments', timeout=10000)
        
        # Get sport identifier
        sport_text = await self.page.inner_text('.panel-title')  # e.g., "Football-NFL"
        
        # Find all game rows
        game_rows = await self.page.query_selector_all('.row')
        
        current_game = {}
        
        for i, row in enumerate(game_rows):
            try:
                # Check if this row has team data
                team_elem = await row.query_selector('span[ng-bind*="Team"]')
                if not team_elem:
                    continue
                
                team_name = (await team_elem.inner_text()).strip()
                
                # Get rotation number
                rot_elem = await row.query_selector('.line-rot-num')
                rot_num = await rot_elem.inner_text() if rot_elem else None
                
                # Extract odds
                spread_elem = await row.query_selector('offering-button[sub-type="S"] span.ng-binding')
                ml_elem = await row.query_selector('offering-button[sub-type="M"] span.ng-binding')
                total_elem = await row.query_selector('offering-button[sub-type="L"] span.ng-binding')
                
                spread_text = await spread_elem.inner_text() if spread_elem else None
                ml_text = await ml_elem.inner_text() if ml_elem else None
                total_text = await total_elem.inner_text() if total_elem else None
                
                # Parse odds
                spread, spread_price = parse_spread(spread_text) if spread_text else (None, None)
                ml = parse_moneyline(ml_text) if ml_text else None
                direction, total, total_price = parse_total(total_text) if total_text else (None, None, None)
                
                # Determine if Team1 (home) or Team2 (away)
                if 'Team2' in await team_elem.get_attribute('ng-bind'):
                    # This is away team
                    current_game['away_team'] = team_name
                    current_game['away_rot'] = rot_num
                    current_game['away_spread'] = spread
                    current_game['away_spread_price'] = spread_price
                    current_game['away_ml'] = ml
                else:
                    # This is home team - complete the game
                    if current_game:
                        betting_line = BettingLine(
                            game_id=f"{current_game['away_rot']}-{rot_num}",
                            sport=sport,
                            away_team=current_game['away_team'],
                            home_team=team_name,
                            game_time="TBD",  # Extract from page
                            spread=current_game.get('away_spread'),
                            spread_away_price=current_game.get('away_spread_price'),
                            spread_home_price=spread_price,
                            total=total,
                            over_price=total_price if direction == 'O' else None,
                            under_price=total_price if direction == 'U' else None,
                            away_ml=current_game.get('away_ml'),
                            home_ml=ml
                        )
                        lines.append(betting_line)
                        current_game = {}
                
            except Exception as e:
                print(f"Error parsing row {i}: {e}")
                continue
        
        print(f"✅ Extracted {len(lines)} betting lines")
        return lines
        
    except Exception as e:
        print(f"❌ Error scraping: {e}")
        return []
```

---

## Ready to Implement!

All the patterns are clear. I'll now update the actual `overtime_ag_scraper.py` file with this parsing logic.

**Estimated time**: 30-60 minutes to implement and test
**Confidence**: High - structure is consistent and well-formed
