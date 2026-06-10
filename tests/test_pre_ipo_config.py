"""Config plumbing for pre-IPO company analysis mode."""

import pytest

from tradingagents.default_config import DEFAULT_CONFIG


@pytest.mark.unit
class TestPreIPOConfigDefaults:
    def test_company_mode_defaults_to_listed(self):
        assert DEFAULT_CONFIG["company_mode"] == "listed"

    def test_pre_ipo_company_defaults_to_none(self):
        assert DEFAULT_CONFIG["pre_ipo_company"] is None
