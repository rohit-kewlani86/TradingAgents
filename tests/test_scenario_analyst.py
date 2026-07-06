"""Scenario Analyst: quantified bull/base/bear targets + probabilities + EV.

Distinct from the qualitative bull/bear research debate — it emits numbers, not
prose. Placed Research Manager -> Scenario Analyst -> Trader.
"""

from unittest.mock import MagicMock

import pytest
from langchain_core.runnables import RunnableLambda

from tradingagents.agents.schemas import (
    Scenario,
    ScenarioAnalysis,
    render_scenario_analysis,
)


def _analysis():
    return ScenarioAnalysis(
        current_price=100.0,
        bull=Scenario(price_target=130.0, probability=0.3, rationale="beats guidance"),
        base=Scenario(price_target=110.0, probability=0.5, rationale="in line"),
        bear=Scenario(price_target=80.0, probability=0.2, rationale="demand softens"),
        summary="Skewed modestly to the upside.",
    )


@pytest.mark.unit
class TestScenarioSchema:
    def test_schema_accepts_valid_analysis(self):
        sa = _analysis()
        assert sa.bull.price_target == 130.0
        assert sa.base.probability == 0.5


@pytest.mark.unit
class TestRenderScenarioAnalysis:
    def test_renders_each_scenario_target_and_probability(self):
        md = render_scenario_analysis(_analysis())
        assert "130" in md and "110" in md and "80" in md
        # probabilities surfaced (as % or fraction)
        assert "30" in md and "50" in md and "20" in md

    def test_computes_expected_value_as_probability_weighted_target(self):
        md = render_scenario_analysis(_analysis())
        # EV = 0.3*130 + 0.5*110 + 0.2*80 = 39 + 55 + 16 = 110.0
        assert "110.0" in md
        assert "Expected Value" in md

    def test_expected_value_omitted_when_a_target_is_missing(self):
        sa = _analysis()
        sa.bull.price_target = None
        md = render_scenario_analysis(sa)
        assert "Expected Value" not in md


@pytest.mark.unit
class TestScenarioAnalystNode:
    def _state(self):
        return {
            "company_of_interest": "NVDA",
            "trade_date": "2026-01-15",
            "market_report": "uptrend, 100",
            "fundamentals_report": "strong",
            "news_report": "positive",
            "investment_plan": "Overweight; add on dips",
        }

    def test_writes_scenario_report(self):
        from tradingagents.agents.managers.scenario_analyst import create_scenario_analyst

        llm = MagicMock()
        llm.with_structured_output.return_value = RunnableLambda(lambda _: _analysis())
        node = create_scenario_analyst(llm)
        out = node(self._state())
        assert "scenario_report" in out
        assert "Expected Value" in out["scenario_report"]

    def test_binds_scenario_analysis_schema(self):
        from tradingagents.agents.managers.scenario_analyst import create_scenario_analyst

        llm = MagicMock()
        llm.with_structured_output.return_value = RunnableLambda(lambda _: _analysis())
        create_scenario_analyst(llm)
        assert llm.with_structured_output.call_args[0][0] is ScenarioAnalysis

    def test_exported_from_agents_package(self):
        import tradingagents.agents as agents
        assert "create_scenario_analyst" in agents.__all__


@pytest.mark.unit
class TestScenarioGraphWiring:
    def _build(self):
        import tradingagents.graph.setup as setup_mod
        from tradingagents.graph.conditional_logic import ConditionalLogic

        tool_nodes = {"market": (lambda state: {})}
        gs = setup_mod.GraphSetup(
            MagicMock(), MagicMock(), tool_nodes, ConditionalLogic()
        )
        return gs.setup_graph(["market"])

    def test_scenario_node_sits_between_research_manager_and_trader(self):
        wf = self._build()
        assert "Scenario Analyst" in wf.nodes
        assert ("Research Manager", "Scenario Analyst") in wf.edges
        assert ("Scenario Analyst", "Trader") in wf.edges
        # the old direct edge is gone
        assert ("Research Manager", "Trader") not in wf.edges

    def test_graph_compiles(self):
        self._build().compile()


@pytest.mark.unit
class TestScenarioConsumers:
    def test_trader_prompt_includes_scenario_report(self):
        import tradingagents.agents.trader.trader as trader_mod

        captured = {}

        def fake_invoke(structured_llm, plain_llm, prompt, render, name):
            captured["prompt"] = prompt
            return "PLAN"

        original = trader_mod.invoke_structured_or_freetext
        trader_mod.invoke_structured_or_freetext = fake_invoke
        try:
            node = trader_mod.create_trader(MagicMock())
            node(
                {
                    "company_of_interest": "NVDA",
                    "investment_plan": "Overweight",
                    "scenario_report": "EV 110 SCENARIO_MARKER",
                },
                name="Trader",
            )
        finally:
            trader_mod.invoke_structured_or_freetext = original

        # trader prompt is a message list; flatten to text
        text = str(captured["prompt"])
        assert "SCENARIO_MARKER" in text

    def test_portfolio_manager_prompt_includes_scenario_report(self):
        import tradingagents.agents.managers.portfolio_manager as pm_mod

        captured = {}

        def fake_invoke(structured_llm, plain_llm, prompt, render, name):
            captured["prompt"] = prompt
            return "DECISION"

        original = pm_mod.invoke_structured_or_freetext
        pm_mod.invoke_structured_or_freetext = fake_invoke
        try:
            node = pm_mod.create_portfolio_manager(MagicMock())
            node(
                {
                    "company_of_interest": "NVDA",
                    "investment_plan": "Overweight",
                    "trader_investment_plan": "Buy",
                    "scenario_report": "EV 110 SCENARIO_MARKER",
                    "risk_debate_state": {
                        "history": "",
                        "aggressive_history": "",
                        "conservative_history": "",
                        "neutral_history": "",
                        "current_aggressive_response": "",
                        "current_conservative_response": "",
                        "current_neutral_response": "",
                        "judge_decision": "",
                        "count": 1,
                    },
                }
            )
        finally:
            pm_mod.invoke_structured_or_freetext = original

        assert "SCENARIO_MARKER" in str(captured["prompt"])
