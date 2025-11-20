from __future__ import annotations

from walters_analyzer.llm.agent import WaltersLLMAgent
from walters_analyzer.pipelines.run_test_pipelines import run_pipeline
from walters_analyzer.models import BetRecommendation, MatchupEvaluation


def main() -> None:
    """
    Run the synthetic test pipeline and send results through the LLM
    for a narrative explanation.
    """
    result = run_pipeline(return_models=True)
    if result is None:
        raise RuntimeError(
            "run_pipeline(return_models=True) returned None; "
            "check pipeline implementation."
        )

    evaluation, recommendation = result
    if not isinstance(evaluation, MatchupEvaluation):
        raise TypeError("Expected MatchupEvaluation from pipeline.")
    if not isinstance(recommendation, BetRecommendation):
        raise TypeError("Expected BetRecommendation from pipeline.")

    agent = WaltersLLMAgent()
    explanation = agent.explain_matchup(
        evaluation=evaluation,
        recommendation=recommendation,
    )

    print("\n=== LLM EXPLANATION ===\n")
    print(explanation)


if __name__ == "__main__":
    main()
