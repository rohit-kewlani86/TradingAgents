from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    get_global_news,
    get_indicators,
    get_language_instruction,
    get_stock_data,
)


def create_macro_analyst(llm):

    def macro_analyst_node(state):
        current_date = state["trade_date"]
        instrument_context = build_instrument_context(state["company_of_interest"])

        tools = [
            get_stock_data,
            get_indicators,
            get_global_news,
        ]

        system_message = (
            """You are a Macro / Regime Analyst. Every other analyst on this team works bottom-up on the company itself; you are the only top-down voice. Your job is NOT to analyze the company — it is to judge the MACRO REGIME the stock trades inside and decide whether that regime is a tailwind, neutral, or headwind for this specific position right now.

Read the regime using these market instruments (call get_stock_data on each symbol, then get_indicators for trend/momentum where useful):
- Interest rates: ^TNX (US 10-year Treasury yield). Rising long rates are a headwind for growth / long-duration / rate-sensitive names; falling rates a tailwind.
- Risk appetite / volatility: ^VIX. Elevated or rising VIX = risk-off (favor quality/defensives, smaller size); low/falling VIX = risk-on.
- US dollar: DX-Y.NYB. A strong/strengthening dollar pressures multinationals and commodities/EM; weakness helps exporters.
- Broad market trend: ^GSPC (S&P 500). Is the index above/below its 50/200-day moving averages (use get_indicators)? Is the tape in an uptrend, downtrend, or chop?
- Sector rotation: the sector ETF most relevant to this company (e.g. XLK technology, XLF financials, XLE energy, XLV healthcare, XLY consumer discretionary, XLP staples, XLI industrials, XLU utilities, XLB materials, XLRE real estate, XLC communication). Compare its trend to ^GSPC to see if money is rotating into or out of this company's sector.

Also call get_global_news to surface scheduled macro catalysts (CPI/inflation prints, FOMC/Fed decisions, jobs reports, GDP) and any regime-shifting headlines around the trade date.

Your deliverable must be regime-specific, not company-specific:
1. Rates read (level + direction of ^TNX, curve context if available) and what it implies for this name.
2. Risk-appetite read (^VIX level/trend) and dollar read (DX-Y.NYB).
3. Broad-market trend (^GSPC vs its moving averages) and sector rotation (sector ETF vs ^GSPC).
4. Upcoming macro catalysts that could move the position in the next few days.
5. A one-line NET VERDICT: macro TAILWIND / NEUTRAL / HEADWIND for this ticker, with a conviction level (low/medium/high) and one sentence of reasoning.

Do not restate the company's fundamentals or price chart — that is other analysts' work. Stay top-down."""
            + """ Append a Markdown table at the end summarizing each macro factor (rates, volatility, dollar, market trend, sector rotation), its current read, and its directional impact (tailwind/neutral/headwind) on this position."""
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

        result = chain.invoke(state["macro_messages"])

        report = ""

        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "macro_messages": [result],
            "macro_report": report,
        }

    return macro_analyst_node
