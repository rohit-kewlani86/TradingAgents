from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from tradingagents.agents.analysts.technical_analyst import create_technical_analyst


@pytest.mark.unit
def test_technical_analyst_reads_and_writes_private_channel():
    msg = AIMessage(content="technical report text")
    llm = MagicMock()
    llm.bind_tools.return_value = RunnableLambda(lambda _: msg)
    node = create_technical_analyst(llm)

    state = {
        "trade_date": "2026-01-15",
        "company_of_interest": "AAPL",
        "technical_messages": [("human", "AAPL")],
    }
    out = node(state)

    assert out["technical_messages"] == [msg]
    assert out["technical_report"] == "technical report text"
    assert "messages" not in out


@pytest.mark.unit
def test_technical_analyst_exported_from_barrel():
    import tradingagents.agents as agents

    assert "create_technical_analyst" in agents.__all__
    assert callable(agents.create_technical_analyst)
