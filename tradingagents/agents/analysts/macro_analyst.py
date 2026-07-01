from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tradingagents.agents.utils.agent_utils import (
    get_global_news,
    get_indicators,
    get_instrument_context_from_state,
    get_language_instruction,
    get_macro_indicators,
    get_stock_data,
)


def create_macro_analyst(llm):

    def macro_analyst_node(state):
        current_date = state["trade_date"]
        instrument_context = get_instrument_context_from_state(state)

        tools = [
            get_macro_indicators,
            get_stock_data,
            get_indicators,
            get_global_news,
        ]

        system_message = (
            """You are a Macro / Regime Analyst. Every other analyst on this team works bottom-up on the company itself; you are the only top-down voice. Your job is NOT to analyze the company — it is to judge the MACRO REGIME the stock trades inside and decide whether that regime is a tailwind, neutral, or headwind for this specific position right now.

Read the regime using two complementary sources:

Use get_macro_indicators (FRED) for the hard macro series — call it per indicator with these aliases:
- 10y_treasury and yield_curve: level/direction of long rates and the curve. Rising long rates or an inverting curve are a headwind for growth / long-duration / rate-sensitive names.
- fed_funds_rate: the policy stance.
- cpi and core_pce: inflation trajectory.
- unemployment: labor-market / growth backdrop.
- vix: risk appetite. Elevated/rising = risk-off (favor quality, smaller size); low/falling = risk-on.

Use get_stock_data + get_indicators (yfinance) for market trend and rotation, which FRED does not cover:
- ^GSPC (S&P 500): is the tape above/below its 50/200-day moving averages? Uptrend, downtrend, or chop?
- the sector ETF most relevant to this company (XLK tech, XLF financials, XLE energy, XLV healthcare, XLY discretionary, XLP staples, XLI industrials, XLU utilities, XLB materials, XLRE real estate, XLC communication). Compare its trend to ^GSPC to see if money is rotating into or out of this company's sector.

Also call get_global_news for scheduled macro catalysts (CPI/FOMC/jobs/GDP) and regime-shifting headlines around the trade date.

Your deliverable must be regime-specific, not company-specific:
1. Rates & inflation read (10y, curve, fed funds, CPI/PCE) and what it implies for this name.
2. Risk-appetite read (VIX).
3. Broad-market trend (^GSPC vs its moving averages) and sector rotation (sector ETF vs ^GSPC).
4. Upcoming macro catalysts in the next few days.
5. A one-line NET VERDICT: macro TAILWIND / NEUTRAL / HEADWIND for this ticker, with a conviction level (low/medium/high) and one sentence of reasoning.

Do not restate the company's fundamentals or price chart — that is other analysts' work. Stay top-down."""
            + """ Append a Markdown table at the end summarizing each macro factor (rates, inflation, volatility, market trend, sector rotation), its current read, and its directional impact (tailwind/neutral/headwind) on this position."""
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
                    " You have access to the following tools: {tool_names}."
                    " Today's date is {current_date}; treat it as 'now' for all analysis and tool-call date ranges. {instrument_context}\n"
                    "{system_message}",
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
            "macro_report": report,
        }

    return macro_analyst_node
