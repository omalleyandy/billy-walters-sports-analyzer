from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any, Callable, Iterable
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup, Tag


def _clean_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.split())


def _table_to_records(table: Tag) -> list[dict[str, str]]:
    headers: list[str] = []
    thead = table.find("thead")
    if thead:
        for idx, cell in enumerate(thead.find_all(["th", "td"])):
            text = _clean_text(cell.get_text(" ", strip=True))
            headers.append(text or f"column_{idx + 1}")
    else:
        first_row = table.find("tr")
        if first_row:
            for idx, cell in enumerate(first_row.find_all(["th", "td"])):
                text = _clean_text(cell.get_text(" ", strip=True))
                headers.append(text or f"column_{idx + 1}")

    records: list[dict[str, str]] = []
    for row in table.find_all("tr"):
        if row.find_parent("thead"):
            continue
        cells = row.find_all(["td", "th"])
        if not cells:
            continue
        values = [_clean_text(cell.get_text(" ", strip=True)) for cell in cells]
        if not any(values):
            continue
        record: dict[str, str] = {}
        for idx, value in enumerate(values):
            key = headers[idx] if idx < len(headers) else f"column_{idx + 1}"
            record[key] = value
        records.append(record)
    return records


def _find_section_by_heading(soup: BeautifulSoup, heading_text: str) -> Tag | None:
    needle = heading_text.lower()
    for heading in soup.find_all(["h1", "h2", "h3", "h4"]):
        text = heading.get_text(strip=True)
        if text and needle in text.lower():
            return heading.find_parent("section") or heading.find_parent("div")
    return None


def _extract_cards(container: Tag) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    seen: set[str] = set()
    for link in container.find_all("a"):
        title = _clean_text(link.get("title") or link.get_text(strip=True))
        href = link.get("href")
        if not title or not href or "/news" not in href:
            continue
        if href in seen:
            continue
        seen.add(href)
        summary_tag = link.find_next(["p", "span"])
        cards.append(
            {
                "title": title,
                "url": urljoin("https://www.nfl.com", href),
                "summary": _clean_text(summary_tag.get_text(strip=True))
                if summary_tag
                else "",
            }
        )
    return cards


def _decode_flight_payload(raw_script: str) -> list[dict[str, Any]]:
    decoded = raw_script.encode("utf-8").decode("unicode_escape")
    decoder = json.JSONDecoder()
    idx = 0
    payloads: list[dict[str, Any]] = []
    marker = '{"state":{"data":'
    while True:
        start = decoded.find(marker, idx)
        if start == -1:
            break
        obj, length = decoder.raw_decode(decoded[start:])
        payloads.append(obj)
        idx = start + length
    return payloads


@dataclass
class ScrapeJob:
    section: str
    filename: str
    payload: dict[str, Any]


class NFLComScraper:
    BASE_URL = "https://www.nfl.com"
    HEADERS = {
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/130.0.0.0 Safari/537.36"
        ),
        "accept-language": "en-US,en;q=0.9",
    }

    PLAYER_STAT_PAGES = {
        "Passing": "/stats/player-stats/category/passing/2025/reg/all/passingyards/desc",
        "Rushing": "/stats/player-stats/category/rushing/2025/reg/all/rushingyards/desc",
        "Receiving": "/stats/player-stats/category/receiving/2025/reg/all/receivingreceptions/desc",
        "Fumbles": "/stats/player-stats/category/fumbles/2025/reg/all/defensiveforcedfumble/desc",
        "Tackles": "/stats/player-stats/category/tackles/2025/reg/all/defensivecombinetackles/desc",
        "Interceptions": "/stats/player-stats/category/interceptions/2025/reg/all/defensiveinterceptions/desc",
        "Field Goals": "/stats/player-stats/category/field-goals/2025/reg/all/kickingfgmade/desc",
        "Kickoffs": "/stats/player-stats/category/kickoffs/2025/reg/all/kickofftotal/desc",
        "Kickoff Returns": "/stats/player-stats/category/kickoff-returns/2025/reg/all/kickreturnsaverageyards/desc",
        "Punting": "/stats/player-stats/category/punts/2025/reg/all/puntingaverageyards/desc",
        "Punt Returns": "/stats/player-stats/category/punt-returns/2025/reg/all/puntreturnsaverageyards/desc",
    }

    TEAM_STAT_PAGES = {
        "Offense": {
            "Passing": "/stats/team-stats/offense/passing/2025/reg/all",
            "Rushing": "/stats/team-stats/offense/rushing/2025/reg/all",
            "Receiving": "/stats/team-stats/offense/receiving/2025/reg/all",
            "Scoring": "/stats/team-stats/offense/scoring/2025/reg/all",
            "Downs": "/stats/team-stats/offense/downs/2025/reg/all",
        },
        "Defense": {
            "Passing": "/stats/team-stats/defense/passing/2025/reg/all",
            "Rushing": "/stats/team-stats/defense/rushing/2025/reg/all",
            "Receiving": "/stats/team-stats/defense/receiving/2025/reg/all",
            "Scoring": "/stats/team-stats/defense/scoring/2025/reg/all",
            "Tackles": "/stats/team-stats/defense/tackles/2025/reg/all",
            "Downs": "/stats/team-stats/defense/downs/2025/reg/all",
            "Fumbles": "/stats/team-stats/defense/fumbles/2025/reg/all",
            "Interceptions": "/stats/team-stats/defense/interceptions/2025/reg/all",
        },
        "Special Teams": {
            "Field Goals": "/stats/team-stats/special-teams/field-goals/2025/reg/all",
            "Scoring": "/stats/team-stats/special-teams/scoring/2025/reg/all",
            "Kickoffs": "/stats/team-stats/special-teams/kickoffs/2025/reg/all",
            "Kickoff Returns": "/stats/team-stats/special-teams/kickoff-returns/2025/reg/all",
            "Punting": "/stats/team-stats/special-teams/punting/2025/reg/all",
            "Punt Returns": "/stats/team-stats/special-teams/punt-returns/2025/reg/all",
        },
    }

    def __init__(
        self,
        output_root: str | Path = Path("src/output/nfl"),
        *,
        season: int | None = None,
        week: int | None = None,
        season_type: str = "REG",
    ) -> None:
        self.output_root = Path(output_root)
        self.output_root.mkdir(parents=True, exist_ok=True)
        today = datetime.now(timezone.utc)
        self.season = season or today.year
        self.week = week or max(1, today.isocalendar().week % 18)
        self.season_type = season_type.upper()
        self.scraped_at = datetime.now(timezone.utc).isoformat()

    def scrape(self) -> dict[str, Path]:
        jobs: list[Callable[[], Iterable[ScrapeJob]]] = [
            self._scrape_home,
            self._scrape_news,
            self._scrape_schedule,
            self._scrape_injuries,
            self._scrape_transactions,
            self._scrape_players,
            self._scrape_teams,
            self._scrape_player_stats,
            self._scrape_team_stats,
            self._scrape_standings,
        ]
        saved: dict[str, Path] = {}
        with httpx.Client(
            headers=self.HEADERS, timeout=30.0, follow_redirects=True
        ) as client:
            self.client = client
            for job in jobs:
                for section_job in job():
                    path = self._write_payload(section_job)
                    saved[f"{section_job.section}/{section_job.filename}"] = path
        return saved

    def _write_payload(self, job: ScrapeJob) -> Path:
        folder = self.output_root / job.section
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / job.filename
        enriched = {
            "scraped_at": self.scraped_at,
            **job.payload,
        }
        path.write_text(json.dumps(enriched, indent=2), encoding="utf-8")
        return path

    def _get_soup(self, url: str) -> BeautifulSoup:
        response = self.client.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    def _scrape_home(self) -> list[ScrapeJob]:
        soup = self._get_soup(f"{self.BASE_URL}/")
        jobs: list[ScrapeJob] = []
        stack = _find_section_by_heading(soup, "Headline Stack")
        stack_cards = _extract_cards(stack) if stack else []
        features = _find_section_by_heading(soup, "WHAT'S POPULAR")
        feature_cards = _extract_cards(features) if features else []
        jobs.append(
            ScrapeJob(
                section="home",
                filename="home.json",
                payload={
                    "source": f"{self.BASE_URL}/",
                    "headline_stack": stack_cards,
                    "whats_popular": feature_cards,
                },
            )
        )
        return jobs

    def _scrape_news(self) -> list[ScrapeJob]:
        url = f"{self.BASE_URL}/news/"
        soup = self._get_soup(url)
        section = _find_section_by_heading(soup, "Latest News")
        cards = _extract_cards(section) if section else []
        return [
            ScrapeJob(
                section="news",
                filename="latest_news.json",
                payload={
                    "source": url,
                    "items": cards,
                },
            )
        ]

    def _scrape_schedule(self) -> list[ScrapeJob]:
        url = f"{self.BASE_URL}/schedules/"
        soup = self._get_soup(url)
        script_tag = next(
            (
                tag
                for tag in soup.find_all("script")
                if tag.string and "homeTeam" in tag.string
            ),
            None,
        )
        games: list[dict[str, Any]] = []
        if script_tag and script_tag.string:
            payloads = _decode_flight_payload(script_tag.string)
            for payload in payloads:
                data = payload.get("state", {}).get("data")
                if isinstance(data, list) and data and "homeTeam" in data[0]:
                    games = data
                    break
        filtered = [
            game
            for game in games
            if game.get("seasonType") == self.season_type
            and game.get("week") == self.week
        ]
        target_games = filtered or [
            game for game in games if game.get("seasonType") == self.season_type
        ]
        if not target_games:
            target_games = games
        normalized: list[dict[str, Any]] = []
        for game in target_games:
            normalized.append(
                {
                    "game_id": game.get("id"),
                    "date": game.get("date"),
                    "kickoff": game.get("time"),
                    "week": game.get("week"),
                    "season": game.get("season"),
                    "venue": game.get("venue", {}),
                    "broadcast": game.get("broadcastInfo", {}),
                    "home_team": game.get("homeTeam", {}),
                    "away_team": game.get("awayTeam", {}),
                    "status": game.get("status", {}),
                }
            )
        target_week = (
            self.week
            if filtered
            else (target_games[0].get("week") if target_games else self.week)
        )
        return [
            ScrapeJob(
                section="schedule",
                filename=f"week_{target_week:02d}.json",
                payload={
                    "source": url,
                    "season": self.season,
                    "season_type": self.season_type,
                    "requested_week": self.week,
                    "week": target_week,
                    "games": normalized,
                },
            )
        ]

    def _scrape_injuries(self) -> list[ScrapeJob]:
        url = f"{self.BASE_URL}/injuries/"
        soup = self._get_soup(url)
        tables = soup.find_all("table")
        heading = soup.find("h1")
        heading_text = _clean_text(heading.get_text(strip=True)) if heading else ""
        week_label = self.week
        if heading_text:
            match = re.search(r"week\s+(\d+)", heading_text, re.IGNORECASE)
            if match:
                week_label = int(match.group(1))
        payload_tables = [
            {
                "index": idx,
                "rows": _table_to_records(table),
            }
            for idx, table in enumerate(tables)
        ]
        return [
            ScrapeJob(
                section="injuries",
                filename=f"week_{week_label:02d}.json",
                payload={
                    "source": url,
                    "heading": heading_text,
                    "requested_week": self.week,
                    "week": week_label,
                    "tables": payload_tables,
                },
            )
        ]

    def _scrape_transactions(self) -> list[ScrapeJob]:
        url = f"{self.BASE_URL}/transactions/"
        soup = self._get_soup(url)
        heading = soup.find("h1")
        table = soup.find("table")
        rows = _table_to_records(table) if table else []
        return [
            ScrapeJob(
                section="transactions",
                filename="transactions.json",
                payload={
                    "source": url,
                    "heading": _clean_text(heading.get_text(strip=True))
                    if heading
                    else "",
                    "rows": rows,
                },
            )
        ]

    def _scrape_players(self) -> list[ScrapeJob]:
        url = f"{self.BASE_URL}/players/"
        soup = self._get_soup(url)
        popular_section = soup.find(
            "div", class_="nfl-c-player-directory__popular-players"
        )
        players: list[dict[str, str]] = []
        if popular_section:
            for link in popular_section.find_all("a"):
                name = _clean_text(link.get_text(strip=True))
                if not name:
                    continue
                players.append(
                    {"name": name, "url": urljoin(self.BASE_URL, link.get("href", ""))}
                )
        return [
            ScrapeJob(
                section="players",
                filename="popular_players.json",
                payload={"source": url, "players": players},
            )
        ]

    def _scrape_teams(self) -> list[ScrapeJob]:
        url = f"{self.BASE_URL}/teams/"
        soup = self._get_soup(url)
        promos = soup.select("div.nfl-c-custom-promo")
        teams = []
        for promo in promos:
            link = promo.find("a")
            title_tag = promo.find(["h3", "h4"])
            teams.append(
                {
                    "name": _clean_text(title_tag.get_text(strip=True))
                    if title_tag
                    else "",
                    "url": urljoin(self.BASE_URL, link.get("href", "")) if link else "",
                }
            )
        return [
            ScrapeJob(
                section="teams",
                filename="teams.json",
                payload={"source": url, "teams": [t for t in teams if t["name"]]},
            )
        ]

    def _scrape_player_stats(self) -> list[ScrapeJob]:
        stats = {}
        for label, path in self.PLAYER_STAT_PAGES.items():
            url = urljoin(self.BASE_URL, path)
            soup = self._get_soup(url)
            table = soup.find("table")
            stats[label] = {
                "source": url,
                "rows": _table_to_records(table) if table else [],
            }
        return [
            ScrapeJob(
                section="player_stats",
                filename="player_stats.json",
                payload={"categories": stats},
            )
        ]

    def _scrape_team_stats(self) -> list[ScrapeJob]:
        stats: dict[str, Any] = {}
        for group, pages in self.TEAM_STAT_PAGES.items():
            group_payload = {}
            for label, path in pages.items():
                url = urljoin(self.BASE_URL, path)
                soup = self._get_soup(url)
                table = soup.find("table")
                group_payload[label] = {
                    "source": url,
                    "rows": _table_to_records(table) if table else [],
                }
            stats[group] = group_payload
        return [
            ScrapeJob(
                section="team_stats",
                filename="team_stats.json",
                payload={"groups": stats},
            )
        ]

    def _scrape_standings(self) -> list[ScrapeJob]:
        url = f"{self.BASE_URL}/standings/"
        soup = self._get_soup(url)
        standings_tables = []
        for table in soup.find_all("table"):
            header = table.find("th")
            standings_tables.append(
                {
                    "division": _clean_text(header.get_text(strip=True))
                    if header
                    else "",
                    "rows": _table_to_records(table),
                }
            )
        return [
            ScrapeJob(
                section="standings",
                filename="standings.json",
                payload={"source": url, "tables": standings_tables},
            )
        ]


__all__ = ["NFLComScraper"]
