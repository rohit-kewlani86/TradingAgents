from typing import get_type_hints
from unittest.mock import MagicMock

import pytest

from tradingagents.agents.risk_mgmt.devils_advocate import create_devils_advocate
from tradingagents.agents.utils.agent_states import AgentState


def _state():
    return {
        "company_of_interest": "AAPL",
        "market_report": "Market report",
        "sentiment_report": "Sentiment report",
        "news_report": "News report",
        "fundamentals_report": "Fundamentals report",
        "investment_plan": "**Recommendation**: Buy",
        "trader_investment_plan": "**Action**: Buy",
        "risk_debate_state": {"history": "Aggressive vs conservative vs neutral..."},
    }


@pytest.mark.unit
def test_agent_state_has_devils_advocate_critique_field():
    hints = get_type_hints(AgentState, include_extras=True)
    assert "devils_advocate_critique" in hints


@pytest.mark.unit
def test_devils_advocate_writes_critique_to_state():
    response = MagicMock()
    response.content = "Pre-mortem: the thesis assumes rates stay flat; if they rise this fails."
    llm = MagicMock()
    llm.invoke.return_value = response

    node = create_devils_advocate(llm)
    out = node(_state())

    assert "devils_advocate_critique" in out
    assert "Pre-mortem" in out["devils_advocate_critique"]
    # Must not clobber unrelated channels.
    assert "messages" not in out


@pytest.mark.unit
def test_devils_advocate_prompt_includes_decision_context():
    prompts = []
    response = MagicMock()
    response.content = "critique"
    llm = MagicMock()
    llm.invoke = lambda p: (prompts.append(p), response)[1]

    node = create_devils_advocate(llm)
    node(_state())

    assert prompts
    assert "**Recommendation**: Buy" in prompts[0]
    assert "**Action**: Buy" in prompts[0]


@pytest.mark.unit
def test_devils_advocate_exported_from_barrel():
    import tradingagents.agents as agents

    assert "create_devils_advocate" in agents.__all__
    assert callable(agents.create_devils_advocate)


@pytest.mark.unit
def test_devils_advocate_wired_between_risk_debate_and_pm():
    import tradingagents.graph.setup as setup_mod
    from tradingagents.graph.conditional_logic import ConditionalLogic

    analysts = ["market", "social", "news", "fundamentals", "technical", "macro"]
    tool_nodes = {a: (lambda state: {}) for a in analysts}
    gs = setup_mod.GraphSetup(MagicMock(), MagicMock(), tool_nodes, ConditionalLogic())
    wf = gs.setup_graph(analysts)

    assert "Devil's Advocate" in wf.nodes
    assert ("Devil's Advocate", "Portfolio Manager") in wf.edges
    # Risk debaters route to the Devil's Advocate on exit, not straight to the PM.
    for debater in ("Aggressive Analyst", "Conservative Analyst", "Neutral Analyst"):
        assert ("Portfolio Manager") not in [
            t for s, t in wf.edges if s == debater
        ], f"{debater} should no longer edge directly to Portfolio Manager"
    wf.compile()


@pytest.mark.unit
def test_risk_analysis_exits_to_devils_advocate():
    from types import SimpleNamespace
    from tradingagents.graph.conditional_logic import ConditionalLogic

    logic = ConditionalLogic(max_risk_discuss_rounds=1)
    # count high enough to end the risk debate (3 speakers * 1 round = 3)
    state = {"risk_debate_state": {"count": 3, "latest_speaker": "Neutral"}}

    assert logic.should_continue_risk_analysis(state) == "Devil's Advocate"
