from typing import get_type_hints

import pytest
from langgraph.graph.message import add_messages

from tradingagents.agents.utils.agent_states import AgentState

ANALYST_CHANNELS = [
    "market_messages",
    "social_messages",
    "news_messages",
    "fundamentals_messages",
]


@pytest.mark.unit
@pytest.mark.parametrize("channel", ANALYST_CHANNELS)
def test_analyst_channel_uses_add_messages_reducer(channel):
    hints = get_type_hints(AgentState, include_extras=True)

    assert channel in hints, f"{channel} missing from AgentState"
    assert add_messages in hints[channel].__metadata__
