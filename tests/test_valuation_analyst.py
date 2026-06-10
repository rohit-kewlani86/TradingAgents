"""Pre-IPO Market & Valuation Analyst node."""

from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from tradingagents.agents.analysts.valuation_analyst import create_valuation_analyst


def _state():
    return {
        "trade_date": "2026-01-15",
        "company_of_interest": "SpaceX",
        "messages": [("human", "SpaceX")],
    }


@pytest.mark.unit
class TestValuationAnalyst:
    def test_writes_market_report_from_content_when_no_tool_calls(self):
        llm = MagicMock()
        llm.bind_tools.return_value = RunnableLambda(
            lambda _: AIMessage(content="Pre-IPO valuation report for SpaceX.")
        )
        node = create_valuation_analyst(llm)
        out = node(_state())
        assert out["market_report"] == "Pre-IPO valuation report for SpaceX."

    def test_binds_valuation_tool(self):
        llm = MagicMock()
        llm.bind_tools.return_value = RunnableLambda(lambda _: AIMessage(content="x"))
        node = create_valuation_analyst(llm)
        node(_state())
        bound_tools = llm.bind_tools.call_args[0][0]
        tool_names = {t.name for t in bound_tools}
        assert "get_valuation" in tool_names
