"""
Configuration for autonomous agent data directories and file paths.
Ensures consistent file organization across the project.
"""

from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class AgentConfig:
    """Configuration for autonomous agent data directories"""

    # Project root (auto-detected or provided)
    project_root: Path

    # Input directories
    data_dir: Optional[Path] = None
    current_data_dir: Optional[Path] = None

    # Output directories
    output_dir: Optional[Path] = None

    # Persistence files
    memory_file: Optional[Path] = None
    portfolio_file: Optional[Path] = None

    # Decision logs
    decisions_file: Optional[Path] = None

    def __post_init__(self):
        """Set default paths and ensure directories exist"""
        # Set defaults if not provided
        if self.data_dir is None:
            self.data_dir = self.project_root / "data"

        if self.current_data_dir is None:
            self.current_data_dir = self.project_root / "data" / "current"

        if self.output_dir is None:
            self.output_dir = self.project_root / "output" / "agent_analysis"

        if self.memory_file is None:
            self.memory_file = self.data_dir / "agent_memory.json"

        if self.portfolio_file is None:
            self.portfolio_file = self.data_dir / "agent_portfolio.json"

        if self.decisions_file is None:
            self.decisions_file = self.output_dir / "decisions.jsonl"

        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_project_root(cls, project_root: Optional[Path] = None) -> "AgentConfig":
        """
        Create config by auto-detecting or using provided project root.

        Args:
            project_root: Optional project root path. If None, auto-detect.

        Returns:
            AgentConfig instance
        """
        if project_root is None:
            # Auto-detect from this file's location
            # agent_config.py is in src/walters_analyzer/config/
            project_root = Path(__file__).parent.parent.parent.parent

        return cls(project_root=project_root)
