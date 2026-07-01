from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tradingagents.agents.utils.agent_utils import (
    get_indicators,
    get_instrument_context_from_state,
    get_language_instruction,
    get_stock_data,
)


def create_technical_analyst(llm):

    def technical_analyst_node(state):
        current_date = state["trade_date"]
        instrument_context = get_instrument_context_from_state(state)

        tools = [
            get_stock_data,
            get_indicators,
        ]

        system_message = (
            """You are a technical analyst focused on trade timing, not long-term trend context. The Market Analyst already covers trend direction with moving averages, so your job is the complementary one: decide WHEN to act and at WHAT levels. Concentrate on momentum, volatility, and actionable price levels using up to **6 indicators** that give complementary signals without redundancy:

Momentum / Oscillators:
- rsi: RSI: Flags overbought (>70) / oversold (<30) conditions and bullish/bearish divergence. Usage: time reversals and pullback entries. Tips: in strong trends RSI can stay extreme — confirm with price structure.
- macd: MACD: Momentum via EMA differences. Usage: trade signal-line crossovers and divergence to time entries/exits.
- macds: MACD Signal: EMA smoothing of MACD. Usage: crossover triggers against the MACD line.
- macdh: MACD Histogram: gap between MACD and its signal. Usage: spot momentum acceleration/exhaustion early.

Volatility / Levels:
- boll: Bollinger Middle (20 SMA): dynamic mean for mean-reversion context.
- boll_ub: Bollinger Upper Band: overbought / breakout zone; potential exit or breakout entry.
- boll_lb: Bollinger Lower Band: oversold / potential bounce entry.
- atr: ATR: current volatility. Usage: size positions and set concrete stop-loss / take-profit distances.

Your deliverable must be **timing- and level-specific**, not a restatement of the trend:
1. Current momentum read (overbought/oversold, divergences, crossovers).
2. Concrete support/resistance levels and recent breakout/breakdown points (derive from price and Bollinger bands).
3. A suggested entry zone, an ATR-based stop-loss, and a take-profit/target level.
4. Near-term timing bias (e.g., wait for pullback / breakout confirmation).

Call get_stock_data first to retrieve the CSV needed for indicators, then call get_indicators with the exact indicator names above (otherwise the call fails). Do not select redundant indicators. Write a detailed, evidence-backed report with specific numeric levels."""
            + """ Make sure to append a Markdown table at the end of the report summarizing the key levels (entry, stop, target) and signals, organized and easy to read."""
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

        result = chain.invoke(state["technical_messages"])

        report = ""

        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "technical_messages": [result],
            "technical_report": report,
        }

    return technical_analyst_node
