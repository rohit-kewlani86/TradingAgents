"""Pre-IPO data adapters (the ``pre_ipo`` vendor implementations).

External services (funding API, web search) are key-gated: absent a key the
adapter returns informative text instead of raising, so the pipeline never
blocks. Where a key is present, HTTP is mocked.
"""

from unittest.mock import MagicMock, patch

import pytest

from tradingagents.dataflows import preipo


@pytest.mark.unit
class TestPreIPOFundamentals:
    def test_delegates_to_edgar_s1_summary(self):
        with patch.object(preipo.edgar, "get_s1_summary", return_value="EDGAR SAYS X") as m:
            out = preipo.get_fundamentals("SpaceX", "2026-01-15")
        m.assert_called_once_with("SpaceX")
        assert "EDGAR SAYS X" in out


@pytest.mark.unit
class TestPreIPOInsider:
    def test_not_applicable_message(self):
        out = preipo.get_insider_transactions("SpaceX")
        assert "not applicable" in out.lower()
        assert "SpaceX" in out


@pytest.mark.unit
class TestPreIPOValuation:
    def test_graceful_when_no_funding_key(self, monkeypatch):
        monkeypatch.delenv("CRUNCHBASE_API_KEY", raising=False)
        out = preipo.get_valuation("SpaceX", "2026-01-15")
        assert "SpaceX" in out
        assert "CRUNCHBASE_API_KEY" in out

    def test_uses_funding_api_when_key_present(self, monkeypatch):
        monkeypatch.setenv("CRUNCHBASE_API_KEY", "secret")
        fake = MagicMock()
        fake.json.return_value = {"properties": {"valuation": "USD 350B", "num_funding_rounds": 30}}
        fake.raise_for_status.return_value = None
        with patch.object(preipo.requests, "get", return_value=fake):
            out = preipo.get_valuation("SpaceX", "2026-01-15")
        assert "350B" in out


@pytest.mark.unit
class TestPreIPONews:
    def test_graceful_when_no_search_key(self, monkeypatch):
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)
        out = preipo.get_news("SpaceX", "2026-01-01", "2026-01-15")
        assert "SpaceX" in out
        assert "TAVILY_API_KEY" in out

    def test_uses_search_api_when_key_present(self, monkeypatch):
        monkeypatch.setenv("TAVILY_API_KEY", "secret")
        fake = MagicMock()
        fake.json.return_value = {"results": [{"title": "SpaceX nears IPO", "content": "details here"}]}
        fake.raise_for_status.return_value = None
        with patch.object(preipo.requests, "post", return_value=fake):
            out = preipo.get_news("SpaceX", "2026-01-01", "2026-01-15")
        assert "SpaceX nears IPO" in out
