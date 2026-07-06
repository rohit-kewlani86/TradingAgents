"""Scenario Analyst: turns the synthesized analysis into quantified bull/base/bear
price scenarios with probabilities and a probability-weighted expected value.

Sits between the Research Manager and the Trader, so the trade plan (and the
Portfolio Manager after it) is built with a quantified outcome distribution in
hand. It complements — does not restate — the qualitative bull/bear debate.
"""

from __future__ import annotations

from tradingagents.agents.schemas import ScenarioAnalysis, render_scenario_analysis
from tradingagents.agents.utils.agent_utils import (
    get_instrument_context_from_state,
    get_language_instruction,
)
from tradingagents.agents.utils.structured import (
    bind_structured,
    invoke_structured_or_freetext,
)


def create_scenario_analyst(llm):
    structured_llm = bind_structured(llm, ScenarioAnalysis, "Scenario Analyst")

    def scenario_analyst_node(state) -> dict:
        instrument_context = get_instrument_context_from_state(state)
        market_report = state.get("market_report", "")
        fundamentals_report = state.get("fundamentals_report", "")
        news_report = state.get("news_report", "")
        investment_plan = state.get("investment_plan", "")

        prompt = f"""You are the Scenario Analyst. Convert the team's analysis into a QUANTIFIED outcome distribution — not a re-argument of the bull/bear debate.

{instrument_context}

Produce exactly three scenarios — bull, base, and bear — each with:
- a specific price target (in the quote currency),
- a probability as a fraction 0-1 (the three must sum to ~1),
- one sentence naming the catalyst/condition that drives it.

Anchor the targets to the current/last price and the levels in the market report. Base your probabilities and targets on the evidence below; do not restate the narrative — quantify it. The expected value is computed from your targets and probabilities, so make them internally consistent.

Market report:
{market_report}

Fundamentals report:
{fundamentals_report}

News report:
{news_report}

Research Manager's investment plan:
{investment_plan}""" + get_language_instruction()

        scenario_report = invoke_structured_or_freetext(
            structured_llm,
            llm,
            prompt,
            render_scenario_analysis,
            "Scenario Analyst",
        )

        return {"scenario_report": scenario_report}

    return scenario_analyst_node
