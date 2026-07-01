from typing import get_type_hints

import pytest
from langgraph.graph.message import add_messages

from tradingagents.agents.utils.agent_states import AgentState


@pytest.mark.unit
def test_agent_state_has_macro_messages_channel():
    hints = get_type_hints(AgentState, include_extras=True)

    assert "macro_messages" in hints
    assert add_messages in hints["macro_messages"].__metadata__


@pytest.mark.unit
def test_agent_state_has_macro_report_field():
    hints = get_type_hints(AgentState, include_extras=True)

    assert "macro_report" in hints
