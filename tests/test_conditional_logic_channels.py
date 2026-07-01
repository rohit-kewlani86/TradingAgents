from types import SimpleNamespace

import pytest

from tradingagents.graph.conditional_logic import ConditionalLogic

ANALYSTS = [
    ("market", "tools_market"),
    ("social", "tools_social"),
    ("news", "tools_news"),
    ("fundamentals", "tools_fundamentals"),
    ("technical", "tools_technical"),
    ("macro", "tools_macro"),
]


def _msg(tool_calls):
    return SimpleNamespace(tool_calls=tool_calls)


@pytest.mark.unit
@pytest.mark.parametrize("analyst,tools_node", ANALYSTS)
def test_continues_to_tools_when_tool_calls_present(analyst, tools_node):
    logic = ConditionalLogic()
    state = {f"{analyst}_messages": [_msg(tool_calls=[{"name": "x"}])]}

    method = getattr(logic, f"should_continue_{analyst}")

    assert method(state) == tools_node


@pytest.mark.unit
@pytest.mark.parametrize("analyst,_tools_node", ANALYSTS)
def test_routes_to_done_barrier_when_no_tool_calls(analyst, _tools_node):
    logic = ConditionalLogic()
    state = {f"{analyst}_messages": [_msg(tool_calls=[])]}

    method = getattr(logic, f"should_continue_{analyst}")

    assert method(state) == f"{analyst.capitalize()} Done"
