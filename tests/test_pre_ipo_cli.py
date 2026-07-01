"""CLI maps pre-IPO selections into config (pure mapping; prompt is thin)."""

from unittest.mock import patch

import pytest

from cli.models import AnalystType, AssetType
from cli.utils import (
    build_pre_ipo_config,
    filter_analysts_for_asset_type,
    is_listed_security,
)


@pytest.mark.unit
class TestBuildPreIPOConfig:
    def test_listed_mode(self):
        cfg = build_pre_ipo_config(is_pre_ipo=False, company_name="NVDA", listed_ticker="")
        assert cfg == {"asset_type": "stock", "pre_ipo_company": None}

    def test_pre_ipo_without_listed_ticker(self):
        cfg = build_pre_ipo_config(is_pre_ipo=True, company_name="SpaceX", listed_ticker="")
        assert cfg == {
            "asset_type": "pre_ipo",
            "pre_ipo_company": {"name": "SpaceX", "listed_ticker": None},
        }

    def test_pre_ipo_with_listed_ticker(self):
        cfg = build_pre_ipo_config(is_pre_ipo=True, company_name="SpaceX", listed_ticker="SPCX")
        assert cfg == {
            "asset_type": "pre_ipo",
            "pre_ipo_company": {"name": "SpaceX", "listed_ticker": "SPCX"},
        }


@pytest.mark.unit
class TestIsListedSecurity:
    def test_resolves_means_listed(self):
        with patch(
            "cli.utils.resolve_instrument_identity",
            return_value={"company_name": "Apple Inc.", "exchange": "NMS"},
        ):
            assert is_listed_security("AAPL") is True

    def test_empty_resolution_means_not_listed(self):
        with patch("cli.utils.resolve_instrument_identity", return_value={}):
            assert is_listed_security("SPACEX") is False

    def test_resolution_error_treated_as_not_listed(self):
        with patch(
            "cli.utils.resolve_instrument_identity", side_effect=RuntimeError("boom")
        ):
            assert is_listed_security("SPACEX") is False


@pytest.mark.unit
class TestFilterAnalystsPreIPO:
    def test_pre_ipo_drops_technical_analyst(self):
        allowed = filter_analysts_for_asset_type(
            [AnalystType.MARKET, AnalystType.TECHNICAL, AnalystType.NEWS],
            AssetType.PRE_IPO,
        )
        assert AnalystType.TECHNICAL not in allowed
        assert AnalystType.MARKET in allowed
