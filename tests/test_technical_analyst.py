from typing import get_type_hints
from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from tradingagents.agents.analysts.technical_analyst import create_technical_analyst
from tradingagents.agents.utils.agent_states import AgentState


@pytest.mark.unit
def test_agent_state_has_technical_report_field():
    hints = get_type_hints(AgentState, include_extras=True)
    assert "technical_report" in hints


@pytest.mark.unit
def test_technical_analyst_writes_report():
    msg = AIMessage(content="RSI 68, entry 448-452, ATR stop 435")
    llm = MagicMock()
    llm.bind_tools.return_value = RunnableLambda(lambda _: msg)
    node = create_technical_analyst(llm)

    state = {"trade_date": "2026-01-15", "company_of_interest": "AAPL",
             "messages": [("human", "AAPL")]}
    out = node(state)

    assert out["messages"] == [msg]
    assert out["technical_report"] == "RSI 68, entry 448-452, ATR stop 435"


@pytest.mark.unit
def test_technical_analyst_exported_from_barrel():
    import tradingagents.agents as agents
    assert "create_technical_analyst" in agents.__all__


@pytest.mark.unit
def test_technical_spec_registered():
    from tradingagents.graph.analyst_execution import ANALYST_NODE_SPECS
    spec = ANALYST_NODE_SPECS["technical"]
    assert spec.agent_node == "Technical Analyst"
    assert spec.tool_node == "tools_technical"
    assert spec.report_key == "technical_report"


@pytest.mark.unit
def test_technical_in_cli_order_and_type():
    from cli.models import AnalystType
    from cli.utils import ANALYST_ORDER
    assert AnalystType.TECHNICAL == "technical"
    assert AnalystType.TECHNICAL in [k for _, k in ANALYST_ORDER]
