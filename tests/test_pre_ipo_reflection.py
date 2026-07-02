"""Pre-IPO decisions stay pending until the company lists, then resolve."""

from unittest.mock import MagicMock, patch

import pytest

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph


def _graph(config):
    return TradingAgentsGraph(selected_analysts=["market"], config=config)


@pytest.mark.unit
class TestResolutionSymbol:
    def test_listed_mode_resolves_against_the_ticker(self, mock_llm_client):
        ta = _graph(DEFAULT_CONFIG.copy())
        assert ta._resolution_symbol("NVDA") == "NVDA"

    def test_pre_ipo_without_listed_ticker_returns_none(self, mock_llm_client):
        config = DEFAULT_CONFIG.copy()
        config["asset_type"] = "pre_ipo"
        config["pre_ipo_company"] = {"name": "SpaceX"}
        ta = _graph(config)
        assert ta._resolution_symbol("SpaceX") is None

    def test_pre_ipo_with_listed_ticker_resolves_against_it(self, mock_llm_client):
        config = DEFAULT_CONFIG.copy()
        config["asset_type"] = "pre_ipo"
        config["pre_ipo_company"] = {"name": "SpaceX", "listed_ticker": "SPCX"}
        ta = _graph(config)
        assert ta._resolution_symbol("SpaceX") == "SPCX"


@pytest.mark.unit
class TestResolvePendingSkips:
    def test_pre_ipo_unlisted_skips_return_fetch(self, mock_llm_client):
        config = DEFAULT_CONFIG.copy()
        config["asset_type"] = "pre_ipo"
        config["pre_ipo_company"] = {"name": "SpaceX"}
        ta = _graph(config)
        ta.memory_log.get_pending_entries = MagicMock(
            return_value=[{"ticker": "SpaceX", "date": "2026-01-15", "decision": "Subscribe"}]
        )
        with patch.object(ta, "_fetch_returns") as fetch:
            ta._resolve_pending_entries("SpaceX")
        fetch.assert_not_called()

    def test_pre_ipo_listed_fetches_against_listed_ticker(self, mock_llm_client):
        config = DEFAULT_CONFIG.copy()
        config["asset_type"] = "pre_ipo"
        config["pre_ipo_company"] = {"name": "SpaceX", "listed_ticker": "SPCX"}
        ta = _graph(config)
        ta.memory_log.get_pending_entries = MagicMock(
            return_value=[{"ticker": "SpaceX", "date": "2026-01-15", "decision": "Subscribe"}]
        )
        with patch.object(ta, "_fetch_returns", return_value=(None, None, None)) as fetch:
            ta._resolve_pending_entries("SpaceX")
        fetch.assert_called_once()
        assert fetch.call_args[0][0] == "SPCX"
