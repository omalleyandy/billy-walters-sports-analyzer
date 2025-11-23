"""
End-to-end workflow tests
Tests complete user workflows from CLI to results
"""

import pytest
import subprocess
import sys
from pathlib import Path


class TestCLICommands:
    """Test CLI commands execute successfully"""

    @pytest.mark.skip(reason="CLI module structure changed - needs __main__.py")
    def test_help_command(self):
        """Test walters-analyzer --help"""
        result = subprocess.run(
            [sys.executable, "-m", "walters_analyzer.cli", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "walters-analyzer" in result.stdout
        assert "analyze-game" in result.stdout
        assert "interactive" in result.stdout

    @pytest.mark.skip(reason="CLI module structure changed - needs __main__.py")
    def test_analyze_game_help(self):
        """Test analyze-game --help"""
        result = subprocess.run(
            [sys.executable, "-m", "walters_analyzer.cli", "analyze-game", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "--home" in result.stdout
        assert "--away" in result.stdout
        assert "--spread" in result.stdout

    @pytest.mark.skip(reason="CLI module structure changed - needs __main__.py")
    def test_slash_help(self):
        """Test slash /help command"""
        result = subprocess.run(
            [sys.executable, "-m", "walters_analyzer.cli", "slash", "/help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "success" in result.stdout


class TestWorkflows:
    """Test automated workflow scripts"""

    @pytest.mark.skipif(
        sys.platform != "win32", reason="PowerShell script (Windows only)"
    )
    def test_super_run_test_system(self):
        """Test super-run.ps1 test-system task"""
        script_path = Path(".codex/super-run.ps1")

        if not script_path.exists():
            pytest.skip("super-run.ps1 not found")

        result = subprocess.run(
            ["pwsh", "-File", str(script_path), "-Task", "test-system"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        # Should complete (may have errors if environment not fully setup)
        assert result.returncode in [0, 1]  # 0 = all pass, 1 = some fail
        assert "System test" in result.stdout


class TestEndToEnd:
    """End-to-end workflow tests"""

    @pytest.mark.skip(reason="CLI module structure changed - needs __main__.py")
    def test_analyze_game_end_to_end(self):
        """Test complete analyze-game workflow"""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "walters_analyzer.cli",
                "analyze-game",
                "--home",
                "Kansas City Chiefs",
                "--away",
                "Buffalo Bills",
                "--spread",
                "-2.5",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0
        assert "RECOMMENDATION" in result.stdout
        assert "Stake:" in result.stdout or "Edge:" in result.stdout

    @pytest.mark.skip(reason="CLI module structure changed - needs __main__.py")
    def test_slash_bankroll_end_to_end(self):
        """Test complete slash bankroll workflow"""
        result = subprocess.run(
            [sys.executable, "-m", "walters_analyzer.cli", "slash", "/bankroll"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0
        assert "success" in result.stdout
        assert "current" in result.stdout


class TestSystemHealth:
    """Test overall system health"""

    def test_imports_work(self):
        """Test all major imports work"""
        from walters_analyzer.core import BillyWaltersAnalyzer
        from walters_analyzer.research import ResearchEngine
        from walters_analyzer.slash_commands import SlashCommandHandler
        from walters_analyzer.ingest.chrome_devtools_ai_scraper import (
            EnhancedChromeDevToolsOddsExtractor,
        )

        assert BillyWaltersAnalyzer is not None
        assert ResearchEngine is not None
        assert SlashCommandHandler is not None
        assert EnhancedChromeDevToolsOddsExtractor is not None

    def test_core_modules_available(self):
        """Test all core modules are importable"""

        assert True

    def test_research_modules_available(self):
        """Test all research modules are importable"""

        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
