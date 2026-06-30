"""Tests that Bull and Bear researchers include technical_report in their prompts."""
import pytest
from unittest.mock import MagicMock

from tradingagents.agents.researchers.bull_researcher import create_bull_researcher
from tradingagents.agents.researchers.bear_researcher import create_bear_researcher


def _make_state(technical_report="RSI: 68, MACD bullish crossover"):
    """Minimal AgentState-like dict for researcher tests."""
    return {
        "market_report": "Market report content",
        "sentiment_report": "Sentiment report content",
        "news_report": "News report content",
        "fundamentals_report": "Fundamentals report content",
        "technical_report": technical_report,
        "investment_debate_state": {
            "history": "",
            "bull_history": "",
            "bear_history": "",
            "current_response": "",
            "count": 0,
        },
    }


def _make_llm(captured: list):
    """Return a mock LLM that records every prompt passed to it."""
    mock_response = MagicMock()
    mock_response.content = "mock argument"
    llm = MagicMock()
    llm.invoke = lambda prompt: (captured.append(prompt), mock_response)[1]
    return llm


@pytest.mark.unit
def test_bull_researcher_includes_technical_report_in_prompt():
    """Bull researcher must pass technical_report content to its LLM prompt."""
    prompts = []
    node = create_bull_researcher(_make_llm(prompts))
    node(_make_state("RSI: 68, MACD bullish crossover"))
    assert prompts, "LLM was never invoked"
    assert "RSI: 68, MACD bullish crossover" in prompts[0]


@pytest.mark.unit
def test_bear_researcher_includes_technical_report_in_prompt():
    """Bear researcher must pass technical_report content to its LLM prompt."""
    prompts = []
    node = create_bear_researcher(_make_llm(prompts))
    node(_make_state("RSI: 82, overbought — bearish divergence"))
    assert prompts, "LLM was never invoked"
    assert "RSI: 82, overbought — bearish divergence" in prompts[0]


@pytest.mark.unit
def test_bull_researcher_handles_missing_technical_report():
    """Bull researcher must not crash when technical_report is absent or empty."""
    prompts = []
    state = _make_state("")
    del state["technical_report"]  # simulate key missing entirely
    node = create_bull_researcher(_make_llm(prompts))
    node(state)  # must not raise


@pytest.mark.unit
def test_bear_researcher_handles_missing_technical_report():
    """Bear researcher must not crash when technical_report is absent or empty."""
    prompts = []
    state = _make_state("")
    del state["technical_report"]
    node = create_bear_researcher(_make_llm(prompts))
    node(state)  # must not raise
