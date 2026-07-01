"""Config plumbing for pre-IPO company analysis mode.

Pre-IPO mode is signalled by ``asset_type == "pre_ipo"`` (reusing the existing
asset-type dimension), so there is no separate ``company_mode`` flag. The only
new config is ``pre_ipo_company``, which carries the name + optional listed
ticker that a bare ticker string cannot.
"""

import pytest

from tradingagents.default_config import DEFAULT_CONFIG


@pytest.mark.unit
class TestPreIPOConfigDefaults:
    def test_pre_ipo_company_defaults_to_none(self):
        assert DEFAULT_CONFIG["pre_ipo_company"] is None
