"""
JSONL storage utilities for Highlightly data
"""

import orjson
from pathlib import Path
from datetime import datetime
from typing import List, Any, Optional
import logging

logger = logging.getLogger(__name__)


def save_to_jsonl(
    data: List[Any],
    endpoint: str,
    sport: str,
    output_dir: Optional[str] = None,
    extra_suffix: str = "",
) -> Path:
    """
    Save data to JSONL file

    Args:
        data: List of data objects (Pydantic models or dicts)
        endpoint: Endpoint name (teams, matches, odds, etc.)
        sport: Sport (nfl or ncaaf)
        output_dir: Custom output directory (default: data/highlightly/{sport})
        extra_suffix: Extra suffix for filename (e.g., match_id, date)

    Returns:
        Path to saved file
    """
    if not data:
        logger.warning(f"No data to save for {endpoint}")
        return None

    # Determine output directory
    if output_dir is None:
        output_dir = f"data/highlightly/{sport}"

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    suffix = f"-{extra_suffix}" if extra_suffix else ""
    filename = f"{endpoint}{suffix}-{timestamp}.jsonl"
    filepath = output_path / filename

    # Write data
    count = 0
    with open(filepath, "wb") as f:
        for item in data:
            # Convert Pydantic model to dict if needed
            if hasattr(item, "model_dump"):
                item_dict = item.model_dump(by_alias=True, exclude_none=True)
            elif hasattr(item, "dict"):
                item_dict = item.dict(by_alias=True, exclude_none=True)
            else:
                item_dict = item

            # Write as JSONL (one JSON object per line)
            f.write(orjson.dumps(item_dict))
            f.write(b"\n")
            count += 1

    logger.info(f"Saved {count} items to {filepath}")
    print(f"[*] Saved {count} items to {filepath}")

    return filepath


def load_from_jsonl(filepath: Path) -> List[dict]:
    """
    Load data from JSONL file

    Args:
        filepath: Path to JSONL file

    Returns:
        List of dictionaries
    """
    data = []

    with open(filepath, "rb") as f:
        for line in f:
            if line.strip():
                data.append(orjson.loads(line))

    return data


def get_latest_file(
    endpoint: str, sport: str, output_dir: Optional[str] = None
) -> Optional[Path]:
    """
    Get the latest JSONL file for an endpoint

    Args:
        endpoint: Endpoint name
        sport: Sport (nfl or ncaaf)
        output_dir: Custom output directory

    Returns:
        Path to latest file or None
    """
    if output_dir is None:
        output_dir = f"data/highlightly/{sport}"

    output_path = Path(output_dir)

    if not output_path.exists():
        return None

    # Find matching files
    pattern = f"{endpoint}-*.jsonl"
    files = sorted(output_path.glob(pattern), reverse=True)

    return files[0] if files else None
