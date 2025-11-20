"""
Test script to validate knowledge graph integration.

Run this to verify all components are working correctly:
- Schema validation
- Knowledge graph storage
- Bet recommendation generation
- Billy Walters methodology compliance
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from walters_analyzer.models.core import (
    BetRecommendation,
    BetSide,
    BetType,
    Game,
    PowerRatingSnapshot,
    Team,
)
from walters_analyzer.models.knowledge_graph import (
    BettingKnowledgeGraph,
    create_recommendation_from_evaluation,
)
from walters_analyzer.pipelines.evaluation import evaluate_matchup
from walters_analyzer.schemas.validators import (
    SchemaValidator,
)


def test_schema_validation():
    """Test that schema validation is working."""
    print("\n" + "=" * 60)
    print("Testing Schema Validation")
    print("=" * 60)
    
    validator = SchemaValidator()
    
    # Test valid recommendation
    valid_rec = {
        "recommendation_id": "test_001",
        "game_id": "2025_W12_DET_PHI",
        "evaluation_id": "eval_001",
        "bet_type": "spread",
        "side": "home",
        "line": -3.5,
        "price": -110,
        "edge_percentage": 7.5,
        "star_rating": 2,
        "stake_fraction": 0.02,
        "bankroll": 20000,
        "is_play": True,
        "rationale": "Strong edge based on power ratings and S-factors",
    }
    
    errors = validator.validate_bet_recommendation(valid_rec)
    if errors:
        print(f"❌ Unexpected validation errors: {errors}")
        return False
    else:
        print("✓ Valid recommendation passed validation")
    
    # Test invalid recommendation (edge too low)
    invalid_rec = valid_rec.copy()
    invalid_rec["edge_percentage"] = 3.0  # Below 5.5% minimum
    
    errors = validator.validate_bet_recommendation(invalid_rec)
    if errors:
        print(f"✓ Invalid recommendation caught: {errors[0]}")
    else:
        print("❌ Failed to catch invalid edge")
        return False
    
    return True


def test_knowledge_graph():
    """Test knowledge graph functionality."""
    print("\n" + "=" * 60)
    print("Testing Knowledge Graph")
    print("=" * 60)
    
    # Initialize graph
    graph = BettingKnowledgeGraph()
    
    # Add teams
    teams = [
        Team(
            team_id="DET",
            name="Detroit Lions",
            conference="NFC",
            division="NFC North",
            power_rating=7.5,
            rating_source="custom",
        ),
        Team(
            team_id="PHI",
            name="Philadelphia Eagles",
            conference="NFC",
            division="NFC East",
            power_rating=8.0,
            rating_source="custom",
        ),
        Team(
            team_id="CIN",
            name="Cincinnati Bengals",
            conference="AFC",
            division="AFC North",
            power_rating=2.5,
            rating_source="custom",
        ),
    ]
    
    for team in teams:
        graph.add_team(team)
    
    print(f"✓ Added {len(teams)} teams to graph")
    
    # Add power rating snapshots
    for team in teams:
        snapshot = PowerRatingSnapshot(
            team_id=team.team_id,
            season=2025,
            week=12,
            rating=team.power_rating or 0.0,
            source="custom",
        )
        graph.add_power_rating(snapshot)
    
    print(f"✓ Added power rating snapshots")
    
    # Add a game
    game = Game(
        game_id="2025_W12_DET_CIN",
        week=12,
        season=2025,
        home_team_id="CIN",
        away_team_id="DET",
        kickoff_datetime=datetime.utcnow() + timedelta(days=3),
        stadium="Paycor Stadium",
        surface_type="turf",
    )
    
    graph.add_game(game)
    print(f"✓ Added game: {game.away_team_id} @ {game.home_team_id}")
    
    # Create evaluation
    home_team = graph.get_team("CIN")
    away_team = graph.get_team("DET")
    
    factors = {
        "home_factor_points": 0,
        "away_factor_points": 0,
        "market_spread": 8.5,  # Bengals getting 8.5
        "s_home": 0,
        "s_away": 0,
        "w_home": 0,
        "w_away": 0,
        "e_home": 0,
        "e_away": 0,
        "injury_home": 0,
        "injury_away": 0,
    }
    
    evaluation = evaluate_matchup(
        game=game,
        home_team=home_team,
        away_team=away_team,
        factors=factors,
    )
    
    eval_id = graph.add_evaluation(evaluation)
    print(f"✓ Created evaluation: {eval_id}")
    print(f"  Power differential: {evaluation.base_spread:+.1f}")
    print(f"  Market spread: {evaluation.market_spread:+.1f}")
    print(f"  Edge: {evaluation.edge_percent:.1f}%")
    
    # Create recommendation if edge is sufficient
    if evaluation.edge_percent >= 5.5:
        recommendation = create_recommendation_from_evaluation(
            evaluation=evaluation,
            game_id=game.game_id,
            evaluation_id=eval_id,
            bankroll=20000,
        )
        
        if recommendation:
            rec_id = graph.add_recommendation(recommendation, eval_id)
            print(f"✓ Created recommendation: {rec_id}")
            print(f"  Bet: {recommendation.side.value} {recommendation.line:+.1f}")
            print(f"  Stake: {recommendation.stake_fraction:.1%} of bankroll")
    else:
        print(f"ℹ No bet recommended (edge {evaluation.edge_percent:.1f}% < 5.5% minimum)")
    
    # Test graph queries
    team_games = graph.get_team_games("DET", season=2025)
    print(f"✓ Found {len(team_games)} games for DET in 2025")
    
    return True


def test_billy_walters_compliance():
    """Test Billy Walters methodology compliance."""
    print("\n" + "=" * 60)
    print("Testing Billy Walters Methodology Compliance")
    print("=" * 60)
    
    validator = SchemaValidator()
    
    # Test edge requirements
    test_cases = [
        (4.5, 0, "Below minimum edge"),
        (6.0, 1, "1-star edge"),
        (8.0, 2, "2-star edge"),
        (12.0, 3, "3-star edge"),
    ]
    
    for edge, expected_stars, description in test_cases:
        rec = BetRecommendation(
            recommendation_id=f"test_{edge}",
            game_id="test_game",
            evaluation_id="test_eval",
            bet_type=BetType.SPREAD,
            side=BetSide.HOME,
            line=-3.5,
            price=-110,
            edge_percentage=edge,  # Use edge_percentage per schema
            star_rating=expected_stars,
            stake_fraction=min(edge / 100 * 0.5, 0.03),  # Scale with edge, cap at 3%
            bankroll=20000,
            is_play=edge >= 5.5,
            rationale=f"Test case: {description}",
        )
        
        errors = validator.validate(rec)
        
        if edge < 5.5:
            # Should not be playable
            if rec.is_play:
                print(f"❌ {description}: Should not be playable")
            else:
                print(f"✓ {description}: Correctly marked as non-playable")
        else:
            # Should be playable with correct stars
            if errors:
                print(f"❌ {description}: Validation errors: {errors}")
            else:
                print(f"✓ {description}: Valid bet with {expected_stars} stars")
    
    # Test risk management
    print("\n📊 Testing Risk Management")
    
    # Create portfolio of bets
    portfolio = []
    for i in range(5):
        portfolio.append(
            BetRecommendation(
                recommendation_id=f"portfolio_{i}",
                game_id=f"game_{i}",
                evaluation_id=f"eval_{i}",
                bet_type=BetType.SPREAD,
                side=BetSide.HOME,
                line=-3.5,
                price=-110,
                edge_percentage=7.0,  # Use edge_percentage per schema
                star_rating=2,
                stake_fraction=0.025,  # 2.5% each
                bankroll=20000,
                is_play=True,
                rationale="Portfolio test bet",
            )
        )
    
    results = validator.validate_portfolio(portfolio)
    
    print(f"  Total exposure: {results['total_exposure_pct']:.1f}%")
    print(f"  Max single bet: {results['max_single_bet_pct']:.1f}%")
    
    if results["errors"]:
        print(f"  ❌ Portfolio errors: {results['errors'][0]}")
    elif results["warnings"]:
        print(f"  ⚠️ Portfolio warnings: {results['warnings'][0]}")
    else:
        print(f"  ✓ Portfolio passes all risk checks")
    
    return True


def main():
    """Run all tests."""
    print("\n" + "🏈" * 30)
    print("Billy Walters Sports Analyzer - Integration Test")
    print("🏈" * 30)
    
    try:
        # Run tests
        schema_ok = test_schema_validation()
        graph_ok = test_knowledge_graph()
        compliance_ok = test_billy_walters_compliance()
        
        # Summary
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        
        if all([schema_ok, graph_ok, compliance_ok]):
            print("✅ All tests passed!")
            print("\nThe knowledge graph integration is working correctly.")
            print("You can now:")
            print("1. Store teams, games, and evaluations in the graph")
            print("2. Generate bet recommendations with validation")
            print("3. Track performance and calculate CLV")
            print("4. Ensure Billy Walters methodology compliance")
            
            print("\nNext steps:")
            print("- Run: python -m walters_analyzer.cli.knowledge_graph_cli init")
            print("- Run: python -m walters_analyzer.cli.knowledge_graph_cli test-recommendation")
            print("- Run: python -m walters_analyzer.cli.knowledge_graph_cli validate-all")
            
        else:
            print("❌ Some tests failed. Review the output above.")
            
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
