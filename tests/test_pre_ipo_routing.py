"""Vendor routing honours pre-IPO mode (asset_type == "pre_ipo")."""

import pytest

from tradingagents.dataflows import interface
from tradingagents.dataflows.config import set_config


@pytest.fixture()
def reset_config():
    yield
    set_config({"asset_type": "stock"})


@pytest.mark.unit
class TestPreIPORouting:
    def test_listed_mode_uses_configured_vendor(self, reset_config):
        set_config({"asset_type": "stock", "data_vendors": {"fundamental_data": "yfinance"}})
        assert interface.get_vendor("fundamental_data", "get_fundamentals") == "yfinance"

    def test_pre_ipo_mode_forces_pre_ipo_vendor(self, reset_config):
        set_config({"asset_type": "pre_ipo", "data_vendors": {"fundamental_data": "yfinance"}})
        assert interface.get_vendor("fundamental_data", "get_fundamentals") == "pre_ipo"

    def test_valuation_method_resolves_to_its_category(self):
        assert interface.get_category_for_method("get_valuation") == "valuation_data"
