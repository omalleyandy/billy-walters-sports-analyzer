import importlib.util
from pathlib import Path
import sys
import pytest


def test_repo_has_pyproject():
    assert Path("pyproject.toml").exists(), "pyproject.toml missing"


def test_python_version_is_modern():
    assert sys.version_info >= (3, 10), "Python >= 3.10 required"


@pytest.mark.parametrize(
    "candidate",
    [
        "cli_interface",  # common in your WSA repo
        "walters_analyzer",  # package root, if present
        "edge_pipeline",  # module, if present
    ],
)
def test_optional_imports(candidate):
    if importlib.util.find_spec(candidate) is None:
        pytest.skip(f"{candidate} not present (skip ok)")
    __import__(candidate)
