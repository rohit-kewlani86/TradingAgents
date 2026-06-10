"""CLI maps pre-IPO selections into config (pure mapping; prompt is thin)."""

import pytest

from cli.utils import build_company_mode_config


@pytest.mark.unit
class TestBuildCompanyModeConfig:
    def test_listed_mode(self):
        cfg = build_company_mode_config(is_pre_ipo=False, company_name="NVDA", listed_ticker="")
        assert cfg == {"company_mode": "listed", "pre_ipo_company": None}

    def test_pre_ipo_without_listed_ticker(self):
        cfg = build_company_mode_config(is_pre_ipo=True, company_name="SpaceX", listed_ticker="")
        assert cfg == {
            "company_mode": "pre_ipo",
            "pre_ipo_company": {"name": "SpaceX", "listed_ticker": None},
        }

    def test_pre_ipo_with_listed_ticker(self):
        cfg = build_company_mode_config(is_pre_ipo=True, company_name="SpaceX", listed_ticker="SPCX")
        assert cfg == {
            "company_mode": "pre_ipo",
            "pre_ipo_company": {"name": "SpaceX", "listed_ticker": "SPCX"},
        }
