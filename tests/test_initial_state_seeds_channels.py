import pytest

from tradingagents.graph.propagation import Propagator

CHANNELS = [
    "market_messages",
    "social_messages",
    "news_messages",
    "fundamentals_messages",
    "technical_messages",
    "macro_messages",
]


@pytest.mark.unit
@pytest.mark.parametrize("channel", CHANNELS)
def test_initial_state_seeds_private_channel(channel):
    state = Propagator().create_initial_state("AAPL", "2026-01-15")

    assert state[channel] == [("human", "AAPL")]
