import pytest

CHANNELS = [
    ("market", "market_messages"),
    ("social", "social_messages"),
    ("news", "news_messages"),
    ("fundamentals", "fundamentals_messages"),
]


@pytest.mark.unit
@pytest.mark.parametrize("analyst,channel", CHANNELS)
def test_tool_node_appends_to_private_channel(mock_llm_client, analyst, channel):
    from tradingagents.default_config import DEFAULT_CONFIG
    from tradingagents.graph.trading_graph import TradingAgentsGraph

    ta = TradingAgentsGraph(config=DEFAULT_CONFIG.copy())

    assert ta.tool_nodes[analyst]._messages_key == channel
