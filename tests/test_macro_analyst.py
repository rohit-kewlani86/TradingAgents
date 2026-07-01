from typing import get_type_hints
from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from tradingagents.agents.analysts.macro_analyst import create_macro_analyst
from tradingagents.agents.utils.agent_states import AgentState


@pytest.mark.unit
def test_agent_state_has_macro_report_field():
    hints = get_type_hints(AgentState, include_extras=True)
    assert "macro_report" in hints


@pytest.mark.unit
def test_macro_analyst_writes_report():
    msg = AIMessage(content="10y rising, VIX low, sector tailwind — net TAILWIND")
    llm = MagicMock()
    llm.bind_tools.return_value = RunnableLambda(lambda _: msg)
    node = create_macro_analyst(llm)

    state = {"trade_date": "2026-01-15", "company_of_interest": "AAPL",
             "macro_messages": [("human", "AAPL")]}
    out = node(state)

    assert out["macro_messages"] == [msg]
    assert out["macro_report"] == "10y rising, VIX low, sector tailwind — net TAILWIND"


@pytest.mark.unit
def test_macro_analyst_binds_fred_and_yfinance_tools():
    """Reconciled design: FRED (get_macro_indicators) + yfinance price tools."""
    captured = {}
    llm = MagicMock()

    def _bind(tools):
        captured["names"] = [t.name for t in tools]
        return RunnableLambda(lambda _: AIMessage(content="x"))

    llm.bind_tools.side_effect = _bind
    node = create_macro_analyst(llm)
    node({"trade_date": "2026-01-15", "company_of_interest": "AAPL",
          "macro_messages": [("human", "AAPL")]})

    assert "get_macro_indicators" in captured["names"]
    assert "get_stock_data" in captured["names"]


@pytest.mark.unit
def test_macro_analyst_exported_and_specced():
    import tradingagents.agents as agents
    from tradingagents.graph.analyst_execution import ANALYST_NODE_SPECS
    assert "create_macro_analyst" in agents.__all__
    assert ANALYST_NODE_SPECS["macro"].report_key == "macro_report"


@pytest.mark.unit
def test_macro_in_cli_order_and_type():
    from cli.models import AnalystType
    from cli.utils import ANALYST_ORDER
    assert AnalystType.MACRO == "macro"
    assert AnalystType.MACRO in [k for _, k in ANALYST_ORDER]
