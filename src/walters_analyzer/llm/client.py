# src/walters_analyzer/llm/client.py

from dataclasses import dataclass

from anthropic import Anthropic

from walters_analyzer.llm.settings import LLMSettings


@dataclass
class Message:
    role: str
    content: str


settings = LLMSettings()

if settings.provider != "anthropic":
    raise RuntimeError("LLM_PROVIDER must be 'anthropic' for this build.")

if not settings.anthropic_api_key:
    raise RuntimeError(
        "ANTHROPIC_API_KEY is not set. Please set it in your env or .env file."
    )

_client = Anthropic(api_key=settings.anthropic_api_key)


def call_llm(prompt: str) -> Message:
    """
    Thin wrapper around Anthropic's Messages API.

    If the API call fails (no credits, rate limits, etc.), we return
    a stub explanation instead of raising, so the CLI can complete.
    """
    try:
        resp = _client.messages.create(
            model=settings.model_name,
            max_tokens=settings.max_tokens,
            temperature=settings.temperature,
            messages=[
                {"role": "user", "content": prompt},
            ],
        )

        text = resp.content[0].text
        return Message(role="assistant", content=text)

    except Exception as exc:
        # Fail-soft: keep the numeric engine working even when LLM is unavailable
        fallback = (
            "LLM explanation is currently disabled (no API credits available).\n\n"
            "Numeric evaluation and bet recommendation above are still valid; "
            "this section will show a narrative breakdown once LLM access is restored."
        )

        return Message(role="assistant", content=fallback)
