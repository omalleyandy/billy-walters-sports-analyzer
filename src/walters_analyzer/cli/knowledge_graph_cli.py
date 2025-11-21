# src/walters_analyzer/cli/knowledge_graph_cli.py

import click
from walters_analyzer.models.core import BetRecommendation
from walters_analyzer.schemas.validators import BetRecommendationValidator


@click.command()
@click.option(
    "--recommendation-id", required=True, help="Unique recommendation identifier"
)
@click.option("--game-id", required=True, help="Game ID for this recommendation")
@click.option(
    "--edge-percentage",  # ← NEW: edge_percentage instead of edge_percent
    required=True,
    type=float,
    help="Estimated edge as percentage (e.g., 6.5 for 6.5%)",
)
@click.option(
    "--price",  # ← NEW: price instead of odds
    type=int,
    help="American odds (e.g., -110, +120)",
)
@click.option(
    "--stake-fraction",  # ← NEW: stake_fraction instead of stake_percentage
    required=True,
    type=float,
    help="Fraction of bankroll to stake (0.0 to 0.03)",
)
@click.option("--bankroll", type=float, help="Bankroll amount in dollars")
@click.option("--is-play", is_flag=True, help="Whether to actually make this bet")
def create_recommendation(
    recommendation_id: str,
    game_id: str,
    edge_percentage: float,
    price: int | None,
    stake_fraction: float,
    bankroll: float | None,
    is_play: bool,
):
    """Create and validate a bet recommendation."""

    # Create recommendation object
    rec = BetRecommendation(
        recommendation_id=recommendation_id,
        game_id=game_id,
        edge_percentage=edge_percentage,
        price=price,
        stake_fraction=stake_fraction,
        bankroll=bankroll,
        is_play=is_play,
        bet_type="spread",
        side="home",
        rationale="Created via CLI",
    )

    # Validate
    validator = BetRecommendationValidator()
    is_valid, message = validator.validate_full_recommendation(rec)

    if is_valid:
        click.echo(f"✓ Recommendation created: {rec.recommendation_id}")
        click.echo(f"  Edge: {rec.edge_percentage}%")
        click.echo(f"  Stake: {rec.stake_fraction * 100:.1f}% of bankroll")
        click.echo(f"  Play: {'YES' if rec.is_play else 'NO'}")
    else:
        click.echo(f"✗ Validation failed: {message}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    create_recommendation()
