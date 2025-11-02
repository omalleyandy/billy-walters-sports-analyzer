import pytest

from walters_analyzer.settings import SettingsError, reload_settings


def _clear_env(monkeypatch):
    keys = [
        "OV_CUSTOMER_ID",
        "OV_CUSTOMER_PASSWORD",
        "ACCUWEATHER_API_KEY",
        "OPENWEATHER_API_KEY",
        "NEWS_API_KEY",
        "PROFOOTBALLDOC_API_KEY",
        "HIGHLIGHTLY_API_KEY",
        "BANKROLL",
        "KELLY_FRACTION",
        "MAX_BET_PERCENTAGE",
        "MINIMUM_EDGE_PERCENTAGE",
        "CACHE_TTL_WEATHER",
        "CACHE_TTL_INJURY",
        "CACHE_TTL_ANALYSIS",
        "CACHE_TTL_ODDS",
        "HTTP_MAX_CONNECTIONS",
        "HTTP_MAX_PER_HOST",
        "HTTP_TIMEOUT",
        "ENABLE_WEB_FETCH",
        "ENABLE_CACHING",
        "ENABLE_RESEARCH",
        "ENABLE_PROFOOTBALLDOC",
        "ENABLE_NEWS_API",
        "PROXY_URL",
        "OVERTIME_PROXY",
    ]
    for key in keys:
        monkeypatch.delenv(key, raising=False)


def test_defaults_applied_when_optional_missing(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("OV_CUSTOMER_ID", "user123")
    monkeypatch.setenv("OV_CUSTOMER_PASSWORD", "secret!")
    monkeypatch.setenv("ACCUWEATHER_API_KEY", "accu-123")

    settings = reload_settings()

    assert settings.bankroll == 10000.0
    assert settings.kelly_fraction == 0.25
    assert settings.enable_caching is True
    assert settings.openweather_api_key is None


@pytest.mark.parametrize("missing_key", ["OV_CUSTOMER_ID", "OV_CUSTOMER_PASSWORD", "ACCUWEATHER_API_KEY"])
def test_missing_required_key_raises(monkeypatch, missing_key):
    _clear_env(monkeypatch)
    base_env = {
        "OV_CUSTOMER_ID": "user123",
        "OV_CUSTOMER_PASSWORD": "secret!",
        "ACCUWEATHER_API_KEY": "accu-123",
    }
    for key, value in base_env.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv(missing_key, raising=False)

    with pytest.raises(SettingsError) as exc:
        reload_settings()
    assert missing_key in str(exc.value)


def test_invalid_numeric_value_raises(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("OV_CUSTOMER_ID", "user123")
    monkeypatch.setenv("OV_CUSTOMER_PASSWORD", "secret!")
    monkeypatch.setenv("ACCUWEATHER_API_KEY", "accu-123")
    monkeypatch.setenv("BANKROLL", "not-a-number")

    with pytest.raises(SettingsError):
        reload_settings()

    # Ensure cache is empty so later tests pick up clean values
    for key in ("BANKROLL",):
        monkeypatch.delenv(key, raising=False)
    reload_settings()
