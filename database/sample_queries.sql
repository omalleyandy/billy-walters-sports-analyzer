-- ============================================================
-- BILLY WALTERS ANALYTICS - SAMPLE SQL QUERIES
-- ============================================================
-- Common analytical queries for sports betting analysis
-- Copy and paste these into pgAdmin 4 Query Tool
-- ============================================================

-- ============================================================
-- 1. WEEKLY BETTING PERFORMANCE
-- ============================================================

-- Overall weekly summary
SELECT
    week,
    COUNT(*) as total_bets,
    SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN result = 'LOSS' THEN 1 ELSE 0 END) as losses,
    ROUND(
        SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END)::NUMERIC /
        NULLIF(SUM(CASE WHEN result IN ('WIN','LOSS') THEN 1 ELSE 0 END), 0) * 100,
        2
    ) as win_pct,
    ROUND(AVG(edge_points), 2) as avg_edge,
    ROUND(AVG(clv), 2) as avg_clv,
    ROUND(SUM(profit_loss), 2) as total_profit,
    ROUND(AVG(roi), 2) as avg_roi
FROM bets b
JOIN games g ON b.game_id = g.game_id
WHERE season = 2025
GROUP BY week
ORDER BY week DESC;

-- ============================================================
-- 2. EDGE PERFORMANCE ANALYSIS
-- ============================================================

-- Performance by edge category
SELECT
    edge_category,
    COUNT(*) as bets,
    ROUND(AVG(edge_points), 2) as avg_edge,
    SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN result = 'LOSS' THEN 1 ELSE 0 END) as losses,
    ROUND(
        SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END)::NUMERIC /
        NULLIF(SUM(CASE WHEN result IN ('WIN','LOSS') THEN 1 ELSE 0 END), 0) * 100,
        2
    ) as win_pct,
    ROUND(AVG(clv), 2) as avg_clv,
    ROUND(AVG(roi), 2) as avg_roi,
    ROUND(SUM(profit_loss), 2) as total_profit
FROM bets b
JOIN games g ON b.game_id = g.game_id
WHERE season = 2025 AND result IN ('WIN', 'LOSS', 'PUSH')
GROUP BY edge_category
ORDER BY avg_edge DESC;

-- Billy Walters expected vs actual win rates
SELECT
    edge_category,
    COUNT(*) as bets,
    CASE edge_category
        WHEN 'MAX' THEN 77.0        -- Expected 77% for 7+ edge
        WHEN 'STRONG' THEN 64.0     -- Expected 64% for 4-7 edge
        WHEN 'MEDIUM' THEN 58.0     -- Expected 58% for 2-4 edge
        WHEN 'WEAK' THEN 54.0       -- Expected 54% for 1-2 edge
    END as expected_win_pct,
    ROUND(
        SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END)::NUMERIC /
        NULLIF(SUM(CASE WHEN result IN ('WIN','LOSS') THEN 1 ELSE 0 END), 0) * 100,
        2
    ) as actual_win_pct,
    ROUND(
        (SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END)::NUMERIC /
        NULLIF(SUM(CASE WHEN result IN ('WIN','LOSS') THEN 1 ELSE 0 END), 0) * 100) -
        CASE edge_category
            WHEN 'MAX' THEN 77.0
            WHEN 'STRONG' THEN 64.0
            WHEN 'MEDIUM' THEN 58.0
            WHEN 'WEAK' THEN 54.0
        END,
        2
    ) as variance
FROM bets b
JOIN games g ON b.game_id = g.game_id
WHERE season = 2025 AND result IN ('WIN', 'LOSS')
GROUP BY edge_category
ORDER BY expected_win_pct DESC;

-- ============================================================
-- 3. CLV (CLOSING LINE VALUE) ANALYSIS
-- ============================================================

-- Weekly CLV metrics
SELECT
    g.week,
    COUNT(*) as total_bets,
    ROUND(AVG(b.clv), 2) as avg_clv,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY b.clv), 2) as median_clv,
    ROUND(
        SUM(CASE WHEN b.clv > 0 THEN 1 ELSE 0 END)::NUMERIC / COUNT(*) * 100,
        2
    ) as positive_clv_pct,
    SUM(CASE WHEN b.clv > 0 AND b.result = 'WIN' THEN 1 ELSE 0 END) as clv_wins,
    SUM(CASE WHEN b.clv > 0 AND b.result = 'LOSS' THEN 1 ELSE 0 END) as clv_losses,
    ROUND(
        SUM(CASE WHEN b.clv > 0 AND b.result = 'WIN' THEN 1 ELSE 0 END)::NUMERIC /
        NULLIF(SUM(CASE WHEN b.clv > 0 AND b.result IN ('WIN','LOSS') THEN 1 ELSE 0 END), 0) * 100,
        2
    ) as clv_win_rate
FROM bets b
JOIN games g ON b.game_id = g.game_id
WHERE b.clv IS NOT NULL AND g.season = 2025
GROUP BY g.week
ORDER BY g.week DESC;

-- CLV distribution
SELECT
    CASE
        WHEN clv >= 3.0 THEN '+3.0 or better (Elite)'
        WHEN clv >= 2.0 THEN '+2.0 to +2.9 (Excellent)'
        WHEN clv >= 1.5 THEN '+1.5 to +1.9 (Professional)'
        WHEN clv >= 1.0 THEN '+1.0 to +1.4 (Good)'
        WHEN clv >= 0 THEN '0 to +0.9 (Positive)'
        WHEN clv >= -1.0 THEN '-0.1 to -0.9 (Slightly Negative)'
        ELSE '-1.0 or worse (Poor)'
    END as clv_range,
    COUNT(*) as bets,
    ROUND(AVG(roi), 2) as avg_roi
FROM bets
WHERE clv IS NOT NULL
GROUP BY clv_range
ORDER BY MIN(clv) DESC;

-- ============================================================
-- 4. WEATHER IMPACT ANALYSIS
-- ============================================================

-- Weather conditions summary
SELECT
    w.weather_category,
    COUNT(*) as games,
    ROUND(AVG(w.temperature), 1) as avg_temp,
    ROUND(AVG(w.wind_speed), 1) as avg_wind,
    ROUND(AVG(w.total_adjustment), 2) as avg_total_adj,
    ROUND(AVG(w.spread_adjustment), 2) as avg_spread_adj
FROM weather w
JOIN games g ON w.game_id = g.game_id
WHERE w.is_actual = TRUE
GROUP BY w.weather_category
ORDER BY avg_total_adj DESC;

-- Weather impact on UNDER bets
SELECT
    CASE
        WHEN w.wind_speed > 20 THEN 'High Wind (>20mph)'
        WHEN w.wind_speed > 15 THEN 'Medium Wind (15-20mph)'
        WHEN w.wind_speed > 10 THEN 'Low Wind (10-15mph)'
        ELSE 'Calm (<10mph)'
    END as wind_category,
    COUNT(*) as bets,
    SUM(CASE WHEN b.result = 'WIN' THEN 1 ELSE 0 END) as wins,
    ROUND(
        SUM(CASE WHEN b.result = 'WIN' THEN 1 ELSE 0 END)::NUMERIC /
        NULLIF(SUM(CASE WHEN b.result IN ('WIN','LOSS') THEN 1 ELSE 0 END), 0) * 100,
        2
    ) as win_pct,
    ROUND(AVG(b.roi), 2) as avg_roi
FROM bets b
JOIN weather w ON b.game_id = w.game_id
WHERE b.bet_type = 'total' AND b.side = 'UNDER' AND w.is_actual = TRUE
GROUP BY wind_category
ORDER BY MIN(w.wind_speed) DESC;

-- Temperature impact on scoring
SELECT
    CASE
        WHEN w.temperature < 20 THEN 'Very Cold (<20°F)'
        WHEN w.temperature < 32 THEN 'Freezing (20-32°F)'
        WHEN w.temperature < 40 THEN 'Cold (32-40°F)'
        WHEN w.temperature < 50 THEN 'Cool (40-50°F)'
        ELSE 'Moderate (50+°F)'
    END as temp_range,
    COUNT(*) as games,
    ROUND(AVG(g.total_points), 1) as avg_total_points,
    ROUND(AVG(w.total_adjustment), 2) as avg_total_adj
FROM games g
JOIN weather w ON g.game_id = w.game_id
WHERE g.total_points IS NOT NULL AND w.is_actual = TRUE
GROUP BY temp_range
ORDER BY MIN(w.temperature);

-- ============================================================
-- 5. INJURY IMPACT ANALYSIS
-- ============================================================

-- QB injuries and their impact
SELECT
    i.injury_status,
    i.player_tier,
    COUNT(DISTINCT i.game_id) as games,
    ROUND(AVG(i.impact_points), 2) as avg_impact,
    COUNT(b.bet_id) as bets_placed,
    SUM(CASE WHEN b.result = 'WIN' THEN 1 ELSE 0 END) as wins,
    ROUND(AVG(b.clv), 2) as avg_clv,
    ROUND(AVG(b.roi), 2) as avg_roi
FROM injuries i
LEFT JOIN bets b ON i.game_id = b.game_id
WHERE i.position = 'QB'
GROUP BY i.injury_status, i.player_tier
ORDER BY avg_impact DESC;

-- Position-specific injury impacts
SELECT
    i.position,
    COUNT(*) as injury_count,
    ROUND(AVG(i.impact_points), 2) as avg_impact,
    MAX(i.impact_points) as max_impact,
    SUM(CASE WHEN i.player_tier = 'ELITE' THEN 1 ELSE 0 END) as elite_players,
    SUM(CASE WHEN i.injury_status = 'OUT' THEN 1 ELSE 0 END) as out_count
FROM injuries i
GROUP BY i.position
ORDER BY avg_impact DESC;

-- ============================================================
-- 6. SITUATIONAL FACTORS (SWEF)
-- ============================================================

-- Division games performance
SELECT
    'Division Games' as game_type,
    COUNT(*) as bets,
    ROUND(AVG(b.edge_points), 2) as avg_edge,
    ROUND(AVG(b.roi), 2) as avg_roi,
    ROUND(AVG(b.clv), 2) as avg_clv
FROM bets b
JOIN situational_factors sf ON b.game_id = sf.game_id
WHERE sf.is_division_game = TRUE
UNION ALL
SELECT
    'Non-Division Games',
    COUNT(*),
    ROUND(AVG(b.edge_points), 2),
    ROUND(AVG(b.roi), 2),
    ROUND(AVG(b.clv), 2)
FROM bets b
JOIN situational_factors sf ON b.game_id = sf.game_id
WHERE sf.is_division_game = FALSE;

-- Rest advantage analysis
SELECT
    CASE
        WHEN sf.days_rest > 7 THEN 'Extra Rest (Bye Week)'
        WHEN sf.days_rest < 7 THEN 'Short Rest (Thursday/Monday)'
        ELSE 'Normal Rest (7 days)'
    END as rest_category,
    COUNT(*) as bets,
    ROUND(AVG(b.edge_points), 2) as avg_edge,
    ROUND(AVG(b.roi), 2) as avg_roi,
    ROUND(AVG(b.clv), 2) as avg_clv
FROM bets b
JOIN situational_factors sf ON b.game_id = sf.game_id
WHERE sf.days_rest IS NOT NULL
GROUP BY rest_category
HAVING COUNT(*) >= 5
ORDER BY avg_roi DESC;

-- Prime time game performance
SELECT
    CASE WHEN sf.is_prime_time THEN 'Prime Time' ELSE 'Regular Time' END as time_slot,
    COUNT(*) as bets,
    ROUND(AVG(b.roi), 2) as avg_roi,
    ROUND(AVG(b.clv), 2) as avg_clv
FROM bets b
JOIN situational_factors sf ON b.game_id = sf.game_id
GROUP BY time_slot;

-- ============================================================
-- 7. LINE MOVEMENT ANALYSIS
-- ============================================================

-- Opening vs closing line movement
SELECT
    g.week,
    g.home_team,
    g.away_team,
    o_open.home_spread as opening_spread,
    o_close.home_spread as closing_spread,
    (o_close.home_spread - o_open.home_spread) as line_movement,
    b.line as our_line,
    b.clv,
    b.result
FROM games g
JOIN odds o_open ON
    g.game_id = o_open.game_id AND
    o_open.odds_type = 'opening' AND
    o_open.sportsbook = 'overtime'
JOIN odds o_close ON
    g.game_id = o_close.game_id AND
    o_close.odds_type = 'closing' AND
    o_close.sportsbook = 'overtime'
LEFT JOIN bets b ON g.game_id = b.game_id
WHERE g.week = 12 AND g.season = 2025
ORDER BY ABS(o_close.home_spread - o_open.home_spread) DESC;

-- ============================================================
-- 8. BET TYPE PERFORMANCE
-- ============================================================

-- Performance by bet type
SELECT
    bet_type,
    COUNT(*) as bets,
    SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
    ROUND(
        SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END)::NUMERIC /
        NULLIF(SUM(CASE WHEN result IN ('WIN','LOSS') THEN 1 ELSE 0 END), 0) * 100,
        2
    ) as win_pct,
    ROUND(AVG(edge_points), 2) as avg_edge,
    ROUND(AVG(clv), 2) as avg_clv,
    ROUND(SUM(profit_loss), 2) as total_profit,
    ROUND(AVG(roi), 2) as avg_roi
FROM bets
WHERE result IN ('WIN', 'LOSS', 'PUSH')
GROUP BY bet_type
ORDER BY avg_roi DESC;

-- ============================================================
-- 9. COMPREHENSIVE GAME ANALYSIS
-- ============================================================

-- Complete game analysis (uses view)
SELECT
    game_id,
    week,
    home_team,
    away_team,
    home_rating,
    away_rating,
    (away_rating - home_rating - 3.0) as predicted_spread,
    opening_spread,
    closing_spread,
    temperature,
    wind_speed,
    weather_category,
    side as bet_side,
    line as bet_line,
    edge_points,
    clv,
    result,
    roi
FROM vw_game_analysis
WHERE week = 12 AND season = 2025
ORDER BY edge_points DESC;

-- ============================================================
-- 10. ROI AND PROFITABILITY
-- ============================================================

-- ROI by week
SELECT
    g.week,
    COUNT(*) as bets,
    ROUND(SUM(b.risk_amount), 2) as total_risked,
    ROUND(SUM(b.profit_loss), 2) as total_profit,
    ROUND(
        SUM(b.profit_loss) / NULLIF(SUM(b.risk_amount), 0) * 100,
        2
    ) as roi_pct,
    ROUND(SUM(b.profit_loss) / COUNT(*), 2) as profit_per_bet
FROM bets b
JOIN games g ON b.game_id = g.game_id
WHERE b.result IN ('WIN', 'LOSS', 'PUSH') AND g.season = 2025
GROUP BY g.week
ORDER BY g.week DESC;

-- Best performing plays (top 10)
SELECT
    g.home_team,
    g.away_team,
    g.game_date,
    b.bet_type,
    b.side,
    b.line,
    b.edge_points,
    b.edge_category,
    b.clv,
    b.result,
    b.roi,
    b.profit_loss
FROM bets b
JOIN games g ON b.game_id = g.game_id
WHERE b.result IN ('WIN', 'LOSS') AND g.season = 2025
ORDER BY b.roi DESC
LIMIT 10;

-- ============================================================
-- 11. CORRELATION ANALYSIS
-- ============================================================

-- Weather + Edge Category correlation
SELECT
    b.edge_category,
    w.weather_category,
    COUNT(*) as bets,
    ROUND(AVG(b.roi), 2) as avg_roi,
    ROUND(AVG(b.clv), 2) as avg_clv
FROM bets b
JOIN weather w ON b.game_id = w.game_id
WHERE w.is_actual = TRUE
GROUP BY b.edge_category, w.weather_category
HAVING COUNT(*) >= 3
ORDER BY b.edge_category, avg_roi DESC;

-- Injury + Weather combined impact
SELECT
    CASE WHEN i.injury_count > 0 THEN 'With Injuries' ELSE 'No Injuries' END as injury_status,
    w.weather_category,
    COUNT(*) as bets,
    ROUND(AVG(b.roi), 2) as avg_roi
FROM bets b
JOIN weather w ON b.game_id = w.game_id
LEFT JOIN (
    SELECT game_id, COUNT(*) as injury_count
    FROM injuries
    WHERE injury_status = 'OUT' AND player_tier IN ('ELITE', 'STARTER')
    GROUP BY game_id
) i ON b.game_id = i.game_id
WHERE w.is_actual = TRUE
GROUP BY injury_status, w.weather_category
HAVING COUNT(*) >= 3
ORDER BY avg_roi DESC;

-- ============================================================
-- 12. DATA QUALITY CHECKS
-- ============================================================

-- Check for missing data
SELECT
    'Games without power ratings' as check_name,
    COUNT(*) as count
FROM games g
LEFT JOIN power_ratings pr ON
    g.season = pr.season AND
    g.week = pr.week AND
    g.home_team = pr.team
WHERE pr.id IS NULL AND g.week = 12
UNION ALL
SELECT
    'Games without odds',
    COUNT(*)
FROM games g
LEFT JOIN odds o ON g.game_id = o.game_id
WHERE o.id IS NULL AND g.week = 12
UNION ALL
SELECT
    'Outdoor games without weather',
    COUNT(*)
FROM games g
LEFT JOIN weather w ON g.game_id = w.game_id
WHERE g.is_outdoor = TRUE AND w.id IS NULL AND g.week = 12;

-- Verify data integrity
SELECT
    table_name,
    row_count
FROM (
    SELECT 'games' as table_name, COUNT(*) as row_count FROM games WHERE week = 12
    UNION ALL
    SELECT 'power_ratings', COUNT(*) FROM power_ratings WHERE week = 12
    UNION ALL
    SELECT 'odds', COUNT(*) FROM odds
    UNION ALL
    SELECT 'bets', COUNT(*) FROM bets
    UNION ALL
    SELECT 'weather', COUNT(*) FROM weather
    UNION ALL
    SELECT 'injuries', COUNT(*) FROM injuries
) data
ORDER BY row_count DESC;

-- ============================================================
-- END OF SAMPLE QUERIES
-- ============================================================

-- USAGE TIPS:
-- 1. Copy queries into pgAdmin 4 Query Tool (Alt+Shift+Q)
-- 2. Modify WHERE clauses to filter by week/season
-- 3. Adjust GROUP BY to analyze different dimensions
-- 4. Save frequently-used queries as Named Queries in pgAdmin
-- 5. Export results to CSV: Query Tool → F8 (Download as CSV)
-- 6. Create custom views for complex queries you run often
