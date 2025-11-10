import pytest

from scrapers.overtime_live.spiders.overtime_live_spider import (
    OvertimeLiveSpider,
    to_float,
)


@pytest.fixture
def spider():
    """Return an instance of the spider for testing helper functions."""
    return OvertimeLiveSpider()


def test_parse_game_block_and_state(spider):
    text = (
        "Team A\n"
        "Team B\n"
        "+6½ -115   -6½ +105\n"
        "O 49½ -110   U 49½ -110\n"
        "+215 -255\n"
        "3rd Q 05:32"
    )
    parsed = spider._parse_game_block(text)
    assert parsed is not None, "Expected parse to succeed"
    assert parsed["away"] == "Team A"
    assert parsed["home"] == "Team B"
    # verify spreads are floats and ints
    spread = parsed["markets"]["spread"]
    assert spread.away.line == to_float("+6.5")
    assert isinstance(spread.away.price, int)
    # verify state parsing
    state = spider._parse_state(text)
    assert state == {"quarter": 3, "clock": "05:32"}


def test_normalize_markets(spider):
    markets = {
        "spread": {
            "away": {"line": "-3.5", "price": "-110"},
            "home": {"line": 3.5, "price": 105},
        },
        "total": {
            "over": {"line": "48.5", "price": "-110"},
            "under": {"line": "48.5", "price": "-110"},
        },
        "moneyline": {
            "away": {"line": None, "price": "+200"},
            "home": {"line": None, "price": "+180"},
        },
    }
    norm = spider._normalize_markets(markets)
    assert norm["spread"]["away"]["line"] == to_float("-3.5")
    assert isinstance(norm["spread"]["away"]["price"], int)
    assert norm["moneyline"]["away"]["price"] == 200
