"""Devil's Advocate / Red Team: a pre-mortem stress-test of the emerging decision.

Runs after the risk debate and before the Portfolio Manager. The bull/bear and
risk debaters each argue an assigned stance; nobody attacks the *collective*
direction for groupthink. This node does exactly that: it assumes the decision
turns out wrong and reasons backwards to find the assumptions, blind spots, and
disconfirming evidence that would cause the failure. The Portfolio Manager reads
the critique before finalising, so it sharpens the decision rather than replacing
any stance in the debate.
"""

from __future__ import annotations

from tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    get_language_instruction,
)


def create_devils_advocate(llm):
    def devils_advocate_node(state) -> dict:
        instrument_context = build_instrument_context(state["company_of_interest"])

        research_plan = state.get("investment_plan", "")
        trader_plan = state.get("trader_investment_plan", "")
        risk_history = state.get("risk_debate_state", {}).get("history", "")
        market_report = state.get("market_report", "")
        sentiment_report = state.get("sentiment_report", "")
        news_report = state.get("news_report", "")
        fundamentals_report = state.get("fundamentals_report", "")

        prompt = f"""You are the Devil's Advocate — an independent red team. Your job is NOT to pick a side or add another opinion to the debate. It is to stress-test the emerging consensus for groupthink and surface why it might be wrong.

{instrument_context}

Run a pre-mortem: assume it is months from now and this decision has turned out badly. Reason backwards to explain the failure.

Cover, concisely and specifically:
1. Load-bearing assumptions — what must be true for this decision to work, and how fragile is each?
2. Disconfirming evidence — what in the analysts' reports was underweighted or explained away?
3. Blind spots / base rates — what has the whole team converged on that a skeptic would question? Are we anchoring, chasing momentum, or ignoring the base rate?
4. Failure modes — the two or three most plausible ways this loses money.
5. Verdict — a one-line call: does the decision survive scrutiny as-is, or should the Portfolio Manager reconsider or size down? Be direct.

Be adversarial but fair — attack the strongest version of the thesis, not a strawman.

**Research Manager's investment plan:**
{research_plan}

**Trader's proposal:**
{trader_plan}

**Risk analysts' debate:**
{risk_history}

**Analyst reports for reference:**
- Market: {market_report}
- Sentiment: {sentiment_report}
- News: {news_report}
- Fundamentals: {fundamentals_report}

Write conversationally, no special formatting required.{get_language_instruction()}"""

        response = llm.invoke(prompt)
        critique = f"Devil's Advocate: {response.content}"

        return {"devils_advocate_critique": critique}

    return devils_advocate_node
