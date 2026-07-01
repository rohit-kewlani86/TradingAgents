from typing import get_type_hints
from unittest.mock import MagicMock

import pytest

from tradingagents.agents.managers.position_sizer import create_position_sizer
from tradingagents.agents.schemas import PositionSizingPlan
from tradingagents.agents.utils.agent_states import AgentState


def _state():
    return {
        "company_of_interest": "AAPL",
        "final_trade_decision": "**Rating**: Buy\n**Executive Summary**: enter now.",
        "technical_report": "ATR: 15.0; entry zone 448-452; stop 435.",
        "macro_report": "VIX low, risk-on regime — TAILWIND.",
        "risk_debate_state": {"history": "Aggressive vs conservative debate..."},
    }


@pytest.mark.unit
def test_agent_state_has_position_sizing_plan_field():
    hints = get_type_hints(AgentState, include_extras=True)
    assert "position_sizing_plan" in hints


@pytest.mark.unit
def test_position_sizer_writes_rendered_plan_to_state():
    plan = PositionSizingPlan(
        recommended_size_pct=5.0,
        stop_loss=435.0,
        sizing_rationale="2% risk, ATR stop 15.",
    )
    structured = MagicMock()
    structured.invoke.return_value = plan
    llm = MagicMock()
    llm.with_structured_output.return_value = structured

    node = create_position_sizer(llm)
    out = node(_state())

    assert "position_sizing_plan" in out
    assert "Recommended Size" in out["position_sizing_plan"]
    assert "5.0" in out["position_sizing_plan"]


@pytest.mark.unit
def test_position_sizer_exported_from_barrel():
    import tradingagents.agents as agents

    assert "create_position_sizer" in agents.__all__
    assert callable(agents.create_position_sizer)


@pytest.mark.unit
def test_position_sizer_wired_after_portfolio_manager():
    from langgraph.graph import END
    import tradingagents.graph.setup as setup_mod
    from tradingagents.graph.conditional_logic import ConditionalLogic

    analysts = ["market", "social", "news", "fundamentals", "technical", "macro"]
    tool_nodes = {a: (lambda state: {}) for a in analysts}
    gs = setup_mod.GraphSetup(MagicMock(), MagicMock(), tool_nodes, ConditionalLogic())
    wf = gs.setup_graph(analysts)

    assert "Position Sizer" in wf.nodes
    assert ("Portfolio Manager", "Position Sizer") in wf.edges
    assert ("Position Sizer", END) in wf.edges
    # Portfolio Manager must no longer terminate the graph directly.
    assert ("Portfolio Manager", END) not in wf.edges
    wf.compile()
