"""
ESPN API Client - Backwards compatibility shim

Redirects imports from archived espn_api_client to archive location.
This maintains compatibility with existing scrapers while the old client
is being migrated to the new async-based ESPNClient.
"""

import sys
from pathlib import Path

# Add archive directory to path
archive_path = Path(__file__).parent / "archive" / "espn_clients"
if str(archive_path) not in sys.path:
    sys.path.insert(0, str(archive_path))

# Import from archived client
from espn_api_client import ESPNAPIClient

__all__ = ["ESPNAPIClient"]
