# Project Agent Notes

## Environment Configuration
- The repository does **not** ship a tracked `.env` file. Personal secrets must live in an untracked `.env` you create locally.
- Copy `env.template` to `.env` and fill in the real credentials for your environment. Keep `env.template` as the authoritative key list.
- After template changes, follow the merge workflow documented in [`.codex/AGENTS.md`](.codex/AGENTS.md) to refresh your local `.env` while preserving existing values.

## Additional Guidance
- Detailed instructions for managing environment variables, running `pytest` as a sanity check, and operating within a hybrid Windows/WSL setup are recorded in [`.codex/AGENTS.md`](.codex/AGENTS.md).
- These notes apply repo-wide unless superseded by a more specific `AGENTS.md` in a subdirectory.
