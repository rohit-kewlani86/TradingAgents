"""Position Sizer: turns the Portfolio Manager's rating into a placeable order.

Runs after the Portfolio Manager. It converts the directional decision into a
concrete position size and entry/stop/target levels, anchored on the Technical
Analyst's ATR (stop distance) and scaled by the Macro Analyst's volatility
regime and the risk debate's conviction. Uses the same structured-output +
graceful-fallback pattern as the Portfolio Manager and Trader.
"""

from __future__ import annotations

from tradingagents.agents.schemas import (
    PositionSizingPlan,
    render_position_sizing_plan,
)
from tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    get_language_instruction,
)
from tradingagents.agents.utils.structured import (
    bind_structured,
    invoke_structured_or_freetext,
)


def create_position_sizer(llm):
    structured_llm = bind_structured(llm, PositionSizingPlan, "Position Sizer")

    def position_sizer_node(state) -> dict:
        instrument_context = build_instrument_context(state["company_of_interest"])

        final_trade_decision = state.get("final_trade_decision", "")
        technical_report = state.get("technical_report", "")
        macro_report = state.get("macro_report", "")
        risk_history = state.get("risk_debate_state", {}).get("history", "")

        prompt = f"""As the Position Sizer, convert the Portfolio Manager's decision into a concrete, placeable order.

{instrument_context}

Your job is NOT to re-decide direction — the rating below is final. Size the position and set levels.

Sizing principles:
- Bound account risk (typically <= 2% of equity at the stop).
- Anchor the stop distance on the Technical Analyst's ATR; derive the entry and target from the reported levels.
- Scale size DOWN in high-volatility (elevated VIX) regimes and UP with stronger conviction from the risk debate.
- For a Hold / Sell / avoid rating, recommend 0% new exposure and say so plainly.

---

**Portfolio Manager's final decision:**
{final_trade_decision}

**Technical analysis (ATR, entry zone, stop/target levels):**
{technical_report}

**Macro / regime context (volatility, risk appetite):**
{macro_report}

**Risk analysts' debate (for conviction):**
{risk_history}

---

Produce a specific size and levels grounded in the ATR and the regime.{get_language_instruction()}"""

        position_sizing_plan = invoke_structured_or_freetext(
            structured_llm,
            llm,
            prompt,
            render_position_sizing_plan,
            "Position Sizer",
        )

        return {"position_sizing_plan": position_sizing_plan}

    return position_sizer_node
