from typing import get_type_hints
from unittest.mock import MagicMock

import pytest

from tradingagents.agents.managers.position_sizer import create_position_sizer
from tradingagents.agents.schemas import PositionSizingPlan, render_position_sizing_plan
from tradingagents.agents.utils.agent_states import AgentState


def _state():
    return {
        "company_of_interest": "AAPL",
        "final_trade_decision": "**Rating**: Buy",
        "technical_report": "ATR 15; stop 435",
        "macro_report": "VIX low; TAILWIND",
        "risk_debate_state": {"history": "debate..."},
    }


@pytest.mark.unit
def test_agent_state_has_position_sizing_plan_field():
    assert "position_sizing_plan" in get_type_hints(AgentState, include_extras=True)


@pytest.mark.unit
def test_render_includes_core_fields():
    plan = PositionSizingPlan(
        recommended_size_pct=5.0, entry_price=450.0, stop_loss=435.0,
        target_price=490.0, risk_reward_ratio=2.6, sizing_rationale="2% risk",
    )
    md = render_position_sizing_plan(plan)
    assert "Recommended Size" in md and "5.0" in md and "435.0" in md


@pytest.mark.unit
def test_position_sizer_writes_plan():
    plan = PositionSizingPlan(recommended_size_pct=5.0, sizing_rationale="2% risk")
    structured = MagicMock()
    structured.invoke.return_value = plan
    llm = MagicMock()
    llm.with_structured_output.return_value = structured

    out = create_position_sizer(llm)(_state())
    assert "Recommended Size" in out["position_sizing_plan"]


@pytest.mark.unit
def test_exported_from_barrel():
    import tradingagents.agents as agents
    assert "create_position_sizer" in agents.__all__


@pytest.mark.unit
def test_wired_after_portfolio_manager():
    import tradingagents.graph.setup as setup_mod
    from tradingagents.graph.conditional_logic import ConditionalLogic
    from langgraph.graph import END

    analysts = ["market", "social", "news", "fundamentals"]
    tool_nodes = {a: (lambda s: {}) for a in analysts}
    wf = setup_mod.GraphSetup(MagicMock(), MagicMock(), tool_nodes, ConditionalLogic()).setup_graph(analysts)
    assert "Position Sizer" in wf.nodes
    assert ("Portfolio Manager", "Position Sizer") in wf.edges
    assert ("Position Sizer", END) in wf.edges
    assert ("Portfolio Manager", END) not in wf.edges
