-- Billy Walters Sports Analyzer - SQLite Schema
-- Betting edges and CLV tracking database

-- Leagues lookup table
CREATE TABLE IF NOT EXISTS leagues (
  id INTEGER PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  display_name TEXT NOT NULL
);

-- Teams lookup table
CREATE TABLE IF NOT EXISTS teams (
  id INTEGER PRIMARY KEY,
  league_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  abbreviation TEXT,
  FOREIGN KEY (league_id) REFERENCES leagues(id),
  UNIQUE(league_id, name)
);

-- Games/matchups table
CREATE TABLE IF NOT EXISTS games (
  id INTEGER PRIMARY KEY,
  game_id TEXT UNIQUE NOT NULL,
  league_id INTEGER NOT NULL,
  week INTEGER NOT NULL,
  away_team_id INTEGER NOT NULL,
  home_team_id INTEGER NOT NULL,
  game_time TEXT NOT NULL,
  total REAL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (league_id) REFERENCES leagues(id),
  FOREIGN KEY (away_team_id) REFERENCES teams(id),
  FOREIGN KEY (home_team_id) REFERENCES teams(id)
);

-- Detected edges table
CREATE TABLE IF NOT EXISTS edges (
  id INTEGER PRIMARY KEY,
  game_id TEXT NOT NULL,
  league_id INTEGER NOT NULL,
  week INTEGER NOT NULL,
  away_team TEXT NOT NULL,
  home_team TEXT NOT NULL,
  game_time TEXT NOT NULL,

  -- Edge metrics
  predicted_line REAL NOT NULL,
  market_line REAL NOT NULL,
  edge REAL NOT NULL,
  edge_abs REAL NOT NULL,

  -- Betting recommendation
  classification TEXT NOT NULL,
  kelly_pct REAL,
  win_rate TEXT,
  recommendation TEXT,

  -- Additional data
  rotation_team1 INTEGER,
  rotation_team2 INTEGER,
  total REAL,

  -- Metadata
  generated_at TIMESTAMP,
  detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (league_id) REFERENCES leagues(id),
  UNIQUE(game_id, league_id, predicted_line)
);

-- CLV tracking table (betting plays and results)
CREATE TABLE IF NOT EXISTS clv_plays (
  id INTEGER PRIMARY KEY,
  game_id TEXT NOT NULL,
  league_id INTEGER NOT NULL,
  week INTEGER NOT NULL,
  rank INTEGER,
  matchup TEXT NOT NULL,
  game_time TEXT NOT NULL,

  -- Pick info
  pick TEXT NOT NULL,
  pick_side TEXT NOT NULL,
  spread REAL NOT NULL,
  total REAL,
  market_spread REAL,

  -- Edge metrics
  edge REAL,
  confidence TEXT,
  kelly REAL,
  units_recommended REAL,

  -- Team power ratings
  away_team TEXT NOT NULL,
  home_team TEXT NOT NULL,
  away_power REAL,
  home_power REAL,

  -- Opening odds
  opening_odds REAL,
  opening_line REAL,
  opening_datetime TIMESTAMP,

  -- Closing odds (for CLV calculation)
  closing_odds REAL,
  closing_line REAL,
  closing_datetime TIMESTAMP,

  -- Result tracking
  result TEXT,
  clv REAL,
  notes TEXT,
  status TEXT,

  -- Timestamps
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (league_id) REFERENCES leagues(id)
);

-- Edge detection sessions (metadata)
CREATE TABLE IF NOT EXISTS edge_sessions (
  id INTEGER PRIMARY KEY,
  league_id INTEGER NOT NULL,
  week INTEGER NOT NULL,
  edges_found INTEGER,
  min_edge REAL,
  hfa REAL,
  generated_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (league_id) REFERENCES leagues(id)
);

-- CLV tracking sessions (metadata)
CREATE TABLE IF NOT EXISTS clv_sessions (
  id INTEGER PRIMARY KEY,
  league_id INTEGER NOT NULL,
  week INTEGER NOT NULL,
  total_max_bet INTEGER,
  total_units_recommended REAL,
  status TEXT,
  generated_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (league_id) REFERENCES leagues(id)
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_edges_league_week ON edges(league_id, week);
CREATE INDEX IF NOT EXISTS idx_edges_game_id ON edges(game_id);
CREATE INDEX IF NOT EXISTS idx_edges_classification ON edges(classification);

CREATE INDEX IF NOT EXISTS idx_clv_plays_league_week ON clv_plays(league_id, week);
CREATE INDEX IF NOT EXISTS idx_clv_plays_game_id ON clv_plays(game_id);
CREATE INDEX IF NOT EXISTS idx_clv_plays_confidence ON clv_plays(confidence);
CREATE INDEX IF NOT EXISTS idx_clv_plays_status ON clv_plays(status);

CREATE INDEX IF NOT EXISTS idx_games_league_week ON games(league_id, week);
CREATE INDEX IF NOT EXISTS idx_games_game_id ON games(game_id);

-- ============================================================
-- RAW DATA TABLES (Data Collection Pipeline)
-- ============================================================

-- Game schedules and metadata
CREATE TABLE IF NOT EXISTS game_schedules (
  id INTEGER PRIMARY KEY,
  game_id TEXT UNIQUE NOT NULL,
  league_id INTEGER NOT NULL,
  season INTEGER NOT NULL,
  week INTEGER NOT NULL,
  away_team_id INTEGER NOT NULL,
  home_team_id INTEGER NOT NULL,
  game_datetime TIMESTAMP NOT NULL,
  venue_name TEXT,
  venue_city TEXT,
  is_neutral_site BOOLEAN DEFAULT 0,
  is_indoor BOOLEAN DEFAULT 0,
  status TEXT,
  source TEXT,
  collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (league_id) REFERENCES leagues(id),
  FOREIGN KEY (away_team_id) REFERENCES teams(id),
  FOREIGN KEY (home_team_id) REFERENCES teams(id)
);

-- Game results and box scores
CREATE TABLE IF NOT EXISTS game_results (
  id INTEGER PRIMARY KEY,
  game_id TEXT NOT NULL,
  league_id INTEGER NOT NULL,
  away_team_id INTEGER NOT NULL,
  home_team_id INTEGER NOT NULL,
  away_score INTEGER,
  home_score INTEGER,
  away_ats BOOLEAN,
  home_ats BOOLEAN,
  over_under BOOLEAN,
  attendance INTEGER,
  status TEXT,
  source TEXT,
  collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (league_id) REFERENCES leagues(id),
  FOREIGN KEY (away_team_id) REFERENCES teams(id),
  FOREIGN KEY (home_team_id) REFERENCES teams(id),
  UNIQUE(game_id)
);

-- Team statistics (offensive and defensive)
CREATE TABLE IF NOT EXISTS team_stats (
  id INTEGER PRIMARY KEY,
  league_id INTEGER NOT NULL,
  team_id INTEGER NOT NULL,
  season INTEGER NOT NULL,
  week INTEGER,

  -- Offensive stats
  points_for REAL,
  passing_yards REAL,
  rushing_yards REAL,
  total_yards REAL,
  first_downs INTEGER,
  third_down_conversion_pct REAL,
  fourth_down_conversion_pct REAL,
  turnovers INTEGER,
  fumbles INTEGER,
  interceptions INTEGER,
  penalties INTEGER,
  penalty_yards INTEGER,
  red_zone_efficiency REAL,
  scoring_efficiency REAL,

  -- Defensive stats
  points_against REAL,
  passing_yards_allowed REAL,
  rushing_yards_allowed REAL,
  total_yards_allowed REAL,
  sacks INTEGER,
  interceptions_forced INTEGER,
  fumbles_forced INTEGER,
  defensive_touchdowns INTEGER,
  red_zone_defense REAL,

  -- Special teams
  field_goal_pct REAL,
  extra_point_pct REAL,
  punting_avg REAL,
  kickoff_return_avg REAL,
  punt_return_avg REAL,

  -- Game metrics
  time_of_possession REAL,
  games_played INTEGER,
  games_won INTEGER,
  games_lost INTEGER,

  -- Metadata
  source TEXT,
  collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (league_id) REFERENCES leagues(id),
  FOREIGN KEY (team_id) REFERENCES teams(id),
  UNIQUE(league_id, team_id, season, week)
);

-- Player statistics (aggregate by team/week)
CREATE TABLE IF NOT EXISTS player_stats (
  id INTEGER PRIMARY KEY,
  league_id INTEGER NOT NULL,
  team_id INTEGER NOT NULL,
  player_name TEXT NOT NULL,
  player_id TEXT,
  position TEXT,
  season INTEGER NOT NULL,
  week INTEGER,

  -- Passing
  pass_attempts INTEGER,
  completions INTEGER,
  passing_yards INTEGER,
  passing_touchdowns INTEGER,
  interceptions INTEGER,

  -- Rushing
  rush_attempts INTEGER,
  rushing_yards INTEGER,
  rushing_touchdowns INTEGER,

  -- Receiving
  receptions INTEGER,
  receiving_yards INTEGER,
  receiving_touchdowns INTEGER,

  -- Defense
  tackles INTEGER,
  sacks REAL,
  pass_breakups INTEGER,
  forced_fumbles INTEGER,

  -- Kicking
  field_goals_made INTEGER,
  field_goals_attempted INTEGER,
  extra_points_made INTEGER,

  -- Metadata
  source TEXT,
  collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (league_id) REFERENCES leagues(id),
  FOREIGN KEY (team_id) REFERENCES teams(id)
);

-- Team standings and records
CREATE TABLE IF NOT EXISTS team_standings (
  id INTEGER PRIMARY KEY,
  league_id INTEGER NOT NULL,
  team_id INTEGER NOT NULL,
  season INTEGER NOT NULL,
  week INTEGER,

  wins INTEGER,
  losses INTEGER,
  ties INTEGER,
  win_percentage REAL,
  points_for INTEGER,
  points_against INTEGER,
  point_differential INTEGER,
  division_rank INTEGER,
  conference_rank INTEGER,
  overall_rank INTEGER,

  source TEXT,
  collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (league_id) REFERENCES leagues(id),
  FOREIGN KEY (team_id) REFERENCES teams(id),
  UNIQUE(league_id, team_id, season, week)
);

-- Massey Ratings and Power Ratings
CREATE TABLE IF NOT EXISTS power_ratings (
  id INTEGER PRIMARY KEY,
  league_id INTEGER NOT NULL,
  team_id INTEGER NOT NULL,
  season INTEGER NOT NULL,
  week INTEGER,

  -- Overall rating
  overall_rating REAL,
  offensive_rating REAL,
  defensive_rating REAL,
  special_teams_rating REAL,

  -- Advanced metrics
  strength_of_schedule REAL,
  strength_of_victory REAL,
  strength_of_loss REAL,
  recent_form_rating REAL,

  -- Comparison and adjustments
  injury_adjustment REAL,
  rest_adjustment REAL,
  momentum_adjustment REAL,

  -- Massey specific
  massey_rating REAL,
  massey_rank INTEGER,

  -- Source attribution
  source TEXT,
  rating_date TIMESTAMP,
  collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (league_id) REFERENCES leagues(id),
  FOREIGN KEY (team_id) REFERENCES teams(id),
  UNIQUE(league_id, team_id, season, week, source)
);

-- Betting odds from multiple sources
CREATE TABLE IF NOT EXISTS betting_odds (
  id INTEGER PRIMARY KEY,
  game_id TEXT NOT NULL,
  league_id INTEGER NOT NULL,
  week INTEGER,

  -- Line information
  away_team_id INTEGER,
  home_team_id INTEGER,
  spread REAL,
  spread_odds REAL,
  total REAL,
  total_odds REAL,
  away_moneyline INTEGER,
  home_moneyline INTEGER,

  -- Timing
  line_time TIMESTAMP,
  opening_time TIMESTAMP,
  closing_time TIMESTAMP,

  -- Source
  source TEXT,
  sportsbook TEXT,
  collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (league_id) REFERENCES leagues(id),
  FOREIGN KEY (away_team_id) REFERENCES teams(id),
  FOREIGN KEY (home_team_id) REFERENCES teams(id)
);

-- Action Network sharp money signals
CREATE TABLE IF NOT EXISTS sharp_money_signals (
  id INTEGER PRIMARY KEY,
  game_id TEXT NOT NULL,
  league_id INTEGER NOT NULL,
  week INTEGER,

  away_team_id INTEGER,
  home_team_id INTEGER,

  -- Spread analysis
  spread_value REAL,
  spread_side TEXT,
  spread_tickets_pct REAL,
  spread_money_pct REAL,
  spread_divergence REAL,

  -- Total analysis
  total_value REAL,
  total_over_tickets_pct REAL,
  total_over_money_pct REAL,
  total_divergence REAL,

  -- Moneyline analysis
  away_tickets_pct REAL,
  away_money_pct REAL,
  home_tickets_pct REAL,
  home_money_pct REAL,
  moneyline_divergence REAL,

  -- Interpretation
  sharp_signal_strength REAL,
  signal_direction TEXT,
  confidence_level REAL,

  -- Metadata
  source TEXT,
  collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (league_id) REFERENCES leagues(id),
  FOREIGN KEY (away_team_id) REFERENCES teams(id),
  FOREIGN KEY (home_team_id) REFERENCES teams(id),
  UNIQUE(game_id, source)
);

-- Weather data for games
CREATE TABLE IF NOT EXISTS weather_data (
  id INTEGER PRIMARY KEY,
  game_id TEXT NOT NULL,
  league_id INTEGER NOT NULL,
  week INTEGER,

  game_datetime TIMESTAMP,
  venue_name TEXT,
  venue_city TEXT,

  -- Current conditions
  temperature_f REAL,
  temperature_c REAL,
  wind_speed_mph REAL,
  wind_direction TEXT,
  precipitation_in REAL,
  humidity_pct REAL,
  cloud_cover_pct REAL,

  -- Advanced metrics
  feels_like_temp_f REAL,
  uv_index REAL,
  visibility_mi REAL,

  -- Conditions
  conditions TEXT,
  weather_category TEXT,

  -- Source
  source TEXT,
  forecast_time TIMESTAMP,
  collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (league_id) REFERENCES leagues(id),
  UNIQUE(game_id, source)
);

-- Injury reports
CREATE TABLE IF NOT EXISTS injury_reports (
  id INTEGER PRIMARY KEY,
  league_id INTEGER NOT NULL,
  team_id INTEGER NOT NULL,
  player_name TEXT NOT NULL,
  player_id TEXT,
  position TEXT,
  season INTEGER NOT NULL,
  week INTEGER,

  injury_status TEXT,
  body_part TEXT,
  severity TEXT,
  expected_return TEXT,
  out_weeks INTEGER,

  -- Importance assessment
  is_starter BOOLEAN DEFAULT 0,
  impact_rating REAL,

  -- Source
  source TEXT,
  reported_date TIMESTAMP,
  collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (league_id) REFERENCES leagues(id),
  FOREIGN KEY (team_id) REFERENCES teams(id)
);

-- News and articles
CREATE TABLE IF NOT EXISTS news_articles (
  id INTEGER PRIMARY KEY,
  league_id INTEGER NOT NULL,
  team_id INTEGER,

  title TEXT NOT NULL,
  content TEXT,
  article_url TEXT UNIQUE,
  source TEXT,
  author TEXT,

  -- Categorization
  category TEXT,
  sentiment TEXT,
  impact_level TEXT,

  -- Relevance
  relevant_teams TEXT,
  relevant_keywords TEXT,

  published_at TIMESTAMP,
  collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (league_id) REFERENCES leagues(id),
  FOREIGN KEY (team_id) REFERENCES teams(id)
);

-- Data collection metadata
CREATE TABLE IF NOT EXISTS collection_sessions (
  id INTEGER PRIMARY KEY,
  league_id INTEGER NOT NULL,
  season INTEGER,
  week INTEGER,

  -- Timing
  started_at TIMESTAMP,
  completed_at TIMESTAMP,

  -- Sources
  sources_attempted TEXT,
  sources_successful TEXT,
  sources_failed TEXT,

  -- Statistics
  games_collected INTEGER,
  stats_records_collected INTEGER,
  odds_records_collected INTEGER,
  weather_records_collected INTEGER,
  injuries_collected INTEGER,

  -- Status
  status TEXT,
  error_messages TEXT,

  FOREIGN KEY (league_id) REFERENCES leagues(id)
);

-- ============================================================
-- TIER 1 CRITICAL TABLES (Billy Walters Methodology Support)
-- ============================================================

-- Player valuations (point spread impact by player)
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
  point_value REAL NOT NULL,
  snap_count_pct REAL,
  impact_rating REAL,
  is_starter BOOLEAN DEFAULT 1,
  depth_chart_position INTEGER,

  -- Context
  notes TEXT,
  source TEXT,
  last_updated TIMESTAMP,
  collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (league_id) REFERENCES leagues(id),
  FOREIGN KEY (team_id) REFERENCES teams(id),
  UNIQUE(league_id, team_id, season, week, player_id)
);

-- Practice reports (Wednesday practice status tracking)
CREATE TABLE IF NOT EXISTS practice_reports (
  id INTEGER PRIMARY KEY,
  league_id INTEGER NOT NULL,
  team_id INTEGER NOT NULL,
  player_id TEXT,
  player_name TEXT NOT NULL,
  season INTEGER NOT NULL,
  week INTEGER NOT NULL,

  -- Practice tracking
  practice_date DATE NOT NULL,
  day_of_week INTEGER,
  participation TEXT NOT NULL,
  severity TEXT,
  notes TEXT,

  -- Trend analysis
  trend TEXT,
  sessions_participated INTEGER,

  source TEXT,
  reported_date TIMESTAMP,
  collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (league_id) REFERENCES leagues(id),
  FOREIGN KEY (team_id) REFERENCES teams(id),
  UNIQUE(league_id, team_id, season, week, player_id, practice_date)
);

-- Game SWE factors (Special, Weather, Emotional adjustments)
CREATE TABLE IF NOT EXISTS game_swe_factors (
  id INTEGER PRIMARY KEY,
  league_id INTEGER NOT NULL,
  game_id TEXT NOT NULL,
  season INTEGER NOT NULL,
  week INTEGER NOT NULL,

  away_team_id INTEGER,
  home_team_id INTEGER,

  -- Special Factors
  special_factor_description TEXT,
  special_adjustment REAL,
  special_examples TEXT,

  -- Weather Factors
  weather_factor_description TEXT,
  weather_adjustment REAL,
  temperature_impact REAL,
  wind_impact REAL,
  precipitation_impact REAL,

  -- Emotional Factors
  emotional_factor_description TEXT,
  emotional_adjustment REAL,
  motivation_level TEXT,
  momentum_direction TEXT,

  -- Overall calculation
  total_adjustment REAL,
  confidence_level REAL,

  notes TEXT,
  source TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (league_id) REFERENCES leagues(id),
  FOREIGN KEY (away_team_id) REFERENCES teams(id),
  FOREIGN KEY (home_team_id) REFERENCES teams(id),
  UNIQUE(league_id, game_id, season, week)
);

-- Team trends (streaks, playoff position, emotional state)
CREATE TABLE IF NOT EXISTS team_trends (
  id INTEGER PRIMARY KEY,
  league_id INTEGER NOT NULL,
  team_id INTEGER NOT NULL,
  season INTEGER NOT NULL,
  week INTEGER NOT NULL,

  -- Streak information
  streak_direction TEXT,
  streak_length INTEGER,
  recent_form_pct REAL,

  -- Playoff context
  playoff_position INTEGER,
  playoff_probability REAL,
  divisional_rank INTEGER,
  conference_rank INTEGER,

  -- Emotional state
  emotional_state TEXT,
  desperation_level INTEGER,
  revenge_factor BOOLEAN,
  rest_advantage REAL,

  -- Contextual factors
  home_field_consistency REAL,
  situational_strength TEXT,

  notes TEXT,
  source TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (league_id) REFERENCES leagues(id),
  FOREIGN KEY (team_id) REFERENCES teams(id),
  UNIQUE(league_id, team_id, season, week)
);

-- ============================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_game_schedules_league_week
  ON game_schedules(league_id, week);
CREATE INDEX IF NOT EXISTS idx_game_schedules_teams
  ON game_schedules(away_team_id, home_team_id);

CREATE INDEX IF NOT EXISTS idx_game_results_game_id
  ON game_results(game_id);
CREATE INDEX IF NOT EXISTS idx_game_results_league_teams
  ON game_results(league_id, away_team_id, home_team_id);

CREATE INDEX IF NOT EXISTS idx_team_stats_league_team_season
  ON team_stats(league_id, team_id, season, week);
CREATE INDEX IF NOT EXISTS idx_team_stats_team
  ON team_stats(team_id, season);

CREATE INDEX IF NOT EXISTS idx_player_stats_league_team
  ON player_stats(league_id, team_id, season, week);
CREATE INDEX IF NOT EXISTS idx_player_stats_position
  ON player_stats(position, season);

CREATE INDEX IF NOT EXISTS idx_team_standings_league_season
  ON team_standings(league_id, season, week);

CREATE INDEX IF NOT EXISTS idx_power_ratings_league_season
  ON power_ratings(league_id, team_id, season, week, source);
CREATE INDEX IF NOT EXISTS idx_power_ratings_source
  ON power_ratings(source, week);

CREATE INDEX IF NOT EXISTS idx_betting_odds_game
  ON betting_odds(game_id, source);
CREATE INDEX IF NOT EXISTS idx_betting_odds_time
  ON betting_odds(line_time, source);

CREATE INDEX IF NOT EXISTS idx_sharp_money_game
  ON sharp_money_signals(game_id, source);

CREATE INDEX IF NOT EXISTS idx_weather_game
  ON weather_data(game_id);

CREATE INDEX IF NOT EXISTS idx_injury_reports_team_week
  ON injury_reports(league_id, team_id, week);

CREATE INDEX IF NOT EXISTS idx_news_team
  ON news_articles(league_id, team_id);
CREATE INDEX IF NOT EXISTS idx_news_published
  ON news_articles(published_at DESC);

-- Indexes for TIER 1 critical tables
CREATE INDEX IF NOT EXISTS idx_player_valuations_league_team_season
  ON player_valuations(league_id, team_id, season, week);
CREATE INDEX IF NOT EXISTS idx_player_valuations_position
  ON player_valuations(position, season);

CREATE INDEX IF NOT EXISTS idx_practice_reports_league_team_week
  ON practice_reports(league_id, team_id, week);
CREATE INDEX IF NOT EXISTS idx_practice_reports_player_date
  ON practice_reports(player_id, practice_date);

CREATE INDEX IF NOT EXISTS idx_game_swe_factors_league_week
  ON game_swe_factors(league_id, week);
CREATE INDEX IF NOT EXISTS idx_game_swe_factors_game_id
  ON game_swe_factors(game_id);

CREATE INDEX IF NOT EXISTS idx_team_trends_league_season
  ON team_trends(league_id, season, week);
CREATE INDEX IF NOT EXISTS idx_team_trends_team_week
  ON team_trends(team_id, week);

-- ============================================================
-- BILLY WALTERS METHODOLOGY REFERENCE TABLES
-- ============================================================

-- Lookup: Point spread value percentages (NFL data since 1974)
CREATE TABLE IF NOT EXISTS lookup_point_values (
  point_spread REAL PRIMARY KEY,
  chance_of_hitting_pct REAL NOT NULL,
  dollar_value_buy_half_point TEXT,
  value_percentage REAL NOT NULL
);

-- Lookup: Play strength guidelines (star rating system)
CREATE TABLE IF NOT EXISTS lookup_play_strength_guidelines (
  min_percentage REAL PRIMARY KEY,
  play_strength_stars REAL NOT NULL,
  description TEXT
);

-- Lookup: Odds to implied spread conversion (at 110/100 vig)
CREATE TABLE IF NOT EXISTS lookup_odds_to_spread_conversion (
  posted_spread REAL NOT NULL,
  bet_price_text TEXT NOT NULL,
  implied_spread_at_110 REAL NOT NULL,
  PRIMARY KEY (posted_spread, bet_price_text)
);

-- Lookup: Moneyline conversion table
CREATE TABLE IF NOT EXISTS lookup_moneyline_conversion (
  point_spread REAL PRIMARY KEY,
  favorite_moneyline INTEGER NOT NULL,
  dog_moneyline INTEGER NOT NULL,
  description TEXT
);

-- ============================================================
-- INSERT BASE DATA
-- ============================================================

-- Insert base leagues
INSERT OR IGNORE INTO leagues (id, name, display_name) VALUES
  (1, 'NFL', 'National Football League'),
  (2, 'NCAAF', 'College Football');

-- Insert lookup: Point Values (The Value of Points table)
INSERT OR IGNORE INTO lookup_point_values (point_spread, chance_of_hitting_pct, dollar_value_buy_half_point, value_percentage) VALUES
  (1, 3, '6', 3.0),
  (2, 3, '6', 3.0),
  (3, 8, '20 off tie, 22 on to tie', 8.0),
  (4, 3, '6', 3.0),
  (5, 3, '6', 3.0),
  (6, 5, '10', 5.0),
  (7, 6, '13', 6.0),
  (8, 3, '6', 3.0),
  (9, 2, '3', 2.0),
  (10, 4, '9', 4.0),
  (11, 2, '5', 2.0),
  (12, 2, '4', 2.0),
  (13, 2, '5', 2.0),
  (14, 5, '11', 5.0),
  (15, 2, '5', 2.0),
  (16, 3, '6', 3.0),
  (17, 3, '6', 3.0),
  (18, 3, '6', 3.0),
  (21, 3, '6', 3.0);

-- Insert lookup: Play Strength Guidelines (star system)
INSERT OR IGNORE INTO lookup_play_strength_guidelines (min_percentage, play_strength_stars, description) VALUES
  (5.5, 0.5, 'Minimum qualifier - lean play'),
  (7.0, 1.0, 'Standard play'),
  (9.0, 1.5, 'Strong play'),
  (11.0, 2.0, 'Very strong play'),
  (13.0, 2.5, 'Excellent play'),
  (15.0, 3.0, 'Premium play - max bet');

-- Insert lookup: Odds to Spread Conversion Table
INSERT OR IGNORE INTO lookup_odds_to_spread_conversion (posted_spread, bet_price_text, implied_spread_at_110) VALUES
  (2.5, '-115', 2.625),
  (3.0, '+105', 2.625),
  (2.5, '-120', 2.75),
  (3.0, '100', 3.0),
  (2.5, '-125', 2.875),
  (3.0, '-105', 3.0),
  (3.0, '-110', 3.0),
  (3.0, '-115', 3.125),
  (3.5, '+105', 3.125),
  (3.0, '-120', 3.25),
  (3.5, '100', 3.25),
  (3.0, '-125', 3.375),
  (3.5, '-105', 3.375),
  (7.0, '100', 6.75),
  (6.5, '-115', 6.75),
  (7.0, '-105', 6.875),
  (6.5, '-120', 6.875),
  (7.0, '-110', 7.0),
  (7.5, '100', 7.25),
  (7.0, '-115', 7.25),
  (7.5, '-105', 7.375),
  (7.0, '-120', 7.375);

-- Insert lookup: Moneyline Conversion Table (part 1)
INSERT OR IGNORE INTO lookup_moneyline_conversion (point_spread, favorite_moneyline, dog_moneyline, description) VALUES
  (1.0, 116, -104, 'Light favorite'),
  (1.5, 123, -102, NULL),
  (2.0, 130, -108, NULL),
  (2.5, 137, -113, NULL),
  (3.0, -170, 141, 'Strong consensus point'),
  (3.5, -197, 163, NULL),
  (4.0, -210, 174, NULL),
  (4.5, -222, 184, NULL),
  (5.0, -237, 196, NULL),
  (5.5, -252, 208, NULL),
  (6.0, -277, 229, NULL),
  (6.5, -299, 247, NULL),
  (7.0, -335, 277, 'Strong favorite point'),
  (7.5, -368, 305, NULL),
  (8.0, -397, 328, NULL),
  (8.5, -427, 353, NULL),
  (9.0, -441, 365, NULL),
  (9.5, -456, 377, NULL),
  (10.0, -510, 422, NULL),
  (10.5, -561, 464, NULL),
  (11.0, -595, 492, NULL),
  (11.5, -631, 522, NULL),
  (12.0, -657, 543, NULL),
  (12.5, -681, 564, NULL),
  (13.0, -730, 604, NULL),
  (13.5, -781, 646, NULL),
  (14.0, -904, 748, NULL),
  (14.5, -1024, 847, NULL),
  (15.0, -1086, 898, NULL),
  (15.5, -1147, 949, NULL),
  (16.0, -1223, 1012, NULL),
  (16.5, -1300, 1076, NULL),
  (17.0, -1418, 1173, NULL),
  (17.5, -1520, 1257, NULL),
  (18.0, -1664, 1377, NULL),
  (18.5, -1803, 1492, NULL),
  (19.0, -1985, 1642, NULL),
  (19.5, -2182, 1805, NULL),
  (20.0, -2390, 1977, NULL);
