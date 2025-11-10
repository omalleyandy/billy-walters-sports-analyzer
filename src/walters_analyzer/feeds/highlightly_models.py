"""
Pydantic models for Highlightly NFL/NCAA API
Based on OpenAPI schema: https://highlightly.net/documentation/american-football/
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


# ============================================================================
# Enums
# ============================================================================


class MatchState(str, Enum):
    """Match state enum"""

    SUSPENDED = "Suspended"
    POSTPONED = "Postponed"
    CANCELLED = "Cancelled"
    ABANDONED = "Abandoned"
    FINISHED = "Finished"
    IN_PROGRESS = "In progress"
    END_PERIOD = "End period"
    HALF_TIME = "Half time"
    UNKNOWN = "Unknown"
    SCHEDULED = "Scheduled"


class OddsType(str, Enum):
    """Odds type enum"""

    PREMATCH = "prematch"
    LIVE = "live"


class SeasonBreakdown(str, Enum):
    """Season breakdown enum"""

    ENTIRE = "Entire"
    SEASON = "Season"


class StatCategory(str, Enum):
    """Stat category enum"""

    GENERAL = "General"
    DEFENSE = "Defense"
    RETURNING = "Returning"
    PASSING = "Passing"
    RUSHING = "Rushing"
    RECEIVING = "Receiving"
    SCORING = "Scoring"
    PUNTING = "Punting"
    KICKING = "Kicking"


# ============================================================================
# Team Models
# ============================================================================


class HighlightlyTeam(BaseModel):
    """Team information"""

    id: int
    logo: Optional[str] = None
    name: str
    displayName: str = Field(..., alias="displayName")
    abbreviation: str
    league: str

    class Config:
        populate_by_name = True


# ============================================================================
# Team Statistics Models
# ============================================================================


class TeamGameStats(BaseModel):
    """Team game statistics"""

    played: int
    wins: int
    loses: int


class TeamPointStats(BaseModel):
    """Team point statistics"""

    scored: int
    received: int


class TeamTotalStats(BaseModel):
    """Team total statistics"""

    games: TeamGameStats
    points: TeamPointStats


class TeamStatistics(BaseModel):
    """Team statistics by season and round"""

    total: TeamTotalStats
    home: TeamTotalStats
    away: TeamTotalStats
    leagueName: str = Field(..., alias="leagueName")
    round: str

    class Config:
        populate_by_name = True


# ============================================================================
# Match Models
# ============================================================================


class MatchScore(BaseModel):
    """Match score information"""

    current: Optional[str] = None
    firstPeriod: Optional[str] = Field(None, alias="firstPeriod")
    secondPeriod: Optional[str] = Field(None, alias="secondPeriod")
    thirdPeriod: Optional[str] = Field(None, alias="thirdPeriod")
    fourthPeriod: Optional[str] = Field(None, alias="fourthPeriod")
    firstOvertimePeriod: Optional[str] = Field(None, alias="firstOvertimePeriod")
    secondOvertimePeriod: Optional[str] = Field(None, alias="secondOvertimePeriod")

    class Config:
        populate_by_name = True


class MatchStateInfo(BaseModel):
    """Match state information"""

    period: Optional[int] = None
    clock: Optional[int] = None
    description: MatchState
    score: MatchScore
    report: Optional[str] = None


class MatchTeam(BaseModel):
    """Match team (simplified)"""

    id: int
    logo: Optional[str] = None
    name: str
    displayName: str = Field(..., alias="displayName")
    abbreviation: str

    class Config:
        populate_by_name = True


class HighlightlyMatch(BaseModel):
    """Match information"""

    id: int
    round: str
    date: str
    league: str
    season: int
    awayTeam: MatchTeam = Field(..., alias="awayTeam")
    homeTeam: MatchTeam = Field(..., alias="homeTeam")
    state: MatchStateInfo

    class Config:
        populate_by_name = True


# ============================================================================
# Detailed Match Models
# ============================================================================


class Venue(BaseModel):
    """Venue information"""

    city: str
    name: str
    state: str


class Forecast(BaseModel):
    """Weather forecast"""

    status: Optional[str] = None
    temperature: Optional[str] = None


class StatisticsItem(BaseModel):
    """Statistics item"""

    name: str
    value: float


class TeamMatchStatistics(BaseModel):
    """Team match statistics"""

    statistics: List[StatisticsItem]


class MatchStatistics(BaseModel):
    """Match statistics for both teams"""

    homeTeam: TeamMatchStatistics = Field(..., alias="homeTeam")
    awayTeam: TeamMatchStatistics = Field(..., alias="awayTeam")

    class Config:
        populate_by_name = True


class PlayerStatisticsItem(BaseModel):
    """Player statistics item"""

    name: str
    value: str


class BoxScorePlayer(BaseModel):
    """Box score player"""

    playerName: str = Field(..., alias="playerName")
    statistics: List[PlayerStatisticsItem]

    class Config:
        populate_by_name = True


class BoxScores(BaseModel):
    """Box scores for both teams"""

    homeTeam: List[BoxScorePlayer] = Field(..., alias="homeTeam")
    awayTeam: List[BoxScorePlayer] = Field(..., alias="awayTeam")

    class Config:
        populate_by_name = True


class TopPerformer(BaseModel):
    """Top performer"""

    name: str
    playerName: str = Field(..., alias="playerName")
    playerPosition: str = Field(..., alias="playerPosition")
    value: str

    class Config:
        populate_by_name = True


class TopPerformers(BaseModel):
    """Top performers for both teams"""

    homeTeam: List[TopPerformer] = Field(..., alias="homeTeam")
    awayTeam: List[TopPerformer] = Field(..., alias="awayTeam")

    class Config:
        populate_by_name = True


class InjuryPlayer(BaseModel):
    """Injury player info"""

    name: str
    jersey: Optional[int] = None
    position: Optional[str] = None


class InjuryItem(BaseModel):
    """Injury item"""

    status: str
    player: InjuryPlayer


class TeamInjuries(BaseModel):
    """Team injuries"""

    team: HighlightlyTeam
    data: List[InjuryItem]


class EventPosition(BaseModel):
    """Event position"""

    clock: str
    period: str
    yardLine: int = Field(..., alias="yardLine")

    class Config:
        populate_by_name = True


class MatchEvent(BaseModel):
    """Match event"""

    end: EventPosition
    team: HighlightlyTeam
    plays: List[str]
    start: EventPosition
    result: str
    description: str
    isScoringPlay: bool = Field(..., alias="isScoringPlay")

    class Config:
        populate_by_name = True


class Prediction(BaseModel):
    """Prediction"""

    type: str
    modelType: str = Field(..., alias="modelType")
    generatedAt: str = Field(..., alias="generatedAt")
    description: str

    class Config:
        populate_by_name = True


class PredictionData(BaseModel):
    """Prediction data"""

    home: List[Prediction]
    away: List[Prediction]


class MatchDetails(BaseModel):
    """Detailed match information"""

    id: int
    round: str
    date: str
    league: str
    season: int
    awayTeam: MatchTeam = Field(..., alias="awayTeam")
    homeTeam: MatchTeam = Field(..., alias="homeTeam")
    state: MatchStateInfo
    venue: Optional[Venue] = None
    forecast: Optional[Forecast] = None
    matchStatistics: Optional[MatchStatistics] = Field(None, alias="matchStatistics")
    boxScores: Optional[List[BoxScores]] = Field(None, alias="boxScores")
    topPerformers: Optional[TopPerformers] = Field(None, alias="topPerformers")
    injuries: Optional[List[TeamInjuries]] = None
    events: Optional[List[MatchEvent]] = None
    predictions: Optional[PredictionData] = None

    class Config:
        populate_by_name = True


# ============================================================================
# Odds Models
# ============================================================================


class MarketSelection(BaseModel):
    """Market selection (outcome)"""

    odd: float
    value: str


class BookmakerMarket(BaseModel):
    """Bookmaker market"""

    bookmakerId: int = Field(..., alias="bookmakerId")
    bookmakerName: Optional[str] = Field(None, alias="bookmakerName")
    type: str
    market: str
    values: List[MarketSelection]

    class Config:
        populate_by_name = True


class MatchOdds(BaseModel):
    """Match odds"""

    matchId: int = Field(..., alias="matchId")
    odds: List[BookmakerMarket]

    class Config:
        populate_by_name = True


class Bookmaker(BaseModel):
    """Bookmaker information"""

    id: int
    name: str


# ============================================================================
# Highlights Models
# ============================================================================


class HighlightlyHighlight(BaseModel):
    """Highlight information"""

    id: int
    type: str
    imgUrl: Optional[str] = Field(None, alias="imgUrl")
    title: str
    description: Optional[str] = None
    url: str
    embedUrl: Optional[str] = Field(None, alias="embedUrl")
    match: HighlightlyMatch
    channel: Optional[str] = None
    source: Optional[str] = None

    class Config:
        populate_by_name = True


class GeoRestriction(BaseModel):
    """Geo restriction information"""

    state: str
    allowedCountries: List[str] = Field(..., alias="allowedCountries")
    blockedCountries: List[str] = Field(..., alias="blockedCountries")
    embeddable: bool

    class Config:
        populate_by_name = True


# ============================================================================
# Standings Models
# ============================================================================


class StandingsStatValue(BaseModel):
    """Standings stat value"""

    value: str
    displayName: str = Field(..., alias="displayName")

    class Config:
        populate_by_name = True


class StandingsTeam(BaseModel):
    """Standings team"""

    id: int
    logo: str
    name: str
    displayName: str = Field(..., alias="displayName")
    abbreviation: str

    class Config:
        populate_by_name = True


class TeamStanding(BaseModel):
    """Team standing"""

    team: StandingsTeam
    statistics: List[StandingsStatValue]


class StandingsData(BaseModel):
    """Standings data"""

    leagueName: str = Field(..., alias="leagueName")
    abbreviation: str
    year: int
    leagueType: str = Field(..., alias="leagueType")
    seasonType: str = Field(..., alias="seasonType")
    startDate: str = Field(..., alias="startDate")
    endDate: str = Field(..., alias="endDate")
    data: List[TeamStanding]

    class Config:
        populate_by_name = True


# ============================================================================
# Lineup Models
# ============================================================================


class LineupPlayer(BaseModel):
    """Lineup player"""

    id: int
    jersey: Optional[int] = None
    player: str
    position: str
    positionAbbreviation: str = Field(..., alias="positionAbbreviation")
    isStarter: Optional[bool] = Field(None, alias="isStarter")

    class Config:
        populate_by_name = True


class TeamLineup(BaseModel):
    """Team lineup"""

    team: HighlightlyTeam
    lineup: List[LineupPlayer]


class Lineups(BaseModel):
    """Match lineups"""

    home: TeamLineup
    away: TeamLineup


# ============================================================================
# Player Models
# ============================================================================


class HighlightlyPlayer(BaseModel):
    """Player information"""

    id: int
    fullName: Optional[str] = Field(None, alias="fullName")
    logo: Optional[str] = None

    class Config:
        populate_by_name = True


class PlayerPosition(BaseModel):
    """Player position"""

    main: Optional[str] = None
    abbreviation: Optional[str] = None


class PlayerDraft(BaseModel):
    """Player draft info"""

    round: Optional[int] = None
    year: Optional[int] = None
    pick: Optional[int] = None


class PlayerTeam(BaseModel):
    """Player team"""

    id: int
    logo: Optional[str] = None
    name: str
    league: str
    displayName: str = Field(..., alias="displayName")
    abbreviation: str

    class Config:
        populate_by_name = True


class PlayerProfile(BaseModel):
    """Player profile"""

    fullName: Optional[str] = Field(None, alias="fullName")
    birthPlace: Optional[str] = Field(None, alias="birthPlace")
    birthDate: Optional[str] = Field(None, alias="birthDate")
    height: Optional[str] = None
    jersey: Optional[str] = None
    weight: Optional[str] = None
    isActive: Optional[bool] = Field(None, alias="isActive")
    position: PlayerPosition
    draft: PlayerDraft
    team: PlayerTeam

    class Config:
        populate_by_name = True


class PlayerSummary(BaseModel):
    """Player summary"""

    id: int
    fullName: Optional[str] = Field(None, alias="fullName")
    logo: Optional[str] = None
    profile: PlayerProfile

    class Config:
        populate_by_name = True


class StatEntry(BaseModel):
    """Stat entry"""

    name: str
    value: float
    category: StatCategory


class PlayerSeasonStats(BaseModel):
    """Player season statistics"""

    stats: List[StatEntry]
    teams: List[PlayerTeam]
    league: str
    season: int
    seasonBreakdown: SeasonBreakdown = Field(..., alias="seasonBreakdown")

    class Config:
        populate_by_name = True


class PlayerStatistics(BaseModel):
    """Player statistics"""

    id: int
    fullName: Optional[str] = Field(None, alias="fullName")
    logo: Optional[str] = None
    perSeason: List[PlayerSeasonStats] = Field(..., alias="perSeason")

    class Config:
        populate_by_name = True


# ============================================================================
# Pagination Models
# ============================================================================


class Pagination(BaseModel):
    """Pagination information"""

    totalCount: int = Field(..., alias="totalCount")
    offset: int
    limit: int

    class Config:
        populate_by_name = True


class PlanInfo(BaseModel):
    """API plan information"""

    tier: str
    message: str


# ============================================================================
# Response Models
# ============================================================================


class TeamsResponse(BaseModel):
    """Teams response"""

    data: List[HighlightlyTeam]
    pagination: Pagination
    plan: PlanInfo


class MatchesResponse(BaseModel):
    """Matches response"""

    data: List[HighlightlyMatch]
    pagination: Pagination
    plan: PlanInfo


class HighlightsResponse(BaseModel):
    """Highlights response"""

    data: List[HighlightlyHighlight]
    pagination: Pagination
    plan: PlanInfo


class OddsResponse(BaseModel):
    """Odds response"""

    data: List[MatchOdds]
    pagination: Pagination
    plan: PlanInfo


class BookmakersResponse(BaseModel):
    """Bookmakers response"""

    data: List[Bookmaker]
    pagination: Pagination
    plan: PlanInfo


class PlayersResponse(BaseModel):
    """Players response"""

    data: List[HighlightlyPlayer]
    pagination: Pagination
    plan: PlanInfo
