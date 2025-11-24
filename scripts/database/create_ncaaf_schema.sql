-- ============================================================================
-- NCAAF PostgreSQL Database Schema
-- Created: November 23, 2025
-- Purpose: Store comprehensive NCAA football data for Billy Walters analytics
-- ============================================================================

-- Drop existing tables if they exist (careful in production!)
-- DROP TABLE IF EXISTS ncaaf_team_injuries CASCADE;
-- DROP TABLE IF EXISTS ncaaf_schedules CASCADE;
-- DROP TABLE IF EXISTS ncaaf_power_ratings CASCADE;
-- DROP TABLE IF EXISTS ncaaf_team_stats CASCADE;
-- DROP TABLE IF EXISTS ncaaf_teams CASCADE;

-- ============================================================================
-- TABLE 1: NCAAF Teams (Master Data)
-- ============================================================================

CREATE TABLE ncaaf_teams (
    team_id VARCHAR(10) PRIMARY KEY,
    team_name VARCHAR(100) NOT NULL UNIQUE,
    team_abbreviation VARCHAR(10),
    conference VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ncaaf_teams_name ON ncaaf_teams(team_name);
CREATE INDEX idx_ncaaf_teams_conf ON ncaaf_teams(conference);

-- ============================================================================
-- TABLE 2: Team Statistics (Weekly)
-- ============================================================================

CREATE TABLE ncaaf_team_stats (
    stat_id SERIAL PRIMARY KEY,
    team_id VARCHAR(10) NOT NULL,
    week INT NOT NULL,
    season_year INT NOT NULL,

    -- Offensive Stats
    points_per_game DECIMAL(5,2),
    total_points DECIMAL(8,1),
    passing_yards_per_game DECIMAL(7,2),
    rushing_yards_per_game DECIMAL(7,2),
    total_yards_per_game DECIMAL(8,2),

    -- Defensive Stats
    points_allowed_per_game DECIMAL(5,2),
    passing_yards_allowed_per_game DECIMAL(7,2),
    rushing_yards_allowed_per_game DECIMAL(7,2),
    total_yards_allowed_per_game DECIMAL(8,2),

    -- Advanced Stats
    turnover_margin DECIMAL(3,1),
    third_down_pct DECIMAL(5,2),
    takeaways INT,
    giveaways INT,

    games_played INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (team_id) REFERENCES ncaaf_teams(team_id) ON DELETE CASCADE,
    UNIQUE(team_id, week, season_year)
);

CREATE INDEX idx_ncaaf_stats_team ON ncaaf_team_stats(team_id);
CREATE INDEX idx_ncaaf_stats_week ON ncaaf_team_stats(week, season_year);
CREATE INDEX idx_ncaaf_stats_season ON ncaaf_team_stats(season_year);

-- ============================================================================
-- TABLE 3: Power Ratings
-- ============================================================================

CREATE TABLE ncaaf_power_ratings (
    rating_id SERIAL PRIMARY KEY,
    team_id VARCHAR(10) NOT NULL,
    rating_system VARCHAR(50),
    rating_value DECIMAL(6,2),
    rating_date DATE,
    week INT,
    season_year INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (team_id) REFERENCES ncaaf_teams(team_id) ON DELETE CASCADE,
    UNIQUE(team_id, rating_system, week, season_year)
);

CREATE INDEX idx_ncaaf_ratings_team ON ncaaf_power_ratings(team_id);
CREATE INDEX idx_ncaaf_ratings_system ON ncaaf_power_ratings(rating_system);
CREATE INDEX idx_ncaaf_ratings_date ON ncaaf_power_ratings(rating_date);

-- ============================================================================
-- TABLE 4: Game Schedules
-- ============================================================================

CREATE TABLE ncaaf_schedules (
    game_id VARCHAR(50) PRIMARY KEY,
    home_team_id VARCHAR(10) NOT NULL,
    away_team_id VARCHAR(10) NOT NULL,
    game_date TIMESTAMP,
    week INT,
    season_year INT,
    status VARCHAR(50),
    home_score INT,
    away_score INT,
    location VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (home_team_id) REFERENCES ncaaf_teams(team_id) ON DELETE CASCADE,
    FOREIGN KEY (away_team_id) REFERENCES ncaaf_teams(team_id) ON DELETE CASCADE
);

CREATE INDEX idx_ncaaf_schedule_date ON ncaaf_schedules(game_date);
CREATE INDEX idx_ncaaf_schedule_week ON ncaaf_schedules(week, season_year);
CREATE INDEX idx_ncaaf_schedule_home ON ncaaf_schedules(home_team_id);
CREATE INDEX idx_ncaaf_schedule_away ON ncaaf_schedules(away_team_id);
CREATE INDEX idx_ncaaf_schedule_status ON ncaaf_schedules(status);

-- ============================================================================
-- TABLE 5: Team Injuries
-- ============================================================================

CREATE TABLE ncaaf_team_injuries (
    injury_id SERIAL PRIMARY KEY,
    team_id VARCHAR(10) NOT NULL,
    player_name VARCHAR(100),
    position VARCHAR(20),
    status VARCHAR(50),
    injury_type VARCHAR(100),
    week INT,
    season_year INT,
    scraped_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (team_id) REFERENCES ncaaf_teams(team_id) ON DELETE CASCADE
);

CREATE INDEX idx_ncaaf_injuries_team ON ncaaf_team_injuries(team_id);
CREATE INDEX idx_ncaaf_injuries_week ON ncaaf_team_injuries(week, season_year);
CREATE INDEX idx_ncaaf_injuries_status ON ncaaf_team_injuries(status);

-- ============================================================================
-- Schema Creation Complete
-- ============================================================================
-- 5 tables created with indexes and foreign keys
-- Total storage estimate: ~50MB for full season (117 teams × 18 weeks)
-- ============================================================================
