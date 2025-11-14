"""
Run autonomous agent analysis on all NFL games
Generates weekly betting recommendations with ML-powered reasoning
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import json

# Add src to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / ".claude"))

from walters_analyzer.agent_data_loader import AgentDataLoader
from walters_autonomous_agent import WaltersCognitiveAgent, ConfidenceLevel


def format_decision_report(decision, game_data) -> str:
    """Format a single decision as readable text"""
    report = []
    report.append("=" * 80)
    report.append(f"GAME: {game_data['away_team']} @ {game_data['home_team']}")
    report.append("=" * 80)

    # Game info
    report.append(f"\nMarket Spread: {game_data['home_team']} {game_data['spread']:+.1f}")
    report.append(f"Total: {game_data['total']}")
    report.append(f"Predicted Spread: {game_data['predicted_spread']:+.1f}")
    report.append(f"Game Time: {game_data.get('game_time', 'TBD')}")

    # Agent decision
    report.append(f"\n[RECOMMENDATION] {decision.recommendation.upper()}")
    report.append(f"Confidence: {decision.confidence.name} ({decision.confidence.value:.0%})")
    report.append(f"Stake: {decision.stake_percentage:.2f}% of bankroll")
    report.append(f"Expected Value: {decision.expected_value:.2f}%")

    # Reasoning chain (top 3 steps)
    report.append(f"\n[REASONING] Top Factors:")
    for step in decision.reasoning_chain[:3]:
        report.append(f"\n{step.step_number}. {step.description}")
        report.append(f"   Confidence: {step.confidence:.0%}")
        for evidence in step.evidence[:2]:  # Top 2 pieces of evidence
            report.append(f"   - {evidence}")
        report.append(f"   Impact: {step.impact_on_decision}")

    # Risk assessment
    report.append(f"\n[RISK ASSESSMENT]")
    report.append(f"  Overall Risk: {decision.risk_assessment.get('confidence', 0):.0%}")
    report.append(f"  Max Loss: {decision.risk_assessment.get('max_loss', 0):.2f}%")
    report.append(f"  Risk/Reward: {decision.risk_assessment.get('risk_reward_ratio', 0):.2f}")

    report.append("")
    return "\n".join(report)


async def main():
    """Run autonomous agent on all games"""
    print("[AGENT] Billy Walters Autonomous Agent - Weekly Analysis")
    print("=" * 80)
    print()

    # Load data
    print("[LOADING] Loading game data...")
    loader = AgentDataLoader(project_root)
    games = loader.load_all_games()

    if not games:
        print("[ERROR] No games loaded. Check odds and power ratings files.")
        return

    print(f"[OK] Loaded {len(games)} games for analysis")
    print()

    # Initialize agent
    print("[AGENT] Initializing autonomous agent...")
    agent = WaltersCognitiveAgent(initial_bankroll=10000)
    print("[OK] Agent initialized with $10,000 bankroll")
    print()

    # Analyze each game
    decisions = []
    recommendations = []

    print("[ANALYZING] Running agent analysis...")
    print()

    for i, game in enumerate(games, 1):
        try:
            # Run agent analysis
            decision = await agent.make_autonomous_decision(game)
            decisions.append(decision)

            # Track recommendations (non-PASS only)
            if decision.recommendation != "pass":
                recommendations.append({
                    "game": f"{game['away_team']} @ {game['home_team']}",
                    "recommendation": decision.recommendation,
                    "confidence": decision.confidence.name,
                    "stake": decision.stake_percentage,
                    "ev": decision.expected_value,
                    "decision": decision,
                    "game_data": game,
                })

            # Store in agent memory
            agent.memory_bank.remember_decision(decision)

            # Progress indicator
            status = "BET" if decision.stake_percentage > 0 else "PASS"
            print(f"[{i:2d}/{len(games)}] {game['away_team']:30s} @ {game['home_team']:30s} -> {status}")

        except Exception as e:
            print(f"[ERROR] Failed to analyze game {i}: {e}")
            continue

    print()
    print("=" * 80)
    print("[COMPLETE] Agent analysis finished")
    print("=" * 80)
    print()

    # Summary statistics
    total_games = len(decisions)
    bet_count = len(recommendations)
    pass_count = total_games - bet_count

    print(f"[SUMMARY]")
    print(f"  Total Games Analyzed: {total_games}")
    print(f"  Betting Opportunities: {bet_count}")
    print(f"  Pass/No Value: {pass_count}")

    if recommendations:
        avg_stake = sum(r['stake'] for r in recommendations) / len(recommendations)
        avg_ev = sum(r['ev'] for r in recommendations) / len(recommendations)
        print(f"  Average Stake: {avg_stake:.2f}%")
        print(f"  Average EV: {avg_ev:.2f}%")

        # Confidence breakdown
        high_conf = sum(1 for r in recommendations if r['confidence'] in ['HIGH', 'VERY_HIGH'])
        print(f"  High Confidence Bets: {high_conf}")

    print()

    # Display detailed recommendations
    if recommendations:
        print("=" * 80)
        print("[RECOMMENDATIONS] Ranked by Expected Value")
        print("=" * 80)
        print()

        # Sort by EV
        recommendations.sort(key=lambda x: x['ev'], reverse=True)

        for rec in recommendations:
            print(format_decision_report(rec['decision'], rec['game_data']))

        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = project_root / "output" / "agent_analysis"
        output_dir.mkdir(parents=True, exist_ok=True)

        report_file = output_dir / f"agent_recommendations_{timestamp}.txt"
        with open(report_file, "w") as f:
            f.write(f"Billy Walters Autonomous Agent Analysis\n")
            f.write(f"Generated: {datetime.now()}\n")
            f.write(f"\n")
            f.write(f"Total Games: {total_games}\n")
            f.write(f"Recommendations: {bet_count}\n")
            f.write(f"\n")
            f.write("=" * 80 + "\n")
            f.write("RECOMMENDATIONS (Sorted by EV)\n")
            f.write("=" * 80 + "\n\n")

            for rec in recommendations:
                f.write(format_decision_report(rec['decision'], rec['game_data']))
                f.write("\n\n")

        print(f"[SAVED] Report saved to: {report_file}")
        print()

        # Save JSON format
        json_file = output_dir / f"agent_recommendations_{timestamp}.json"
        json_data = [
            {
                "game": rec['game'],
                "recommendation": rec['recommendation'],
                "confidence": rec['confidence'],
                "stake_pct": rec['stake'],
                "expected_value": rec['ev'],
                "spread": rec['game_data']['spread'],
                "total": rec['game_data']['total'],
                "predicted_spread": rec['game_data']['predicted_spread'],
            }
            for rec in recommendations
        ]

        with open(json_file, "w") as f:
            json.dump(json_data, f, indent=2)

        print(f"[SAVED] JSON data saved to: {json_file}")
        print()

    else:
        print("[INFO] No betting opportunities identified by the agent")
        print("      All games were assessed as 'PASS'")
        print()


if __name__ == "__main__":
    asyncio.run(main())
