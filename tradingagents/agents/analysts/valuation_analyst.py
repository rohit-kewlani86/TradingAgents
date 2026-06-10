from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    get_fundamentals,
    get_language_instruction,
    get_news,
)
from tradingagents.agents.utils.valuation_tools import get_valuation


def create_valuation_analyst(llm):
    """Pre-IPO replacement for the Market/Technical Analyst.

    A company that has not listed has no price history, so MACD/RSI-style
    technical analysis is impossible. This analyst instead reasons about
    private valuation: funding-round marks, secondary-market prices,
    comparable public-company multiples, and the proposed IPO price range.
    It writes the same ``market_report`` slot so the rest of the graph is
    unchanged.
    """

    def valuation_analyst_node(state):
        current_date = state["trade_date"]
        instrument_context = build_instrument_context(state["company_of_interest"])

        tools = [
            get_valuation,
            get_fundamentals,
            get_news,
        ]

        system_message = (
            """You are a pre-IPO market and valuation analyst. The company you are analysing is NOT yet publicly traded, so there is no price history and no technical indicators to compute. Your job is to establish a valuation view from private-market evidence.

Use the tools to gather:
- get_valuation: latest private valuation, funding-round history, secondary-market marks, and comparable public-company multiples.
- get_fundamentals: registration-statement (S-1/F-1) disclosure when the company has filed to go public; otherwise note that audited public financials are not yet available.
- get_news: recent news bearing on the IPO timeline, demand, and sentiment.

Assess: implied valuation vs comparable listed peers (is the rumoured/last-round valuation rich or cheap on revenue/EBITDA multiples?), funding trajectory and dilution, the credibility and timing of the IPO, and the key risks specific to investing before a public market exists (illiquidity, lock-ups, information asymmetry, down-round risk). Be explicit when data is missing and reason about what its absence implies.

Write a detailed, nuanced report with specific, actionable insights to help the team decide whether to SUBSCRIBE to the IPO, WAIT, or SKIP."""
            + """ Make sure to append a Markdown table at the end of the report to organize key valuation points, organized and easy to read."""
            + get_language_instruction()
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant, collaborating with other assistants."
                    " Use the provided tools to progress towards answering the question."
                    " If you are unable to fully answer, that's OK; another assistant with different tools"
                    " will help where you left off. Execute what you can to make progress."
                    " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
                    " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
                    " You have access to the following tools: {tool_names}.\n{system_message}"
                    "For your reference, the current date is {current_date}. {instrument_context}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(instrument_context=instrument_context)

        chain = prompt | llm.bind_tools(tools)

        result = chain.invoke(state["messages"])

        report = ""
        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "messages": [result],
            "market_report": report,
        }

    return valuation_analyst_node
