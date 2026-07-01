from typing import get_type_hints
from unittest.mock import MagicMock

import pytest

from tradingagents.agents.risk_mgmt.devils_advocate import create_devils_advocate
from tradingagents.agents.utils.agent_states import AgentState


def _state():
    return {
        "company_of_interest": "AAPL",
        "market_report": "m", "sentiment_report": "s", "news_report": "n",
        "fundamentals_report": "f",
        "investment_plan": "**Recommendation**: Buy",
        "trader_investment_plan": "**Action**: Buy",
        "risk_debate_state": {"history": "debate..."},
    }


@pytest.mark.unit
def test_agent_state_has_devils_advocate_critique_field():
    assert "devils_advocate_critique" in get_type_hints(AgentState, include_extras=True)


@pytest.mark.unit
def test_devils_advocate_writes_critique():
    resp = MagicMock(); resp.content = "Pre-mortem: rates assumption is fragile."
    llm = MagicMock(); llm.invoke.return_value = resp
    out = create_devils_advocate(llm)(_state())
    assert "Pre-mortem" in out["devils_advocate_critique"]
    assert "messages" not in out


@pytest.mark.unit
def test_devils_advocate_prompt_has_decision_context():
    prompts = []
    resp = MagicMock(); resp.content = "critique"
    llm = MagicMock(); llm.invoke = lambda p: (prompts.append(p), resp)[1]
    create_devils_advocate(llm)(_state())
    assert "**Recommendation**: Buy" in prompts[0]
    assert "**Action**: Buy" in prompts[0]


@pytest.mark.unit
def test_exported_from_barrel():
    import tradingagents.agents as agents
    assert "create_devils_advocate" in agents.__all__


@pytest.mark.unit
def test_risk_exit_routes_to_devils_advocate():
    from tradingagents.graph.conditional_logic import ConditionalLogic
    logic = ConditionalLogic(max_risk_discuss_rounds=1)
    state = {"risk_debate_state": {"count": 3, "latest_speaker": "Neutral"}}
    assert logic.should_continue_risk_analysis(state) == "Devil's Advocate"


@pytest.mark.unit
def test_wired_between_risk_and_pm():
    import tradingagents.graph.setup as setup_mod
    from tradingagents.graph.conditional_logic import ConditionalLogic
    analysts = ["market", "social", "news", "fundamentals"]
    tool_nodes = {a: (lambda s: {}) for a in analysts}
    wf = setup_mod.GraphSetup(MagicMock(), MagicMock(), tool_nodes, ConditionalLogic()).setup_graph(analysts)
    assert "Devil's Advocate" in wf.nodes
    assert ("Devil's Advocate", "Portfolio Manager") in wf.edges
