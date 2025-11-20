from __future__ import annotations

from typing import Any

from walters_analyzer.llm.client import Message, call_llm
from walters_analyzer.llm.settings import LLMSettings
from walters_analyzer.models.matchup_evaluation import MatchupEvaluation
from walters_analyzer.models.core import BetRecommendation


class WaltersLLMAgent:
    """
    Thin wrapper around the LLM for structured matchup → explanation
    generation.

    Produces a human-readable narrative based on evaluation +
    bet recommendation.
    """

    def __init__(self, settings: LLMSettings | None = None) -> None:
        self.settings = settings or LLMSettings()

    def build_prompt(
        self,
        evaluation: MatchupEvaluation,
        recommendation: BetRecommendation,
    ) -> str:
        """
        Generate the prompt for the LLM using pure text instructions.
        """
        return (
            "You are the analysis layer of the Billy Walters Sports Analyzer.\n"
            "Explain the evaluation and recommendation in clear terms.\n\n"
            f"== MATCHUP EVALUATION ==\n{evaluation.model_dump_json()}\n\n"
            f"== RECOMMENDATION ==\n{recommendation.model_dump_json()}\n\n"
            "Return a concise explanation."
        )

    def explain_matchup(
        self,
        evaluation: MatchupEvaluation,
        recommendation: BetRecommendation,
    ) -> str:
        prompt = self.build_prompt(evaluation, recommendation)
        msg: Message = call_llm(prompt)
        return msg.content
