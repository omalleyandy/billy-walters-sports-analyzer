-- ============================================================
-- NFL DATA EXTENSIONS TO BILLY WALTERS SCHEMA
-- Version: 1.0.0
-- Created: 2025-11-24
-- Description: Extensions for NFL 2025 season data storage
-- ============================================================

-- NFL Team Statistics: Weekly cumulative statistics
-- Stores game-by-game and cumulative statistics for each NFL team
CREATE TABLE IF NOT EXISTS nfl_team_stats (
    id SERIAL PRIMARY KEY,

    -- Identification
    team_abbr VARCHAR(10) NOT NULL,
    team_name VARCHAR(100) NOT NULL,
    week INT NOT NULL CHECK (week BETWEEN 1 AND 18),
    season_year INT NOT NULL,

    -- Offensive Stats (Per Game Averages)
    points_per_game DECIMAL(5, 2),
    total_points INT,
    passing_yards_per_game DECIMAL(7, 2),
    rushing_yards_per_game DECIMAL(7, 2),
    total_yards_per_game DECIMAL(7, 2),

    -- Defensive Stats (Per Game Averages)
    points_allowed_per_game DECIMAL(5, 2),
    passing_yards_allowed_per_game DECIMAL(7, 2),
    rushing_yards_allowed_per_game DECIMAL(7, 2),
    total_yards_allowed_per_game DECIMAL(7, 2),

    -- Advanced Stats
    turnover_margin INT,
    third_down_pct DECIMAL(5, 2),
    takeaways INT,
    giveaways INT,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_nfl_team_week UNIQUE (team_abbr, week, season_year),
    CONSTRAINT valid_season CHECK (season_year >= 2000)
);

-- Create indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_nfl_team_stats_team_season
    ON nfl_team_stats(team_abbr, season_year);

CREATE INDEX IF NOT EXISTS idx_nfl_team_stats_week
    ON nfl_team_stats(week, season_year);

CREATE INDEX IF NOT EXISTS idx_nfl_team_stats_season
    ON nfl_team_stats(season_year);

-- ============================================================
-- ANALYTICAL VIEWS
-- ============================================================

-- NFL Average Stats by Week (for power rating enhancement)
CREATE OR REPLACE VIEW nfl_weekly_averages AS
SELECT
    week,
    season_year,
    ROUND(AVG(points_per_game)::NUMERIC, 2) AS avg_ppg,
    ROUND(AVG(points_allowed_per_game)::NUMERIC, 2) AS avg_ppag,
    ROUND(AVG(total_yards_per_game)::NUMERIC, 2) AS avg_total_yards,
    ROUND(AVG(total_yards_allowed_per_game)::NUMERIC, 2) AS avg_total_yards_allowed,
    COUNT(*) AS teams_count
FROM nfl_team_stats
GROUP BY week, season_year
ORDER BY season_year DESC, week;

-- NFL Team Performance Ranking by Week
CREATE OR REPLACE VIEW nfl_team_rankings_by_week AS
SELECT
    week,
    season_year,
    team_name,
    team_abbr,
    points_per_game,
    points_allowed_per_game,
    total_yards_per_game,
    (total_yards_per_game - total_yards_allowed_per_game) AS yards_differential,
    ROW_NUMBER() OVER (PARTITION BY week, season_year ORDER BY points_per_game DESC)
        AS ppg_rank,
    ROW_NUMBER() OVER (PARTITION BY week, season_year ORDER BY points_allowed_per_game ASC)
        AS ppag_rank
FROM nfl_team_stats
ORDER BY season_year DESC, week, ppg_rank;

-- ============================================================
-- DATA VALIDATION PROCEDURES
-- ============================================================

-- Function to validate NFL team stats completeness
CREATE OR REPLACE FUNCTION validate_nfl_team_stats(p_season INT, p_week INT)
RETURNS TABLE (
    team_abbr VARCHAR,
    team_name VARCHAR,
    missing_fields INT,
    completeness_pct NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        nts.team_abbr,
        nts.team_name,
        (
            CASE WHEN nts.points_per_game IS NULL THEN 1 ELSE 0 END +
            CASE WHEN nts.points_allowed_per_game IS NULL THEN 1 ELSE 0 END +
            CASE WHEN nts.total_yards_per_game IS NULL THEN 1 ELSE 0 END +
            CASE WHEN nts.total_yards_allowed_per_game IS NULL THEN 1 ELSE 0 END
        ) AS missing_fields,
        ROUND(
            (100.0 * (4 - (
                CASE WHEN nts.points_per_game IS NULL THEN 1 ELSE 0 END +
                CASE WHEN nts.points_allowed_per_game IS NULL THEN 1 ELSE 0 END +
                CASE WHEN nts.total_yards_per_game IS NULL THEN 1 ELSE 0 END +
                CASE WHEN nts.total_yards_allowed_per_game IS NULL THEN 1 ELSE 0 END
            )) / 4.0)::NUMERIC,
            1
        ) AS completeness_pct
    FROM nfl_team_stats nts
    WHERE nts.season_year = p_season
        AND nts.week = p_week
    ORDER BY completeness_pct DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to check for missing teams in a given week
CREATE OR REPLACE FUNCTION check_nfl_coverage(p_season INT, p_week INT)
RETURNS TABLE (
    total_games INT,
    unique_teams INT,
    expected_teams INT,
    coverage_pct NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        (SELECT COUNT(DISTINCT CASE
            WHEN g.league = 'NFL' THEN 1
        END) * 2
        FROM games g
        WHERE g.season = p_season
            AND g.week = p_week
            AND g.league = 'NFL'
        ) AS total_games,
        COUNT(DISTINCT team_abbr)::INT AS unique_teams,
        (SELECT COUNT(DISTINCT CASE
            WHEN g.league = 'NFL' THEN 1
        END) * 2
        FROM games g
        WHERE g.season = p_season
            AND g.week = p_week
            AND g.league = 'NFL'
        ) AS expected_teams,
        ROUND(
            100.0 * COUNT(DISTINCT team_abbr) / (
                SELECT COUNT(DISTINCT CASE
                    WHEN g.league = 'NFL' THEN 1
                END) * 2
                FROM games g
                WHERE g.season = p_season
                    AND g.week = p_week
                    AND g.league = 'NFL'
            ),
            1
        ) AS coverage_pct
    FROM nfl_team_stats
    WHERE season_year = p_season
        AND week = p_week;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- NOTES FOR POWER RATING ENHANCEMENT
-- ============================================================
-- These NFL team statistics can enhance Billy Walters power ratings:
--
-- 1. OFFENSIVE EFFICIENCY:
--    adjusted_ppg = (points_per_game - league_avg_ppg) / league_std_dev
--
-- 2. DEFENSIVE EFFICIENCY:
--    adjusted_ppag = (points_allowed_per_game - league_avg_ppag) / league_std_dev
--
-- 3. YARDS DIFFERENTIAL:
--    yards_eff = (total_yards_per_game - total_yards_allowed_per_game) / league_avg_diff
--
-- 4. TREND ANALYSIS:
--    recent_form = (current_week_ppg - (week-1)_ppg) weighted 0.5
--
-- Example: Enhanced Power Rating Formula
-- enhanced_rating = base_rating +
--     (ppg_deviation * 0.15) +
--     (ppag_deviation * 0.15) +
--     (yards_differential * 0.05) +
--     (recent_form * 0.10)
