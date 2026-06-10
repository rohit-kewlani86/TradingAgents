"""End-to-end vendor dispatch into the pre-IPO adapters + the valuation tool."""

from unittest.mock import patch

import pytest

from tradingagents.dataflows import interface
from tradingagents.dataflows.config import set_config


@pytest.fixture()
def pre_ipo_mode():
    set_config({"company_mode": "pre_ipo"})
    yield
    set_config({"company_mode": "listed"})


@pytest.mark.unit
class TestPreIPODispatch:
    def test_fundamentals_route_to_preipo_adapter(self, pre_ipo_mode):
        # Patch the deepest seam (EDGAR) so we observe real routing through
        # the pre_ipo fundamentals adapter without hitting the network.
        with patch(
            "tradingagents.dataflows.edgar.get_s1_summary", return_value="EDGAR-S1-TEXT"
        ):
            out = interface.route_to_vendor("get_fundamentals", "SpaceX", "2026-01-15")
        assert "EDGAR-S1-TEXT" in out

    def test_valuation_routes_to_preipo_adapter(self, pre_ipo_mode, monkeypatch):
        # No funding key → the pre_ipo valuation adapter returns its graceful
        # message, proving the call reached that adapter.
        monkeypatch.delenv("CRUNCHBASE_API_KEY", raising=False)
        out = interface.route_to_vendor("get_valuation", "SpaceX", "2026-01-15")
        assert "CRUNCHBASE_API_KEY" in out
        assert "SpaceX" in out


@pytest.mark.unit
class TestValuationTool:
    def test_tool_wrapper_routes_through_interface(self):
        from tradingagents.agents.utils.valuation_tools import get_valuation

        with patch(
            "tradingagents.agents.utils.valuation_tools.route_to_vendor",
            return_value="ROUTED",
        ) as m:
            out = get_valuation.invoke({"company": "SpaceX", "curr_date": "2026-01-15"})
        assert out == "ROUTED"
        m.assert_called_once_with("get_valuation", "SpaceX", "2026-01-15")
