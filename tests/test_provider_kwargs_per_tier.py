import pytest

from tradingagents.graph.trading_graph import _provider_kwargs


@pytest.mark.unit
def test_google_quick_tier_overrides_thinking_level():
    cfg = {
        "llm_provider": "google",
        "google_thinking_level": "high",
        "quick_think_thinking_level": "minimal",
    }
    assert _provider_kwargs(cfg, "deep") == {"thinking_level": "high"}
    assert _provider_kwargs(cfg, "quick") == {"thinking_level": "minimal"}


@pytest.mark.unit
def test_google_quick_tier_falls_back_to_global_when_no_override():
    cfg = {"llm_provider": "google", "google_thinking_level": "high"}
    assert _provider_kwargs(cfg, "deep") == {"thinking_level": "high"}
    assert _provider_kwargs(cfg, "quick") == {"thinking_level": "high"}


@pytest.mark.unit
def test_openai_quick_tier_overrides_reasoning_effort():
    cfg = {
        "llm_provider": "openai",
        "openai_reasoning_effort": "high",
        "quick_think_reasoning_effort": "low",
    }
    assert _provider_kwargs(cfg, "deep") == {"reasoning_effort": "high"}
    assert _provider_kwargs(cfg, "quick") == {"reasoning_effort": "low"}


@pytest.mark.unit
def test_no_thinking_config_yields_empty_kwargs():
    cfg = {"llm_provider": "google"}
    assert _provider_kwargs(cfg, "deep") == {}
    assert _provider_kwargs(cfg, "quick") == {}


@pytest.mark.unit
def test_google_max_output_tokens_per_tier():
    cfg = {
        "llm_provider": "google",
        "quick_think_max_tokens": 8192,
        "deep_think_max_tokens": 32768,
    }
    assert _provider_kwargs(cfg, "quick") == {"max_output_tokens": 8192}
    assert _provider_kwargs(cfg, "deep") == {"max_output_tokens": 32768}


@pytest.mark.unit
def test_openai_uses_max_tokens_name():
    cfg = {"llm_provider": "openai", "quick_think_max_tokens": 4096}
    assert _provider_kwargs(cfg, "quick") == {"max_tokens": 4096}


@pytest.mark.unit
def test_max_tokens_combines_with_thinking():
    cfg = {
        "llm_provider": "google",
        "google_thinking_level": "high",
        "quick_think_thinking_level": "minimal",
        "quick_think_max_tokens": 8192,
    }
    assert _provider_kwargs(cfg, "quick") == {
        "thinking_level": "minimal",
        "max_output_tokens": 8192,
    }


@pytest.mark.unit
def test_deep_think_temperature_included_in_deep_kwargs():
    """deep_think_temperature must appear as 'temperature' in the deep-tier kwargs."""
    cfg = {"llm_provider": "openai", "deep_think_temperature": 0.0}
    kwargs = _provider_kwargs(cfg, "deep")
    assert "temperature" in kwargs
    assert kwargs["temperature"] == 0.0


@pytest.mark.unit
def test_quick_think_temperature_included_in_quick_kwargs():
    """quick_think_temperature must appear as 'temperature' in the quick-tier kwargs."""
    cfg = {"llm_provider": "openai", "quick_think_temperature": 0.3}
    kwargs = _provider_kwargs(cfg, "quick")
    assert "temperature" in kwargs
    assert kwargs["temperature"] == 0.3


@pytest.mark.unit
def test_temperature_not_in_kwargs_when_absent_from_config():
    """When neither temperature key is present, 'temperature' must not appear in kwargs."""
    cfg = {"llm_provider": "openai"}
    assert "temperature" not in _provider_kwargs(cfg, "deep")
    assert "temperature" not in _provider_kwargs(cfg, "quick")


@pytest.mark.unit
def test_temperature_tiers_are_independent():
    """deep and quick temperatures are read from separate config keys."""
    cfg = {
        "llm_provider": "anthropic",
        "deep_think_temperature": 0.0,
        "quick_think_temperature": 0.3,
    }
    assert _provider_kwargs(cfg, "deep")["temperature"] == 0.0
    assert _provider_kwargs(cfg, "quick")["temperature"] == 0.3
