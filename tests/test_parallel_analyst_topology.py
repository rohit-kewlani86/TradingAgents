from unittest.mock import MagicMock

import pytest
from langgraph.graph import START

import tradingagents.graph.setup as setup_mod
from tradingagents.graph.conditional_logic import ConditionalLogic

ANALYSTS = ["market", "social", "news", "fundamentals", "technical", "macro"]


def _build_workflow(analysts):
    tool_nodes = {a: (lambda state: {}) for a in analysts}
    gs = setup_mod.GraphSetup(MagicMock(), MagicMock(), tool_nodes, ConditionalLogic())
    return gs.setup_graph(analysts)


@pytest.mark.unit
def test_start_fans_out_to_every_analyst():
    wf = _build_workflow(ANALYSTS)
    for analyst in ANALYSTS:
        assert (START, f"{analyst.capitalize()} Analyst") in wf.edges


@pytest.mark.unit
def test_no_msg_clear_nodes_remain():
    wf = _build_workflow(ANALYSTS)
    assert [n for n in wf.nodes if "Msg Clear" in n] == []


@pytest.mark.unit
def test_each_analyst_has_done_barrier_node():
    wf = _build_workflow(ANALYSTS)
    for analyst in ANALYSTS:
        assert f"{analyst.capitalize()} Done" in wf.nodes


@pytest.mark.unit
def test_done_nodes_join_at_bull_researcher_as_barrier():
    wf = _build_workflow(ANALYSTS)
    expected_sources = tuple(f"{a.capitalize()} Done" for a in ANALYSTS)

    assert (expected_sources, "Bull Researcher") in wf.waiting_edges


@pytest.mark.unit
def test_each_analyst_tool_loop_edge_present():
    wf = _build_workflow(ANALYSTS)
    for analyst in ANALYSTS:
        assert (f"tools_{analyst}", f"{analyst.capitalize()} Analyst") in wf.edges


@pytest.mark.unit
def test_each_analyst_has_conditional_branch():
    wf = _build_workflow(ANALYSTS)
    for analyst in ANALYSTS:
        assert f"{analyst.capitalize()} Analyst" in wf.branches


@pytest.mark.unit
def test_topology_compiles():
    wf = _build_workflow(ANALYSTS)
    wf.compile()
