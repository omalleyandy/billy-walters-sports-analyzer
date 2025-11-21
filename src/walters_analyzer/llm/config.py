from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseSettings):
    """
    Configuration for the Walters LLM layer.

    Reads from environment variables, with reasonable defaults.
    """

    anthropic_api_key: str = Field(
        alias="ANTHROPIC_API_KEY",
        description="API key for Anthropic.",
    )
    model: str = Field(
        default="claude-3-5-sonnet-latest",
        description="Default Anthropic model name.",
    )
    max_output_tokens: int = Field(
        default=2048,
        description="Max output tokens per response.",
    )

    model_config = SettingsConfigDict(
        env_prefix="BWSA_LLM_",
        populate_by_name=True,
        env_file=".env",
        env_file_encoding="utf-8",
    )
