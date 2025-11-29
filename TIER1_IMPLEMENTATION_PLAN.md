# TIER 1 Critical Tables Implementation Plan

## Overview
Implement 4 critical tables to complete the Billy Walters analytics system. These tables enable injury impact assessment, practice tracking, weather/emotional adjustments, and team dynamics analysis.

**Status**: Planning Phase | **Target**: Single Focused Implementation

---

## Architecture Strategy

### File Organization (Following Existing Patterns)
- **Pydantic Models**: Add to `src/db/raw_data_models.py` (data collection pipeline tables)
- **CRUD Operations**: Add to `src/db/raw_data_operations.py` (25+ new methods)
- **Schema**: Add to `src/db/schema.sql` (4 new tables + 8 indexes)
- **Exports**: Update `src/db/__init__.py` to export new models

### Design Principles
- Follow existing SQLite schema patterns (no breaking changes)
- Use raw_data model structure (league_id, season, week, team_id, created_at)
- Add proper foreign keys with referential integrity
- Create performance indexes for common query patterns
- Validation through Pydantic models before database insert

---

## Table 1: player_valuations

### Purpose
Pre-calculated point spread impact values for players. Used by injury tracking to determine severity of player loss.

### Schema
```sql
CREATE TABLE IF NOT EXISTS player_valuations (
  id INTEGER PRIMARY KEY,
  league_id INTEGER NOT NULL,
  team_id INTEGER NOT NULL,
  player_id TEXT,
  player_name TEXT NOT NULL,
  position TEXT NOT NULL,
  season INTEGER NOT NULL,
  week INTEGER,

  -- Valuation metrics
  point_value REAL NOT NULL,        -- Spread points player represents (0.5 - 5.0)
  snap_count_pct REAL,              -- % of team snaps played (0-100)
  impact_rating REAL,               -- Overall impact coefficient (1.0 = average)
  is_starter BOOLEAN DEFAULT 1,     -- Plays significant role
  depth_chart_position INTEGER,     -- Position on depth chart (1 = starter)

  -- Context
  notes TEXT,
  source TEXT,
  last_updated TIMESTAMP,
  collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (league_id) REFERENCES leagues(id),
  FOREIGN KEY (team_id) REFERENCES teams(id),
  UNIQUE(league_id, team_id, season, week, player_id)
);
```

### Pydantic Model
```python
class PlayerValuation(BaseModel):
    league_id: int
    team_id: int
    player_id: Optional[str] = None
    player_name: str
    position: str
    season: int
    week: Optional[int] = None

    point_value: float  # 0.5 - 5.0
    snap_count_pct: Optional[float] = None
    impact_rating: Optional[float] = None
    is_starter: bool = True
    depth_chart_position: Optional[int] = None

    notes: Optional[str] = None
    source: Optional[str] = None
```

### CRUD Operations (RawDataOperations)
- `insert_player_valuation(valuation: PlayerValuation)`
- `get_player_valuation(league_id, team_id, season, week, player_id)`
- `get_team_valuations_by_week(league_id, team_id, season, week)`
- `update_player_snap_count(league_id, team_id, player_id, snap_count_pct)`
- `get_starters_by_position(league_id, team_id, season, week, position)`

### Integration Points
- Injury calculator uses `point_value` to determine spread impact
- Edge detector adjusts confidence based on player absences
- Player rankings system feeds into depth chart positions

---

## Table 2: practice_reports

### Purpose
Track Wednesday practice status (Billy Walters' key signal: "Wednesday practice = Sunday play"). This is critical for injury assessment.

### Schema
```sql
CREATE TABLE IF NOT EXISTS practice_reports (
  id INTEGER PRIMARY KEY,
  league_id INTEGER NOT NULL,
  team_id INTEGER NOT NULL,
  player_id TEXT,
  player_name TEXT NOT NULL,
  season INTEGER NOT NULL,
  week INTEGER NOT NULL,

  -- Practice tracking
  practice_date DATE NOT NULL,        -- Practice date
  day_of_week INTEGER,                -- 0=Monday, 1=Tuesday, 2=Wednesday...
  participation TEXT NOT NULL,        -- FP, LP, DNP, NA, DTD
  severity TEXT,                      -- If injured: mild, moderate, severe
  notes TEXT,

  -- Trend analysis
  trend TEXT,                         -- improving, stable, declining
  sessions_participated INTEGER,      -- # sessions this week

  source TEXT,
  reported_date TIMESTAMP,
  collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (league_id) REFERENCES leagues(id),
  FOREIGN KEY (team_id) REFERENCES teams(id),
  UNIQUE(league_id, team_id, season, week, player_id, practice_date)
);
```

### Pydantic Model
```python
class PracticeReport(BaseModel):
    league_id: int
    team_id: int
    player_id: Optional[str] = None
    player_name: str
    season: int
    week: int

    practice_date: str  # ISO format
    day_of_week: Optional[int] = None
    participation: str  # FP, LP, DNP, NA, DTD
    severity: Optional[str] = None
    notes: Optional[str] = None

    trend: Optional[str] = None
    sessions_participated: Optional[int] = None

    source: Optional[str] = None
```

### CRUD Operations (RawDataOperations)
- `insert_practice_report(report: PracticeReport)`
- `get_practice_reports_by_week(league_id, team_id, season, week)`
- `get_player_practice_history(league_id, team_id, player_id, season, week_start, week_end)`
- `get_wednesday_status(league_id, team_id, season, week)` - Billy's key signal
- `update_trend(league_id, team_id, player_id, trend)`

### Integration Points
- **Billy's Rule**: "Wednesday practice = Sunday play" - check Wednesday participation before setting bet confidence
- Injury tracker uses practice trend to adjust severity assessment
- Edge detector adjusts confidence if key player DNP on Wednesday

---

## Table 3: game_swe_factors

### Purpose
Track Special, Weather, and Emotional (SWE) factors that adjust power ratings ±10-20%. Critical for spread calculation accuracy.

### Schema
```sql
CREATE TABLE IF NOT EXISTS game_swe_factors (
  id INTEGER PRIMARY KEY,
  league_id INTEGER NOT NULL,
  game_id TEXT NOT NULL,
  season INTEGER NOT NULL,
  week INTEGER NOT NULL,

  away_team_id INTEGER,
  home_team_id INTEGER,

  -- Special Factors (S)
  special_factor_description TEXT,
  special_adjustment REAL,            -- ±% adjustment to power ratings
  special_examples TEXT,              -- e.g., "Super Bowl letdown, primetime effect"

  -- Weather Factors (W)
  weather_factor_description TEXT,
  weather_adjustment REAL,            -- ±% adjustment
  temperature_impact REAL,            -- < 0°F increases difficulty
  wind_impact REAL,                   -- > 15mph affects kicking/passing
  precipitation_impact REAL,          -- Rain/snow affects running game

  -- Emotional Factors (E)
  emotional_factor_description TEXT,
  emotional_adjustment REAL,          -- ±% adjustment
  motivation_level TEXT,              -- revenge game, rivalry, playoff implications
  momentum_direction TEXT,             -- gaining, stable, losing confidence

  -- Overall calculation
  total_adjustment REAL,              -- Sum of S+W+E adjustments
  confidence_level REAL,              -- Impact certainty (0.0-1.0)

  notes TEXT,
  source TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (league_id) REFERENCES leagues(id),
  FOREIGN KEY (away_team_id) REFERENCES teams(id),
  FOREIGN KEY (home_team_id) REFERENCES teams(id),
  UNIQUE(league_id, game_id, season, week)
);
```

### Pydantic Model
```python
class GameSWEFactors(BaseModel):
    league_id: int
    game_id: str
    season: int
    week: int

    away_team_id: Optional[int] = None
    home_team_id: Optional[int] = None

    # Special Factors
    special_factor_description: Optional[str] = None
    special_adjustment: Optional[float] = None
    special_examples: Optional[str] = None

    # Weather Factors
    weather_factor_description: Optional[str] = None
    weather_adjustment: Optional[float] = None
    temperature_impact: Optional[float] = None
    wind_impact: Optional[float] = None
    precipitation_impact: Optional[float] = None

    # Emotional Factors
    emotional_factor_description: Optional[str] = None
    emotional_adjustment: Optional[float] = None
    motivation_level: Optional[str] = None
    momentum_direction: Optional[str] = None

    total_adjustment: Optional[float] = None
    confidence_level: Optional[float] = None

    notes: Optional[str] = None
    source: Optional[str] = None
```

### CRUD Operations (RawDataOperations)
- `insert_game_swe_factors(factors: GameSWEFactors)`
- `get_game_swe_factors(league_id, game_id)`
- `calculate_adjustment(game_id, league_id)` - Returns total adjustment %
- `get_weather_impact(league_id, game_id)`
- `get_emotional_factors(league_id, team_id, week)`

### Integration Points
- Edge detector applies `total_adjustment` to power rating calculations
- Power ratings adjusted: `home_power = massey_rating × (1 + total_adjustment)`
- Used in confidence level calculations (±10-20% range from PRD)

---

## Table 4: team_trends

### Purpose
Track team streaks, playoff position, and emotional state. Used for contextual play selection and confidence adjustments.

### Schema
```sql
CREATE TABLE IF NOT EXISTS team_trends (
  id INTEGER PRIMARY KEY,
  league_id INTEGER NOT NULL,
  team_id INTEGER NOT NULL,
  season INTEGER NOT NULL,
  week INTEGER NOT NULL,

  -- Streak information
  streak_direction TEXT,              -- winning, losing, neutral
  streak_length INTEGER,              -- Consecutive W/L
  recent_form_pct REAL,               -- Win % last 4 games

  -- Playoff context
  playoff_position INTEGER,           -- Rank for playoff seeding
  playoff_probability REAL,           -- % chance to make playoffs (0.0-1.0)
  divisional_rank INTEGER,            -- Division standing (1 = leader)
  conference_rank INTEGER,            -- Conference standing

  -- Emotional state
  emotional_state TEXT,               -- confident, struggling, desperate, comfortable
  desperation_level INTEGER,          -- 1-10 scale (10 = must win)
  revenge_factor BOOLEAN,             -- Playing against former team/coach
  rest_advantage REAL,                -- Days rest vs opponent

  -- Contextual factors
  home_field_consistency REAL,        -- Performance at home vs away
  situational_strength TEXT,          -- strong in blowouts, tight games, comebacks

  notes TEXT,
  source TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (league_id) REFERENCES leagues(id),
  FOREIGN KEY (team_id) REFERENCES teams(id),
  UNIQUE(league_id, team_id, season, week)
);
```

### Pydantic Model
```python
class TeamTrends(BaseModel):
    league_id: int
    team_id: int
    season: int
    week: int

    # Streaks
    streak_direction: Optional[str] = None
    streak_length: Optional[int] = None
    recent_form_pct: Optional[float] = None

    # Playoff context
    playoff_position: Optional[int] = None
    playoff_probability: Optional[float] = None
    divisional_rank: Optional[int] = None
    conference_rank: Optional[int] = None

    # Emotional
    emotional_state: Optional[str] = None
    desperation_level: Optional[int] = None
    revenge_factor: Optional[bool] = None
    rest_advantage: Optional[float] = None

    # Contextual
    home_field_consistency: Optional[float] = None
    situational_strength: Optional[str] = None

    notes: Optional[str] = None
    source: Optional[str] = None
```

### CRUD Operations (RawDataOperations)
- `insert_team_trends(trends: TeamTrends)`
- `get_team_trends(league_id, team_id, season, week)`
- `get_streak_info(league_id, team_id, season, week)`
- `get_playoff_context(league_id, week)` - All teams' playoff standings
- `calculate_desperation(league_id, team_id, week)` - Must-win situation detection
- `get_recent_form(league_id, team_id, season, last_n_games=4)`

### Integration Points
- Confidence adjustment: Desperate teams behave differently
- Play selection: Eliminate bets against teams with winning streaks (exception: value too high)
- Situational: Team playing to clinch vs team eliminated affects motivation
- Rest advantage: Travel fatigue can be 0.5-1.5 point swing

---

## Implementation Checklist

### Phase 1: Database Layer (Core)
- [ ] Add 4 table schemas to `schema.sql`
- [ ] Add 8 performance indexes
- [ ] Add 4 Pydantic models to `raw_data_models.py`
- [ ] Implement 25+ CRUD methods in `raw_data_operations.py`
- [ ] Update `src/db/__init__.py` with new exports

### Phase 2: Integration Points (Edge Detection)
- [ ] Update injury impact calculator to use `player_valuations`
- [ ] Update practice report loader to track Wednesday status
- [ ] Integrate SWE factor adjustments into power rating calculations
- [ ] Integrate team trends into confidence scoring

### Phase 3: Data Population (Collection)
- [ ] Create scrapers/APIs for player valuations (ESPN depth charts)
- [ ] Create practice report tracker (ESPN NFL/NCAAF practice reports)
- [ ] Create SWE factor analyzer (weather + situational inputs)
- [ ] Create team trends calculator (standings + recent form)

### Phase 4: Testing & Validation
- [ ] Unit tests for all 25+ CRUD operations
- [ ] Integration tests with edge detector
- [ ] Data validation tests (Pydantic models)
- [ ] Performance tests on index efficiency

### Phase 5: Documentation
- [ ] API docstrings for all new methods
- [ ] Usage examples for each table
- [ ] Data flow diagrams (collection → storage → analysis)
- [ ] Integration guide for edge detection

---

## Data Integration Sequence

```
Collection Phase:
  ESPN Depth Charts → player_valuations (snap count, position)
  Practice Reports → practice_reports (participation tracking)
  Weather API + Situational → game_swe_factors
  Standings + Win/Loss → team_trends

Analysis Phase:
  Injury Reports + player_valuations → Impact calculation
  Practice Reports → Billy's Wednesday signal
  game_swe_factors → ±10-20% power rating adjustment
  team_trends → Confidence adjustment (desperation, streak)

Edge Detection Output:
  Adjusted power ratings → More accurate edges
  Higher confidence signals → Better bet selection
  Risk mitigation → Avoid wrong situations
```

---

## Success Criteria

1. **Completeness**: All 4 tables implemented with schema + models + operations
2. **Integration**: Edge detector uses all 4 tables for calculations
3. **Quality**: 25+ CRUD operations fully tested (80%+ coverage)
4. **Performance**: Query times <100ms for common patterns (via indexes)
5. **Documentation**: Complete API docs + usage examples
6. **Data Accuracy**: Matches Billy Walters methodology (PRD v1.5)

---

## Dependencies & Assumptions

### Assumptions
- Player IDs consistent across data sources
- Season/week provide sufficient granularity for tracking
- Weather/emotional factors quantifiable as % adjustments
- Team trends available from standings/recent results

### Dependencies
- Existing database schema and connection layer
- Pydantic validation framework
- SQLite3 with foreign key constraints enabled
- Existing edge detection engine (will integrate with it)

### No Breaking Changes
- All new tables are additive (no modifications to existing tables)
- Backward compatible with current edge detection
- Optional integration (system works without these tables, just less accurate)

---

## Estimated Deliverables

**Files Modified**:
1. `src/db/schema.sql` - Add 4 table definitions + indexes
2. `src/db/raw_data_models.py` - Add 4 Pydantic models
3. `src/db/raw_data_operations.py` - Add 25+ CRUD methods
4. `src/db/__init__.py` - Update exports

**Files Created**:
- None (all changes integrated into existing structure)

**Tests**:
- `tests/db/test_player_valuations.py` - CRUD + validation
- `tests/db/test_practice_reports.py` - CRUD + Billy's rule
- `tests/db/test_game_swe_factors.py` - CRUD + adjustments
- `tests/db/test_team_trends.py` - CRUD + context

---

## Next Steps (If Approved)

1. Review & approve this plan
2. Implement database layer (schema + models + operations)
3. Add integration tests with edge detector
4. Create data population scripts
5. Document API and usage patterns
6. Validate against Billy Walters PRD requirements
