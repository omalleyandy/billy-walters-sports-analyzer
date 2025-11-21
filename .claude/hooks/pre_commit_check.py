#!/usr/bin/env python3
"""
Pre-commit hook to validate code before commits.
Checks for exposed API keys, data validation, and code quality.
"""

import json
import re
import sys
from pathlib import Path


def check_for_api_keys(data: dict) -> list[str]:
    """Check if code contains exposed API keys."""
    errors = []

    # Patterns for common API keys
    patterns = {
        "Anthropic API Key": r"sk-ant-[a-zA-Z0-9-]{95,}",
        "OpenAI API Key": r"sk-[a-zA-Z0-9]{48}",
        "GitHub Token": r"ghp_[a-zA-Z0-9]{36}",
        "Generic API Key": r"['\"]?(?:api[_-]?key|apikey)['\"]?\s*[:=]\s*['\"][^'\"]+['\"]",
    }

    for file_info in data.get("staged_files", []):
        file_path = file_info.get("path", "")

        # Skip .env.example - it should have empty values
        if file_path.endswith(".env.example"):
            continue

        # Read file content if it's a text file
        if file_path.endswith((".py", ".json", ".md", ".txt", ".yml", ".yaml")):
            try:
                content = Path(file_path).read_text()
                for key_type, pattern in patterns.items():
                    if re.search(pattern, content, re.IGNORECASE):
                        errors.append(
                            f"[ERROR] Potential {key_type} found in {file_path}. "
                            "Never commit API keys!"
                        )
            except Exception:
                pass

    return errors


def validate_python_files(data: dict) -> list[str]:
    """Validate Python files have proper structure."""
    errors = []

    for file_info in data.get("staged_files", []):
        file_path = file_info.get("path", "")

        if file_path.endswith(".py"):
            try:
                content = Path(file_path).read_text()

                # Check for type hints in function definitions
                functions = re.findall(r"def\s+(\w+)\s*\([^)]*\):", content)
                if functions and "-> " not in content:
                    errors.append(
                        f"[WARNING]  {file_path}: Consider adding type hints to functions"
                    )

            except Exception as e:
                errors.append(f"[ERROR] Error reading {file_path}: {e}")

    return errors


def main():
    """Main hook execution."""
    try:
        # Read input from stdin
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        print("[ERROR] Invalid JSON input", file=sys.stderr)
        sys.exit(1)

    all_errors = []

    # Run checks
    all_errors.extend(check_for_api_keys(input_data))
    all_errors.extend(validate_python_files(input_data))

    # Output results
    if all_errors:
        print("[*] Pre-commit validation failed:\n")
        for error in all_errors:
            print(error)
        print("\n[INFO] Fix these issues before committing.")
        sys.exit(1)
    else:
        print("[*] Pre-commit checks passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
