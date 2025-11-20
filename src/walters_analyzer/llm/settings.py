# src/walters_analyzer/llm/settings.py

from typing import Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseSettings):
    """
    Central config for the Walters Analyzer LLM layer.

    Reads from environment variables:
      - LLM_PROVIDER          (anthropic|openai)
      - ANTHROPIC_API_KEY
      - OPENAI_API_KEY
      - LLM_MODEL_NAME
      - LLM_TEMPERATURE
      - LLM_MAX_TOKENS
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    provider: Literal["anthropic", "openai"] = Field(
        default="anthropic",
        alias="LLM_PROVIDER",
    )

    # Anthropic
    anthropic_api_key: Optional[str] = Field(
        default=None,
        alias="ANTHROPIC_API_KEY",
    )

    # OpenAI (kept for future if you ever want a dual-provider setup)
    openai_api_key: Optional[str] = Field(
        default=None,
        alias="OPENAI_API_KEY",
    )

    model_name: str = Field(
        default="claude-3-5-sonnet-latest",
        alias="LLM_MODEL_NAME",
    )

    temperature: float = Field(
        default=0.3,
        alias="LLM_TEMPERATURE",
    )

    max_tokens: int = Field(
        default=512,
        alias="LLM_MAX_TOKENS",
    )
