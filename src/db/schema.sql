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

-- ============================================================
-- INSERT BASE DATA
-- ============================================================

-- Insert base leagues
INSERT OR IGNORE INTO leagues (id, name, display_name) VALUES
  (1, 'NFL', 'National Football League'),
  (2, 'NCAAF', 'College Football');
