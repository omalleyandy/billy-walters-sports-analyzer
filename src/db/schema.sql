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

-- Insert base leagues
INSERT OR IGNORE INTO leagues (id, name, display_name) VALUES
  (1, 'NFL', 'National Football League'),
  (2, 'NCAAF', 'College Football');
