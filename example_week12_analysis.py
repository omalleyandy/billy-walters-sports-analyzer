"""
Real-World Example: Week 12 NFL Game Analysis with S and W Factors

This shows how to use the Billy Walters S and W Factor system
in your actual betting analysis workflow.
"""

from billy_walters_sfactor_reference import (
    SFactorCalculator,
    WFactorCalculator,
    TurfType,
    TeamQuality,
    get_team_time_zone,
    is_warm_weather_team,
    is_dome_team
)

def analyze_week12_game():
    """Analyze a real Week 12 game: Chiefs @ Panthers"""
    
    print("="*70)
    print("WEEK 12 NFL ANALYSIS: Kansas City Chiefs @ Carolina Panthers")
    print("="*70)
    
    # Game info
    home_team = "CAR"  # Panthers
    away_team = "KC"   # Chiefs
    
    print("\n1. TEAM CLASSIFICATIONS")
    print("-" * 70)
    print(f"Home (Panthers): Time Zone={get_team_time_zone(home_team)}, "
          f"Warm Weather={is_warm_weather_team(home_team)}, "
          f"Dome={is_dome_team(home_team)}")
    print(f"Away (Chiefs):   Time Zone={get_team_time_zone(away_team)}, "
          f"Warm Weather={is_warm_weather_team(away_team)}, "
          f"Dome={is_dome_team(away_team)}")
    
    # Panthers S-Factors (Home team)
    print("\n2. PANTHERS S-FACTORS (Home Team)")
    print("-" * 70)
    
    panthers_sf = SFactorCalculator.calculate_complete_sfactors(
        is_home=True,
        team_turf=TurfType.NATURAL_GRASS,
        opponent_turf=TurfType.NATURAL_GRASS,
        same_division=False,
        same_conference=False,  # AFC vs NFC
        coming_off_bye=False,
        team_quality=TeamQuality.BELOW_AVERAGE,  # Panthers 3-7 record
        is_thursday_night=False,
        is_sunday_night=False,
        is_monday_night=False,
        team_time_zone="ET",
        game_time_zone="ET"
    )
    
    print(f"Total S-Factor Points: {panthers_sf.total_points:.1f}")
    print(f"Spread Adjustment: {panthers_sf.spread_adjustment:+.2f} points")
    print(f"Breakdown:")
    for category, value in panthers_sf.breakdown.items():
        if value != 0:
            print(f"  - {category.title()}: {value:+.1f} points")
    
    # Chiefs S-Factors (Away team)
    print("\n3. CHIEFS S-FACTORS (Away Team)")
    print("-" * 70)
    
    chiefs_sf = SFactorCalculator.calculate_complete_sfactors(
        is_home=False,
        team_turf=TurfType.NATURAL_GRASS,
        opponent_turf=TurfType.NATURAL_GRASS,
        same_division=False,
        same_conference=False,  # AFC vs NFC
        coming_off_bye=False,
        team_quality=TeamQuality.GREAT,  # Chiefs 9-1 record
        team_time_zone="CT",
        game_time_zone="ET"
    )
    
    print(f"Total S-Factor Points: {chiefs_sf.total_points:.1f}")
    print(f"Spread Adjustment: {chiefs_sf.spread_adjustment:+.2f} points")
    print(f"Breakdown:")
    for category, value in chiefs_sf.breakdown.items():
        if value != 0:
            print(f"  - {category.title()}: {value:+.1f} points")
    
    # W-Factors (Weather)
    print("\n4. W-FACTORS (Weather Impact)")
    print("-" * 70)
    
    # Charlotte weather in late November (outdoor game)
    game_temp = 52  # Moderate temperature
    
    wf = WFactorCalculator.calculate_complete_wfactors(
        temperature_f=game_temp,
        home_team_warm_weather=is_warm_weather_team(home_team),
        visiting_team_warm_weather=is_warm_weather_team(away_team),
        home_team_dome=is_dome_team(home_team),
        visiting_team_dome=is_dome_team(away_team),
        is_raining=False,
        wind_speed_mph=8  # Light wind
    )
    
    print(f"Game Temperature: {game_temp}F")
    print(f"Total W-Factor Points: {wf.total_points:.1f}")
    print(f"Spread Adjustment: {wf.spread_adjustment:+.2f} points")
    print(f"Breakdown:")
    for category, value in wf.breakdown.items():
        if value != 0:
            print(f"  - {category.title()}: {value:+.1f} points")
    
    # Calculate net advantage
    print("\n5. NET S AND W FACTOR ADVANTAGE")
    print("-" * 70)
    
    net_sfactor = panthers_sf.spread_adjustment - chiefs_sf.spread_adjustment
    net_total = net_sfactor + wf.spread_adjustment
    
    print(f"Panthers S-Factor advantage: {panthers_sf.spread_adjustment:+.2f}")
    print(f"Chiefs S-Factor advantage:   {chiefs_sf.spread_adjustment:+.2f}")
    print(f"Net S-Factor to Panthers:    {net_sfactor:+.2f}")
    print(f"W-Factor adjustment:         {wf.spread_adjustment:+.2f}")
    print(f"\nTOTAL NET ADJUSTMENT:        {net_total:+.2f} points to Panthers")
    
    # Apply to spread prediction
    print("\n6. APPLY TO BETTING ANALYSIS")
    print("-" * 70)
    
    # Example: Your power ratings say Chiefs should be -9.5
    base_predicted_spread = -9.5  # Panthers +9.5
    market_spread = -11.0  # Current market: Chiefs -11
    
    # Adjust for S and W factors
    adjusted_predicted_spread = base_predicted_spread - net_total  # Subtract because it's Panthers advantage
    
    print(f"Base Predicted Spread (from power ratings): Panthers {base_predicted_spread:+.1f}")
    print(f"S/W Factor Adjustment:                      {net_total:+.2f} to Panthers")
    print(f"Adjusted Predicted Spread:                  Panthers {adjusted_predicted_spread:+.1f}")
    print(f"Market Spread:                              Panthers {-market_spread:+.1f}")
    
    # Calculate edge
    edge = adjusted_predicted_spread - (-market_spread)
    
    print(f"\nEDGE: {abs(edge):.1f} points")
    if edge > 0:
        print(f"RECOMMENDATION: Bet Panthers +{-market_spread} (Panthers undervalued)")
    elif edge < 0:
        print(f"RECOMMENDATION: Bet Chiefs {market_spread} (Chiefs undervalued)")
    else:
        print(f"RECOMMENDATION: No bet (line is fair)")
    
    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    
    # Billy Walters principle
    print("\nBilly Walters Principle:")
    print("Average S-Factor: 3.2 points per team = 0.64 spread adjustment")
    print(f"This game S-Factor: {panthers_sf.total_points + chiefs_sf.total_points:.1f} points = "
          f"{abs(net_sfactor):.2f} spread adjustment")
    
    if abs(net_sfactor) > 1.0:
        print("NOTE: Above-average S-Factor situation (>1.0 spread adjustment)")
    
    return net_total

if __name__ == "__main__":
    adjustment = analyze_week12_game()
    print(f"\nFinal S/W Factor Adjustment: {adjustment:+.2f} points")
    print("\nThis adjustment should be applied to your power rating spread!")
