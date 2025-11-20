from importlib.resources import files

__all__ = [
    "load_system_prompt",
    "load_tool_spec",
]


def load_system_prompt() -> str:
    return (files(__package__) / "bwsa-system-prompt.txt").read_text(encoding="utf-8")


def load_tool_spec(
    name: str = "billy_walters_sports_analyzer.json",
) -> str:
    return (files(__package__) / name).read_text(encoding="utf-8")
