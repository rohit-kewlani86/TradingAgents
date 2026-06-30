import pytest

from tradingagents.llm_clients.google_client import GoogleClient
from tradingagents.llm_clients.openai_client import OpenAIClient
from tradingagents.llm_clients.anthropic_client import AnthropicClient


@pytest.mark.unit
def test_google_forwards_max_output_tokens():
    llm = GoogleClient(
        "gemini-2.5-flash", api_key="x", max_output_tokens=8192
    ).get_llm()
    assert llm.max_output_tokens == 8192


@pytest.mark.unit
def test_openai_forwards_max_tokens():
    llm = OpenAIClient(
        "gpt-4.1", provider="openai", api_key="x", max_tokens=4096
    ).get_llm()
    assert llm.max_tokens == 4096


# ── Temperature passthrough tests ────────────────────────────────────────────

@pytest.mark.unit
def test_openai_forwards_temperature():
    llm = OpenAIClient(
        "gpt-4.1", provider="openai", api_key="x", temperature=0.3
    ).get_llm()
    assert llm.temperature == 0.3


@pytest.mark.unit
def test_openai_forwards_temperature_zero():
    """0.0 is a valid temperature — must not be skipped by falsy check."""
    llm = OpenAIClient(
        "gpt-4.1", provider="openai", api_key="x", temperature=0.0
    ).get_llm()
    assert llm.temperature == 0.0


@pytest.mark.unit
def test_anthropic_forwards_temperature():
    llm = AnthropicClient(
        "claude-opus-4-8", api_key="x", temperature=0.3
    ).get_llm()
    assert llm.temperature == 0.3


@pytest.mark.unit
def test_google_forwards_temperature_when_thinking_disabled():
    """Temperature is forwarded when thinking is not active."""
    llm = GoogleClient(
        "gemini-2.5-flash", api_key="x", temperature=0.3
    ).get_llm()
    assert llm.temperature == 0.3


@pytest.mark.unit
def test_google_omits_temperature_when_thinking_enabled():
    """Gemini 2.5 with thinking_budget=-1 does not accept temperature.
    The client must NOT forward the caller's temperature — the LLM falls
    back to its provider default (0.7) rather than using our value (0.1)."""
    llm = GoogleClient(
        "gemini-2.5-flash", api_key="x", thinking_level="high", temperature=0.1
    ).get_llm()
    assert getattr(llm, "temperature", None) != 0.1
