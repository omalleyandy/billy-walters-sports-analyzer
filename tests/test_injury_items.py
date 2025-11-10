"""Test injury report item structure and methods."""
import json
from datetime import datetime
from scrapers.overtime_live.items import InjuryReportItem, iso_now


def test_injury_item_creation():
    """Test creating an injury report item."""
    item = InjuryReportItem(
        source="espn",
        sport="college_football",
        league="NCAAF",
        collected_at=iso_now(),
        team="Alabama Crimson Tide",
        team_abbr="ALA",
        player_name="Jalen Milroe",
        position="QB",
        injury_status="Questionable",
        injury_type="Ankle",
        date_reported="2025-10-30",
        game_date="2025-11-02",
        opponent="LSU Tigers",
        notes="Limited in practice",
    )
    
    assert item.player_name == "Jalen Milroe"
    assert item.position == "QB"
    assert item.injury_status == "Questionable"
    assert item.team == "Alabama Crimson Tide"


def test_injury_item_to_dict():
    """Test converting injury item to dictionary."""
    item = InjuryReportItem(
        source="espn",
        sport="college_football",
        league="NCAAF",
        collected_at=iso_now(),
        team="Ohio State Buckeyes",
        team_abbr="OSU",
        player_name="Will Howard",
        position="QB",
        injury_status="Out",
        injury_type="Shoulder",
        date_reported="2025-10-29",
        game_date=None,
        opponent=None,
        notes=None,
    )
    
    data = item.to_dict()
    
    assert isinstance(data, dict)
    assert data["player_name"] == "Will Howard"
    assert data["injury_status"] == "Out"
    assert data["team_abbr"] == "OSU"


def test_injury_impact_score():
    """Test impact score calculation."""
    # Out = 100
    item_out = InjuryReportItem(
        source="espn",
        sport="college_football",
        league="NCAAF",
        collected_at=iso_now(),
        team="Test Team",
        team_abbr="TST",
        player_name="Player 1",
        position="QB",
        injury_status="Out",
        injury_type="Knee",
        date_reported=None,
        game_date=None,
        opponent=None,
        notes=None,
    )
    assert item_out.get_impact_score() == 100
    
    # Doubtful = 75
    item_doubtful = InjuryReportItem(
        source="espn",
        sport="college_football",
        league="NCAAF",
        collected_at=iso_now(),
        team="Test Team",
        team_abbr="TST",
        player_name="Player 2",
        position="RB",
        injury_status="Doubtful",
        injury_type="Hamstring",
        date_reported=None,
        game_date=None,
        opponent=None,
        notes=None,
    )
    assert item_doubtful.get_impact_score() == 75
    
    # Questionable = 50
    item_questionable = InjuryReportItem(
        source="espn",
        sport="college_football",
        league="NCAAF",
        collected_at=iso_now(),
        team="Test Team",
        team_abbr="TST",
        player_name="Player 3",
        position="WR",
        injury_status="Questionable",
        injury_type="Ankle",
        date_reported=None,
        game_date=None,
        opponent=None,
        notes=None,
    )
    assert item_questionable.get_impact_score() == 50
    
    # Probable = 25
    item_probable = InjuryReportItem(
        source="espn",
        sport="college_football",
        league="NCAAF",
        collected_at=iso_now(),
        team="Test Team",
        team_abbr="TST",
        player_name="Player 4",
        position="TE",
        injury_status="Probable",
        injury_type="Toe",
        date_reported=None,
        game_date=None,
        opponent=None,
        notes=None,
    )
    assert item_probable.get_impact_score() == 25


def test_injury_json_serialization():
    """Test that injury items can be serialized to JSON."""
    item = InjuryReportItem(
        source="espn",
        sport="college_football",
        league="NCAAF",
        collected_at=iso_now(),
        team="Georgia Bulldogs",
        team_abbr="UGA",
        player_name="Carson Beck",
        position="QB",
        injury_status="Probable",
        injury_type="Elbow",
        date_reported="2025-10-30",
        game_date="2025-11-02",
        opponent="Florida Gators",
        notes="Full participant in practice",
    )
    
    # Convert to dict and then to JSON
    json_str = json.dumps(item.to_dict())
    
    # Parse back
    parsed = json.loads(json_str)
    
    assert parsed["player_name"] == "Carson Beck"
    assert parsed["position"] == "QB"
    assert parsed["injury_status"] == "Probable"


if __name__ == "__main__":
    print("Running injury item tests...")
    test_injury_item_creation()
    print("[PASS] Item creation test passed")
    
    test_injury_item_to_dict()
    print("[PASS] to_dict() test passed")
    
    test_injury_impact_score()
    print("[PASS] Impact score test passed")
    
    test_injury_json_serialization()
    print("[PASS] JSON serialization test passed")
    
    print("\n[SUCCESS] All injury item tests passed!")

