import pytest

from tradingagents.default_config import DEFAULT_CONFIG


@pytest.mark.unit
def test_default_config_has_deep_think_temperature():
    """DEFAULT_CONFIG must expose deep_think_temperature so providers can pin
    the deep-tier judge LLM to a deterministic temperature."""
    assert "deep_think_temperature" in DEFAULT_CONFIG
    assert DEFAULT_CONFIG["deep_think_temperature"] == 0.0


@pytest.mark.unit
def test_default_config_has_quick_think_temperature():
    """DEFAULT_CONFIG must expose quick_think_temperature so analysts/debaters
    get a low-but-nonzero temperature that reduces variance while preserving
    lexical diversity in research prose."""
    assert "quick_think_temperature" in DEFAULT_CONFIG
    assert DEFAULT_CONFIG["quick_think_temperature"] == 0.3


@pytest.mark.unit
def test_default_max_debate_rounds_is_2():
    """Two debate rounds give each researcher a rebuttal turn, building a more
    stable consensus before the Research Manager judges — reducing run-to-run
    variance at modest latency cost."""
    assert DEFAULT_CONFIG["max_debate_rounds"] == 2


@pytest.mark.unit
def test_default_max_risk_discuss_rounds_is_2():
    """Two risk-discussion rounds let the three risk agents converge rather than
    handing a single-round split to the Portfolio Manager."""
    assert DEFAULT_CONFIG["max_risk_discuss_rounds"] == 2
