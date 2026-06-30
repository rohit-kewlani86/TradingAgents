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
