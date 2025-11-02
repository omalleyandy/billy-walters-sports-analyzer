# Repository Agent Guide

This repository uses `env.template` as the canonical list of environment variables. Follow this workflow whenever the template changes or you onboard a new environment:

1. **Back up your secrets.** Copy your personal `.env` to `.env.backup` before making changes so you can recover your values if needed.
2. **Review template updates.** Compare the new `env.template` with your backup to see which keys were added, removed, or renamed.
3. **Stage a merged file.** Duplicate `env.template` (e.g., `cp env.template .env.new`) to preserve its comments and ordering.
4. **Reapply real values.** Paste values from `.env.backup` into `.env.new` for existing keys. Provide values for new keys and remove obsolete ones only after confirming they are no longer required.
5. **Optional helper script.** If the list is long, adapt the Python snippet below to automate the merge:

   ```python
   from pathlib import Path

   def load_env(path: Path) -> dict[str, str]:
       data: dict[str, str] = {}
       for line in path.read_text().splitlines():
           stripped = line.strip()
           if not stripped or stripped.startswith("#") or "=" not in stripped:
               continue
           key, value = stripped.split("=", 1)
           data[key.strip()] = value.strip()
       return data

   template_path = Path("env.template")
   backup_path = Path(".env.backup")
   merged_path = Path(".env.new")

   template_vars = load_env(template_path)
   backup_vars = load_env(backup_path)

   merged_lines: list[str] = []
   for raw_line in template_path.read_text().splitlines():
       if not raw_line or raw_line.lstrip().startswith("#") or "=" not in raw_line:
           merged_lines.append(raw_line)
           continue
       key, _ = raw_line.split("=", 1)
       value = backup_vars.get(key, template_vars.get(key, ""))
       merged_lines.append(f"{key}={value}")

   merged_path.write_text("\n".join(merged_lines) + "\n")
   ```

6. **Validate.** Replace `.env` with `.env.new` once reviewed, then run the application or tests to ensure everything loads correctly. Never commit your personal `.env` or other files containing secrets.

These instructions apply to the entire repository unless overridden by a more specific `AGENTS.md` in a subdirectory.
