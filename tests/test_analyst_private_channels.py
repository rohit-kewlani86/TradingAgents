from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from tradingagents.agents.analysts.fundamentals_analyst import (
    create_fundamentals_analyst,
)
from tradingagents.agents.analysts.market_analyst import create_market_analyst
from tradingagents.agents.analysts.news_analyst import create_news_analyst
from tradingagents.agents.analysts.social_media_analyst import (
    create_social_media_analyst,
)
from tradingagents.agents.analysts.valuation_analyst import create_valuation_analyst

CASES = [
    ("market", create_market_analyst, "market_messages", "market_report"),
    ("social", create_social_media_analyst, "social_messages", "sentiment_report"),
    ("news", create_news_analyst, "news_messages", "news_report"),
    (
        "fundamentals",
        create_fundamentals_analyst,
        "fundamentals_messages",
        "fundamentals_report",
    ),
    ("valuation", create_valuation_analyst, "market_messages", "market_report"),
]


@pytest.mark.unit
@pytest.mark.parametrize(
    "name,factory,channel,report_field", CASES, ids=[c[0] for c in CASES]
)
def test_analyst_reads_and_writes_private_channel(name, factory, channel, report_field):
    msg = AIMessage(content="report text")
    llm = MagicMock()
    llm.bind_tools.return_value = RunnableLambda(lambda _: msg)
    node = factory(llm)

    state = {
        "trade_date": "2026-01-15",
        "company_of_interest": "AAPL",
        channel: [("human", "AAPL")],
    }
    out = node(state)

    assert out[channel] == [msg]
    assert out[report_field] == "report text"
    assert "messages" not in out
