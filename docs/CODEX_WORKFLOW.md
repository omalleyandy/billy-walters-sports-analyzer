# Codex Workflow Guide

This document explains how the Billy Walters Sports Analyzer repo is wired for the Codex CLI so you can get oriented quickly, run the automations, and know which guardrails are in place.

## Entry Points
- `START_HERE.md` – product walkthrough and verification steps.
- `CLAUDE.md` – project guardrails and coding standards (Codex follows these).
- `docs/PROJECT_STRUCTURE.md` – detailed package layout if you need a deeper tour.

## Preflight and Hooks
- Codex runs `.codex/preflight.sh` before each session; it iterates through `hooks/*.sh`.
- Hooks are designed to be fast safety rails: repository info, guardrails on protected files, quality checks, and optional pytest (`hooks/30-pytest.sh`).
- If you need to adjust hook behaviour, edit the shell scripts in `hooks/` and keep them idempotent.

## Commands Directory
- Executables live in `commands/`. Shell scripts (for example `commands/bootstrap`) are invoked directly.
- JSON workflow files (for example `commands/wk-card.json`) capture repeatable `uv run …` pipelines that Codex can replay.
- Add new automations by dropping another file in `commands/` and documenting the intent in the file header comment.

## Environment Expectations
- Python is managed with `uv`; avoid system Python. Use `uv sync` to install deps and `uv run …` for execution.
- Playwright browsers are provisioned by the bootstrap command (`./commands/bootstrap`).
- Secrets stay outside the repo. Use `.env` (ignored) for local values and update `env.template` when new variables are required.

## Validation and Testing
- The preferred smoke test is `uv run python examples/verify_all.py` (see `START_HERE.md`).
- Full test suite: `pytest tests/ -v` or via any JSON command that wraps it.
- Cached data lives in `data/` and `.uv-cache/`; clean these only when you understand the downstream impact.

## When Modifying or Extending
- Follow the rules in `CLAUDE.md`: typed code, retries/backoff for IO, configuration-driven behaviour.
- Reference the quick patterns in `docs/QUICK_REFERENCE.md` before writing new modules.
- If you add new tooling, update this guide and the Codex section in `README.md` so automations stay discoverable.

## Troubleshooting
- If Codex reports a permissions issue, check `.claude/settings.local.json` for the allow/deny lists.
- Hooks failing? Run them individually (`bash hooks/10-guardrails.sh`) to reproduce outside Codex.
- Unexpected behaviour from a JSON command? Open the file to review the exact `uv run` arguments.
