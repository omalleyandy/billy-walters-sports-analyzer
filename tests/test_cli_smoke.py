import subprocess
import sys


def test_cli_help_runs():
    """Ensure the CLI boots and prints help without network calls."""

    result = subprocess.run(
        [sys.executable, "-m", "walters_analyzer.cli", "--help"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert result.returncode == 0
    output = (result.stdout + result.stderr).lower()
    assert "usage:" in output
    assert "walters-analyzer" in output
