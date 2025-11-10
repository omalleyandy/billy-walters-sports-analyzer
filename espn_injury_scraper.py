#!/usr/bin/env python3
"""
Simple ESPN Injury Scraper
Fetches NFL and NCAA FBS injury reports directly from ESPN API
"""

import json
import os
import requests
from datetime import datetime
from typing import Dict, List, Optional
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class ESPNInjuryScraper:
    """Scraper for ESPN injury data using their internal API"""

    def __init__(self, output_dir: str = "output/injuries"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # ESPN uses internal APIs - these are the actual endpoints
        self.base_url = "https://site.api.espn.com/apis/site/v2/sports"

    def scrape_nfl_injuries(self) -> List[Dict]:
        """
        Scrape NFL injury data from ESPN API

        Returns:
            List of injury dictionaries
        """
        logger.info("Scraping NFL injuries from ESPN...")

        injuries = []

        # ESPN API endpoint for NFL teams
        teams_url = f"{self.base_url}/football/nfl/teams"

        try:
            response = requests.get(teams_url, timeout=10)
            response.raise_for_status()
            teams_data = response.json()

            # Get all NFL teams
            teams = teams_data.get('sports', [{}])[0].get('leagues', [{}])[0].get('teams', [])

            logger.info(f"Found {len(teams)} NFL teams")

            # For each team, get their injury report
            for team_info in teams:
                team = team_info.get('team', {})
                team_id = team.get('id')
                team_name = team.get('displayName', 'Unknown')
                team_abbr = team.get('abbreviation', '')

                # ESPN injury endpoint per team
                injury_url = f"{self.base_url}/football/nfl/teams/{team_id}/injuries"

                try:
                    injury_response = requests.get(injury_url, timeout=10)
                    injury_response.raise_for_status()
                    injury_data = injury_response.json()

                    # Parse injuries
                    team_injuries = injury_data.get('injuries', [])

                    for injury in team_injuries:
                        athlete = injury.get('athlete', {})
                        status = injury.get('status', {})

                        injuries.append({
                            'source': 'espn',
                            'sport': 'nfl',
                            'league': 'NFL',
                            'team': team_name,
                            'team_abbr': team_abbr,
                            'team_id': team_id,
                            'player_name': athlete.get('displayName', ''),
                            'player_id': athlete.get('id'),
                            'position': athlete.get('position', {}).get('abbreviation', ''),
                            'injury_status': status.get('type', ''),
                            'injury_description': status.get('description', ''),
                            'injury_detail': injury.get('details', {}).get('detail', ''),
                            'date_reported': injury.get('date', datetime.now().isoformat()),
                            'collected_at': datetime.now().isoformat()
                        })

                    if team_injuries:
                        logger.info(f"  {team_name}: {len(team_injuries)} injuries")

                except Exception as e:
                    logger.warning(f"Could not fetch injuries for {team_name}: {e}")
                    continue

            logger.info(f"Total NFL injuries collected: {len(injuries)}")
            return injuries

        except Exception as e:
            logger.error(f"Error scraping NFL injuries: {e}")
            return []

    def scrape_ncaaf_injuries(self) -> List[Dict]:
        """
        Scrape NCAA FBS injury data from ESPN API

        Returns:
            List of injury dictionaries
        """
        logger.info("Scraping NCAA FBS injuries from ESPN...")

        injuries = []

        # ESPN API endpoint for college football teams (FBS)
        teams_url = f"{self.base_url}/football/college-football/teams"

        try:
            response = requests.get(teams_url, timeout=10)
            response.raise_for_status()
            teams_data = response.json()

            # Get all FBS teams
            teams = teams_data.get('sports', [{}])[0].get('leagues', [{}])[0].get('teams', [])

            logger.info(f"Found {len(teams)} NCAA FBS teams")

            # For top 50 teams (to avoid API rate limits)
            for team_info in teams[:50]:  # Limit to avoid long scrapes
                team = team_info.get('team', {})
                team_id = team.get('id')
                team_name = team.get('displayName', 'Unknown')
                team_abbr = team.get('abbreviation', '')

                # ESPN injury endpoint per team
                injury_url = f"{self.base_url}/football/college-football/teams/{team_id}/injuries"

                try:
                    injury_response = requests.get(injury_url, timeout=10)
                    injury_response.raise_for_status()
                    injury_data = injury_response.json()

                    # Parse injuries
                    team_injuries = injury_data.get('injuries', [])

                    for injury in team_injuries:
                        athlete = injury.get('athlete', {})
                        status = injury.get('status', {})

                        injuries.append({
                            'source': 'espn',
                            'sport': 'college_football',
                            'league': 'NCAAF',
                            'team': team_name,
                            'team_abbr': team_abbr,
                            'team_id': team_id,
                            'player_name': athlete.get('displayName', ''),
                            'player_id': athlete.get('id'),
                            'position': athlete.get('position', {}).get('abbreviation', ''),
                            'injury_status': status.get('type', ''),
                            'injury_description': status.get('description', ''),
                            'injury_detail': injury.get('details', {}).get('detail', ''),
                            'date_reported': injury.get('date', datetime.now().isoformat()),
                            'collected_at': datetime.now().isoformat()
                        })

                    if team_injuries:
                        logger.info(f"  {team_name}: {len(team_injuries)} injuries")

                except Exception as e:
                    logger.debug(f"No injuries for {team_name}")
                    continue

            logger.info(f"Total NCAA FBS injuries collected: {len(injuries)}")
            return injuries

        except Exception as e:
            logger.error(f"Error scraping NCAA FBS injuries: {e}")
            return []

    def save_injuries(self, injuries: List[Dict], filename: str):
        """Save injuries to JSON file"""
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, 'w') as f:
            json.dump(injuries, f, indent=2)

        logger.info(f"Saved {len(injuries)} injuries to {filepath}")

        # Also save as JSONL
        jsonl_filepath = filepath.replace('.json', '.jsonl')
        with open(jsonl_filepath, 'w') as f:
            for injury in injuries:
                f.write(json.dumps(injury) + '\n')

        logger.info(f"Saved JSONL to {jsonl_filepath}")


def main():
    """Main entry point"""
    scraper = ESPNInjuryScraper()

    # Scrape NFL injuries
    logger.info("=" * 60)
    logger.info("NFL INJURY SCRAPER")
    logger.info("=" * 60)
    nfl_injuries = scraper.scrape_nfl_injuries()

    if nfl_injuries:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        scraper.save_injuries(nfl_injuries, f"nfl_injuries_{timestamp}.json")

    # Scrape NCAA FBS injuries
    logger.info("")
    logger.info("=" * 60)
    logger.info("NCAA FBS INJURY SCRAPER")
    logger.info("=" * 60)
    ncaaf_injuries = scraper.scrape_ncaaf_injuries()

    if ncaaf_injuries:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        scraper.save_injuries(ncaaf_injuries, f"ncaaf_injuries_{timestamp}.json")

    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    logger.info(f"NFL Injuries: {len(nfl_injuries)}")
    logger.info(f"NCAA FBS Injuries: {len(ncaaf_injuries)}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
