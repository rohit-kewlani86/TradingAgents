from unittest.mock import MagicMock

import pytest
from langgraph.graph import START

import tradingagents.graph.setup as setup_mod
from tradingagents.graph.conditional_logic import ConditionalLogic

ANALYSTS = ["market", "social", "news", "fundamentals", "technical", "macro"]
AGENT_NODES = {
    "market": "Market Analyst",
    "social": "Sentiment Analyst",
    "news": "News Analyst",
    "fundamentals": "Fundamentals Analyst",
    "technical": "Technical Analyst",
    "macro": "Macro Analyst",
}
DONE_NODES = {
    "market": "Market Done",
    "social": "Sentiment Done",
    "news": "News Done",
    "fundamentals": "Fundamentals Done",
    "technical": "Technical Done",
    "macro": "Macro Done",
}


def _build(analysts):
    tool_nodes = {a: (lambda state: {}) for a in analysts}
    gs = setup_mod.GraphSetup(MagicMock(), MagicMock(), tool_nodes, ConditionalLogic())
    return gs.setup_graph(analysts)


@pytest.mark.unit
def test_start_fans_out_to_every_analyst():
    wf = _build(ANALYSTS)
    for a in ANALYSTS:
        assert (START, AGENT_NODES[a]) in wf.edges


@pytest.mark.unit
def test_no_msg_clear_nodes_remain():
    wf = _build(ANALYSTS)
    assert [n for n in wf.nodes if "Msg Clear" in n] == []


@pytest.mark.unit
def test_each_analyst_has_done_barrier_node():
    wf = _build(ANALYSTS)
    for a in ANALYSTS:
        assert DONE_NODES[a] in wf.nodes


@pytest.mark.unit
def test_done_nodes_join_at_bull_researcher_as_barrier():
    wf = _build(ANALYSTS)
    expected = tuple(DONE_NODES[a] for a in ANALYSTS)
    assert (expected, "Bull Researcher") in wf.waiting_edges


@pytest.mark.unit
def test_each_analyst_tool_loop_edge_present():
    wf = _build(ANALYSTS)
    for a in ANALYSTS:
        assert (f"tools_{a}", AGENT_NODES[a]) in wf.edges


@pytest.mark.unit
def test_topology_compiles():
    _build(ANALYSTS).compile()
