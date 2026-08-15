"""Offline tests for market parsing (no network — feeds a sample API payload)."""
from polybot.markets import _parse

# Shape mirrors a real Polymarket Gamma API market object.
SAMPLE = {
    "question": "Will it rain tomorrow?",
    "slug": "will-it-rain-tomorrow",
    "clobTokenIds": '["111111", "222222"]',  # API returns these as a JSON string
    "outcomes": '["Yes", "No"]',
    "volumeNum": 12345.67,
    "active": True,
    "closed": False,
}


def test_parse_extracts_token_ids():
    m = _parse(SAMPLE)
    assert m is not None
    assert m.yes_token_id == "111111"
    assert m.no_token_id == "222222"
    assert m.outcomes == ["Yes", "No"]
    assert m.volume == 12345.67
    assert m.active and not m.closed


def test_parse_rejects_non_binary_market():
    bad = dict(SAMPLE, clobTokenIds='["only-one"]')
    assert _parse(bad) is None


def test_config_block_is_pasteable():
    m = _parse(SAMPLE)
    block = m.config_block()
    assert 'name: "will-it-rain-tomorrow"' in block
    assert 'yes_token_id: "111111"' in block
    assert 'no_token_id: "222222"' in block
    assert "moving_average" in block
