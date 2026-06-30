from typing import get_type_hints

import pytest
from langgraph.graph.message import add_messages

from tradingagents.agents.utils.agent_states import AgentState


@pytest.mark.unit
def test_agent_state_has_technical_messages_channel():
    hints = get_type_hints(AgentState, include_extras=True)

    assert "technical_messages" in hints
    assert add_messages in hints["technical_messages"].__metadata__


@pytest.mark.unit
def test_agent_state_has_technical_report_field():
    hints = get_type_hints(AgentState, include_extras=True)

    assert "technical_report" in hints
