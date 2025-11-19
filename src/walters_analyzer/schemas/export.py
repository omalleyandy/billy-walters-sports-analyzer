from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping, Type

from pydantic import BaseModel

from walters_analyzer.models.core import (
    BetRecommendation,
    Game,
    MatchupEvaluation,
    PowerRatingSnapshot,
    Team,
)


MODELS: Mapping[str, Type[BaseModel]] = {
    "team": Team,
    "game": Game,
    "power_rating_snapshot": PowerRatingSnapshot,
    "matchup_evaluation": MatchupEvaluation,
    "bet_recommendation": BetRecommendation,
}


def export_schemas(output_dir: Path | None = None) -> None:
    """
    Export Pydantic JSON Schemas for all core models.

    Example:
        uv run python -m walters_analyzer.schemas.export -o src/walters_analyzer/schemas
    """
    if output_dir is None:
        output_dir = Path(__file__).parent

    output_dir.mkdir(parents=True, exist_ok=True)

    for name, model in MODELS.items():
        schema = model.model_json_schema()
        path = output_dir / f"{name}.schema.json"
        path.write_text(json.dumps(schema, indent=2), encoding="utf-8")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Export JSON Schemas for core Billy Walters models."
    )
    parser.add_argument(
        "-o",
        "--out-dir",
        type=Path,
        default=Path(__file__).parent,
        help="Directory to write *.schema.json files into.",
    )
    args = parser.parse_args()
    export_schemas(args.out_dir)


if __name__ == "__main__":
    main()
