-- ============================================================
-- BILLY WALTERS SPORTS ANALYTICS DATABASE SCHEMA
-- Version: 1.0.0
-- Created: 2025-11-23
-- Description: Complete schema for NFL/NCAAF betting analytics
-- ============================================================

-- Drop existing tables (be careful in production!)
DROP TABLE IF EXISTS performance_metrics CASCADE;
DROP TABLE IF EXISTS situational_factors CASCADE;
DROP TABLE IF EXISTS injuries CASCADE;
DROP TABLE IF EXISTS weather CASCADE;
DROP TABLE IF EXISTS bets CASCADE;
DROP TABLE IF EXISTS odds CASCADE;
DROP TABLE IF EXISTS power_ratings CASCADE;
DROP TABLE IF EXISTS games CASCADE;
DROP TABLE IF EXISTS teams CASCADE;

-- ============================================================
-- CORE TABLES
-- ============================================================

-- Teams: Master team list
CREATE TABLE teams (
    team_id SERIAL PRIMARY KEY,
    team_name VARCHAR(100) NOT NULL UNIQUE,
    team_abbr VARCHAR(10) UNIQUE,
    league VARCHAR(10) NOT NULL CHECK (league IN ('NFL', 'NCAAF')),

    -- Location
    city VARCHAR(100),
    state VARCHAR(50),
    stadium_name VARCHAR(100),
    is_outdoor BOOLEAN DEFAULT TRUE,

    -- Conference (NCAAF only)
    conference VARCHAR(50),
    division VARCHAR(50),

    -- Metadata
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Games: Core schedule and results
CREATE TABLE games (
    game_id VARCHAR(50) PRIMARY KEY,  -- e.g., "BUF_KC_2025_W12"

    -- Schedule Info
    season INT NOT NULL,
    week INT NOT NULL,
    league VARCHAR(10) NOT NULL CHECK (league IN ('NFL', 'NCAAF')),
    game_date TIMESTAMP NOT NULL,

    -- Teams
    home_team VARCHAR(100) NOT NULL,
    away_team VARCHAR(100) NOT NULL,

    -- Results (NULL until game finishes)
    home_score INT,
    away_score INT,
    final_margin INT,  -- home_score - away_score
    total_points INT,  -- home_score + away_score

    -- Game Status
    status VARCHAR(20) DEFAULT 'SCHEDULED',  -- SCHEDULED, IN_PROGRESS, FINAL, POSTPONED

    -- Venue
    stadium VARCHAR(100),
    is_outdoor BOOLEAN,
    is_neutral_site BOOLEAN DEFAULT FALSE,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Indexes
    CONSTRAINT unique_game UNIQUE (season, week, league, home_team, away_team)
);

-- Power Ratings: Weekly team ratings
CREATE TABLE power_ratings (
    id SERIAL PRIMARY KEY,

    -- Identification
    season INT NOT NULL,
    week INT NOT NULL,
    league VARCHAR(10) NOT NULL CHECK (league IN ('NFL', 'NCAAF')),
    team VARCHAR(100) NOT NULL,

    -- Ratings
    rating DECIMAL(6,2) NOT NULL,     -- e.g., 92.50
    offense_rating DECIMAL(6,2),
    defense_rating DECIMAL(6,2),
    special_teams_rating DECIMAL(6,2),

    -- Adjustments
    sos_adjustment DECIMAL(5,2),      -- Strength of schedule
    recent_form_adjustment DECIMAL(5,2),
    injury_adjustment DECIMAL(5,2),

    -- Source
    source VARCHAR(50) NOT NULL,      -- 'massey', 'espn', 'composite'
    raw_rating DECIMAL(6,2),          -- Before adjustments

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_rating UNIQUE (season, week, league, team, source)
);

-- Odds: Line movements and closing lines
CREATE TABLE odds (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL REFERENCES games(game_id) ON DELETE CASCADE,

    -- Source
    sportsbook VARCHAR(50) NOT NULL,  -- 'overtime', 'pinnacle', 'circa', 'fanduel'
    odds_type VARCHAR(20) NOT NULL,   -- 'opening', 'current', 'closing'

    -- Spread
    home_spread DECIMAL(4,1),
    home_spread_juice INT DEFAULT -110,
    away_spread DECIMAL(4,1),
    away_spread_juice INT DEFAULT -110,

    -- Total
    total DECIMAL(4,1),
    over_juice INT DEFAULT -110,
    under_juice INT DEFAULT -110,

    -- Moneyline
    home_moneyline INT,
    away_moneyline INT,

    -- Timing
    timestamp TIMESTAMP NOT NULL,
    line_movement DECIMAL(4,1),       -- Change from previous line

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_odds_type CHECK (odds_type IN ('opening', 'current', 'closing'))
);

-- Bets: Our plays and results
CREATE TABLE bets (
    bet_id VARCHAR(50) PRIMARY KEY,   -- e.g., "2025_W12_GB_MIN_SPREAD"
    game_id VARCHAR(50) NOT NULL REFERENCES games(game_id) ON DELETE CASCADE,

    -- Bet Details
    bet_type VARCHAR(20) NOT NULL,    -- 'spread', 'total', 'moneyline'
    side VARCHAR(50) NOT NULL,        -- team name or 'OVER'/'UNDER'
    line DECIMAL(4,1) NOT NULL,       -- line we got
    juice INT DEFAULT -110,
    sportsbook VARCHAR(50),

    -- Edge Analysis
    predicted_line DECIMAL(4,1),      -- our line (from power ratings)
    market_line DECIMAL(4,1),         -- market line when we bet
    edge_points DECIMAL(4,2) NOT NULL,-- difference (always positive)
    edge_category VARCHAR(20) NOT NULL, -- 'MAX', 'STRONG', 'MEDIUM', 'WEAK'
    confidence INT CHECK (confidence BETWEEN 1 AND 100),

    -- Position Sizing
    kelly_pct DECIMAL(5,2),           -- recommended Kelly %
    actual_pct DECIMAL(5,2),          -- what we actually bet
    units DECIMAL(6,2) NOT NULL,      -- bet size in units
    risk_amount DECIMAL(10,2),        -- dollars risked

    -- Results
    closing_line DECIMAL(4,1),        -- line at kickoff
    clv DECIMAL(4,2),                 -- closing line value (closing - our line)

    result VARCHAR(20) DEFAULT 'PENDING', -- 'WIN', 'LOSS', 'PUSH', 'PENDING'
    profit_loss DECIMAL(10,2),        -- actual P&L
    roi DECIMAL(6,2),                 -- return on investment %

    -- Tracking
    placed_at TIMESTAMP,
    closed_at TIMESTAMP,              -- when line closed (game start)
    graded_at TIMESTAMP,              -- when result was graded

    -- Notes
    notes TEXT,
    key_factors TEXT[],               -- Array of key factors

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_bet_type CHECK (bet_type IN ('spread', 'total', 'moneyline')),
    CONSTRAINT valid_edge_category CHECK (edge_category IN ('MAX', 'STRONG', 'MEDIUM', 'WEAK')),
    CONSTRAINT valid_result CHECK (result IN ('WIN', 'LOSS', 'PUSH', 'PENDING', 'CANCELLED'))
);

-- Weather: Game-time conditions
CREATE TABLE weather (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL REFERENCES games(game_id) ON DELETE CASCADE,

    -- Temperature
    temperature DECIMAL(5,2),         -- Fahrenheit
    feels_like DECIMAL(5,2),

    -- Wind
    wind_speed DECIMAL(5,2),          -- MPH
    wind_gust DECIMAL(5,2),
    wind_direction VARCHAR(10),       -- 'N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'

    -- Precipitation
    humidity INT,                     -- percentage
    precipitation_chance INT,         -- percentage
    precipitation_type VARCHAR(20),   -- 'none', 'rain', 'snow', 'sleet'
    precipitation_amount DECIMAL(5,2), -- inches

    -- Visibility
    visibility DECIMAL(5,2),          -- miles
    cloud_cover INT,                  -- percentage

    -- Billy Walters Adjustments
    total_adjustment DECIMAL(4,2),    -- impact on total (negative = lower)
    spread_adjustment DECIMAL(4,2),   -- impact on spread
    weather_severity_score INT CHECK (weather_severity_score BETWEEN 0 AND 100),

    -- Classification
    weather_category VARCHAR(20),     -- 'IDEAL', 'GOOD', 'MODERATE', 'POOR', 'SEVERE'

    -- Source & Timing
    source VARCHAR(50) NOT NULL,      -- 'accuweather', 'openweather', 'noaa'
    forecast_type VARCHAR(20),        -- 'forecast', 'current', 'actual'
    forecast_hours_ahead INT,         -- how far in advance (0 = actual)
    is_actual BOOLEAN DEFAULT FALSE,  -- TRUE if post-game actual

    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_weather_category CHECK (
        weather_category IN ('IDEAL', 'GOOD', 'MODERATE', 'POOR', 'SEVERE')
    )
);

-- Injuries: Player status and impact
CREATE TABLE injuries (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL REFERENCES games(game_id) ON DELETE CASCADE,
    team VARCHAR(100) NOT NULL,

    -- Player Info
    player_name VARCHAR(100) NOT NULL,
    position VARCHAR(10) NOT NULL,    -- 'QB', 'RB', 'WR', 'TE', 'OL', 'DL', 'LB', 'DB'
    jersey_number INT,

    -- Injury Details
    injury_status VARCHAR(20) NOT NULL, -- 'OUT', 'DOUBTFUL', 'QUESTIONABLE', 'PROBABLE'
    injury_type VARCHAR(50),           -- 'knee', 'concussion', 'hamstring', etc.
    injury_side VARCHAR(10),           -- 'left', 'right', 'both'

    -- Impact Assessment
    impact_points DECIMAL(4,2),       -- power rating adjustment
    player_tier VARCHAR(20),          -- 'ELITE', 'STARTER', 'BACKUP', 'DEPTH'
    is_key_player BOOLEAN DEFAULT FALSE,

    -- Timeline
    reported_date DATE,
    game_status VARCHAR(20),          -- 'ACTIVE', 'INACTIVE', 'LIMITED', 'DNP'
    last_updated TIMESTAMP,

    -- Source
    source VARCHAR(50) NOT NULL,      -- 'espn', 'nfl', 'fantasypros', 'official'

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_injury_status CHECK (
        injury_status IN ('OUT', 'DOUBTFUL', 'QUESTIONABLE', 'PROBABLE', 'HEALTHY')
    ),
    CONSTRAINT valid_player_tier CHECK (
        player_tier IN ('ELITE', 'STARTER', 'BACKUP', 'DEPTH')
    ),
    CONSTRAINT valid_game_status CHECK (
        game_status IN ('ACTIVE', 'INACTIVE', 'LIMITED', 'DNP', 'FULL')
    )
);

-- Situational Factors: SWEF (Situation, Weather, Emotion, Fundamentals)
CREATE TABLE situational_factors (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL REFERENCES games(game_id) ON DELETE CASCADE,
    team VARCHAR(100) NOT NULL,

    -- Situation (Rest & Travel)
    days_rest INT,
    is_short_rest BOOLEAN DEFAULT FALSE,    -- Thursday/Monday night
    is_extra_rest BOOLEAN DEFAULT FALSE,    -- Coming off bye

    travel_distance INT,                    -- miles
    time_zone_change INT,                   -- hours (negative = west to east)
    is_long_travel BOOLEAN DEFAULT FALSE,   -- >1500 miles

    -- Emotion (Motivation & Context)
    is_division_game BOOLEAN DEFAULT FALSE,
    is_rivalry BOOLEAN DEFAULT FALSE,
    is_playoff_implications BOOLEAN DEFAULT FALSE,
    is_revenge_game BOOLEAN DEFAULT FALSE,
    is_prime_time BOOLEAN DEFAULT FALSE,

    -- Fundamentals (Performance & Trends)
    current_streak INT,                     -- positive = win streak, negative = loss
    home_record VARCHAR(10),                -- e.g., "6-2"
    away_record VARCHAR(10),
    ats_record VARCHAR(10),                 -- against the spread
    ats_last_5 VARCHAR(10),                 -- ATS last 5 games

    scoring_avg DECIMAL(5,2),               -- points per game
    scoring_avg_last_3 DECIMAL(5,2),
    points_allowed_avg DECIMAL(5,2),
    points_allowed_last_3 DECIMAL(5,2),

    turnover_margin INT,                    -- season total
    turnover_margin_last_3 INT,

    -- Billy Walters Adjustments
    situational_adjustment DECIMAL(4,2),    -- total impact on line
    situation_score INT CHECK (situation_score BETWEEN -10 AND 10),

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_team_situation UNIQUE (game_id, team)
);

-- Performance Metrics: Weekly/seasonal aggregates
CREATE TABLE performance_metrics (
    id SERIAL PRIMARY KEY,

    -- Period
    season INT NOT NULL,
    week INT,                         -- NULL for season totals
    league VARCHAR(10) CHECK (league IN ('NFL', 'NCAAF')),

    -- Betting Results
    total_bets INT DEFAULT 0,
    wins INT DEFAULT 0,
    losses INT DEFAULT 0,
    pushes INT DEFAULT 0,
    pending INT DEFAULT 0,
    win_pct DECIMAL(5,2),

    -- By Category
    max_bets INT DEFAULT 0,
    max_wins INT DEFAULT 0,
    max_roi DECIMAL(6,2),

    strong_bets INT DEFAULT 0,
    strong_wins INT DEFAULT 0,
    strong_roi DECIMAL(6,2),

    medium_bets INT DEFAULT 0,
    medium_wins INT DEFAULT 0,
    medium_roi DECIMAL(6,2),

    weak_bets INT DEFAULT 0,
    weak_wins INT DEFAULT 0,
    weak_roi DECIMAL(6,2),

    -- By Type
    spread_bets INT DEFAULT 0,
    spread_wins INT DEFAULT 0,
    total_bets_count INT DEFAULT 0,  -- renamed to avoid column name conflict
    total_wins INT DEFAULT 0,
    moneyline_bets INT DEFAULT 0,
    moneyline_wins INT DEFAULT 0,

    -- Financial
    total_risked DECIMAL(10,2),
    total_profit DECIMAL(10,2),
    roi DECIMAL(6,2),
    roi_per_bet DECIMAL(6,2),

    -- CLV (Closing Line Value)
    avg_clv DECIMAL(4,2),              -- Average closing line value
    median_clv DECIMAL(4,2),
    positive_clv_pct DECIMAL(5,2),     -- % of bets with +CLV
    clv_wins INT DEFAULT 0,            -- Wins when we had +CLV
    clv_losses INT DEFAULT 0,          -- Losses when we had +CLV

    -- Edge Analysis
    avg_edge DECIMAL(4,2),
    median_edge DECIMAL(4,2),
    edge_realization_pct DECIMAL(5,2), -- How often edges resulted in wins

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_period UNIQUE (season, week, league)
);

-- ============================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================

-- Games
CREATE INDEX idx_games_season_week ON games(season, week, league);
CREATE INDEX idx_games_date ON games(game_date);
CREATE INDEX idx_games_teams ON games(home_team, away_team);
CREATE INDEX idx_games_status ON games(status);

-- Power Ratings
CREATE INDEX idx_power_ratings_lookup ON power_ratings(season, week, league, team);
CREATE INDEX idx_power_ratings_source ON power_ratings(source);

-- Odds
CREATE INDEX idx_odds_game_id ON odds(game_id);
CREATE INDEX idx_odds_sportsbook ON odds(sportsbook);
CREATE INDEX idx_odds_type ON odds(odds_type);
CREATE INDEX idx_odds_timestamp ON odds(timestamp);

-- Bets
CREATE INDEX idx_bets_game_id ON bets(game_id);
CREATE INDEX idx_bets_result ON bets(result);
CREATE INDEX idx_bets_category ON bets(edge_category);
CREATE INDEX idx_bets_type ON bets(bet_type);
CREATE INDEX idx_bets_placed_at ON bets(placed_at);

-- Weather
CREATE INDEX idx_weather_game_id ON weather(game_id);
CREATE INDEX idx_weather_severity ON weather(weather_severity_score);
CREATE INDEX idx_weather_category ON weather(weather_category);

-- Injuries
CREATE INDEX idx_injuries_game_id ON injuries(game_id);
CREATE INDEX idx_injuries_team ON injuries(team);
CREATE INDEX idx_injuries_position ON injuries(position);
CREATE INDEX idx_injuries_status ON injuries(injury_status);

-- Situational Factors
CREATE INDEX idx_situational_game_id ON situational_factors(game_id);
CREATE INDEX idx_situational_team ON situational_factors(team);

-- Performance Metrics
CREATE INDEX idx_performance_season_week ON performance_metrics(season, week);

-- ============================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================

-- View: Complete game analysis (combines all data)
CREATE OR REPLACE VIEW vw_game_analysis AS
SELECT
    g.game_id,
    g.season,
    g.week,
    g.league,
    g.game_date,
    g.home_team,
    g.away_team,
    g.home_score,
    g.away_score,
    g.status,

    -- Power Ratings
    pr_home.rating as home_rating,
    pr_away.rating as away_rating,

    -- Odds
    o_open.home_spread as opening_spread,
    o_close.home_spread as closing_spread,
    o_open.total as opening_total,
    o_close.total as closing_total,

    -- Weather
    w.temperature,
    w.wind_speed,
    w.weather_category,
    w.total_adjustment as weather_total_adj,

    -- Bets
    b.bet_id,
    b.bet_type,
    b.side,
    b.line,
    b.edge_points,
    b.edge_category,
    b.clv,
    b.result,
    b.roi

FROM games g
LEFT JOIN power_ratings pr_home ON
    g.season = pr_home.season AND
    g.week = pr_home.week AND
    g.home_team = pr_home.team AND
    pr_home.source = 'composite'
LEFT JOIN power_ratings pr_away ON
    g.season = pr_away.season AND
    g.week = pr_away.week AND
    g.away_team = pr_away.team AND
    pr_away.source = 'composite'
LEFT JOIN odds o_open ON
    g.game_id = o_open.game_id AND
    o_open.odds_type = 'opening'
LEFT JOIN odds o_close ON
    g.game_id = o_close.game_id AND
    o_close.odds_type = 'closing'
LEFT JOIN weather w ON
    g.game_id = w.game_id AND
    w.is_actual = TRUE
LEFT JOIN bets b ON
    g.game_id = b.game_id;

-- View: Weekly betting summary
CREATE OR REPLACE VIEW vw_weekly_summary AS
SELECT
    season,
    week,
    league,
    COUNT(*) as total_bets,
    SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN result = 'LOSS' THEN 1 ELSE 0 END) as losses,
    SUM(CASE WHEN result = 'PUSH' THEN 1 ELSE 0 END) as pushes,
    ROUND(AVG(edge_points), 2) as avg_edge,
    ROUND(AVG(clv), 2) as avg_clv,
    ROUND(AVG(roi), 2) as avg_roi,
    ROUND(SUM(profit_loss), 2) as total_profit
FROM bets b
JOIN games g ON b.game_id = g.game_id
WHERE result IN ('WIN', 'LOSS', 'PUSH')
GROUP BY season, week, league
ORDER BY season DESC, week DESC;

-- ============================================================
-- COMMENTS
-- ============================================================

COMMENT ON TABLE games IS 'Core game schedule and results';
COMMENT ON TABLE power_ratings IS 'Weekly team power ratings from multiple sources';
COMMENT ON TABLE odds IS 'Line movements and odds from various sportsbooks';
COMMENT ON TABLE bets IS 'Our betting plays with edge analysis and results';
COMMENT ON TABLE weather IS 'Game-time weather conditions and impact adjustments';
COMMENT ON TABLE injuries IS 'Player injuries and impact on power ratings';
COMMENT ON TABLE situational_factors IS 'SWEF factors (Situation, Weather, Emotion, Fundamentals)';
COMMENT ON TABLE performance_metrics IS 'Weekly and seasonal betting performance aggregates';

COMMENT ON VIEW vw_game_analysis IS 'Complete game analysis combining all data sources';
COMMENT ON VIEW vw_weekly_summary IS 'Weekly betting performance summary';

-- ============================================================
-- SCHEMA VERSION
-- ============================================================

CREATE TABLE schema_version (
    version VARCHAR(20) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT NOW(),
    description TEXT
);

INSERT INTO schema_version (version, description) VALUES
('1.0.0', 'Initial schema with games, bets, weather, injuries, situational factors');
