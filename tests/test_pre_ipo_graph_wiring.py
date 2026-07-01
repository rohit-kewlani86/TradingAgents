"""Graph wiring swaps the Market Analyst for the Valuation Analyst in pre-IPO mode."""

from unittest.mock import MagicMock

import pytest

import tradingagents.graph.setup as setup_mod
from tradingagents.graph.conditional_logic import ConditionalLogic


def _patch_analyst_factories(monkeypatch):
    called = {}

    def mk(name):
        def factory(llm):
            called[name] = True
            return lambda state: {}
        return factory

    monkeypatch.setattr(setup_mod, "create_market_analyst", mk("market"))
    monkeypatch.setattr(setup_mod, "create_valuation_analyst", mk("valuation"))
    return called


@pytest.mark.unit
class TestGraphSetupAnalystSelection:
    def test_listed_mode_uses_market_analyst(self, monkeypatch):
        called = _patch_analyst_factories(monkeypatch)
        gs = setup_mod.GraphSetup(
            MagicMock(), MagicMock(), {"market": MagicMock()}, ConditionalLogic()
        )
        gs.setup_graph(["market"])
        assert called.get("market") and not called.get("valuation")

    def test_pre_ipo_mode_uses_valuation_analyst(self, monkeypatch):
        called = _patch_analyst_factories(monkeypatch)
        gs = setup_mod.GraphSetup(
            MagicMock(),
            MagicMock(),
            {"market": MagicMock()},
            ConditionalLogic(),
            asset_type="pre_ipo",
        )
        gs.setup_graph(["market"])
        assert called.get("valuation") and not called.get("market")


@pytest.mark.unit
class TestTradingGraphPreIPOWiring:
    def test_market_tool_node_has_valuation_tool_in_pre_ipo(self, mock_llm_client):
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        from tradingagents.default_config import DEFAULT_CONFIG

        config = DEFAULT_CONFIG.copy()
        config["asset_type"] = "pre_ipo"
        ta = TradingAgentsGraph(selected_analysts=["market"], config=config)
        tool_names = {t.name for t in ta.tool_nodes["market"].tools_by_name.values()}
        assert "get_valuation" in tool_names

    def test_market_tool_node_has_price_tools_when_listed(self, mock_llm_client):
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        from tradingagents.default_config import DEFAULT_CONFIG

        config = DEFAULT_CONFIG.copy()
        ta = TradingAgentsGraph(selected_analysts=["market"], config=config)
        tool_names = {t.name for t in ta.tool_nodes["market"].tools_by_name.values()}
        assert "get_stock_data" in tool_names
        assert "get_valuation" not in tool_names
