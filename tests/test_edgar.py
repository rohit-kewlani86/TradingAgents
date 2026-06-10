"""SEC EDGAR S-1/F-1 adapter. HTTP is mocked; no live network in tests."""

from unittest.mock import MagicMock, patch

import pytest

from tradingagents.dataflows import edgar


_FTS_WITH_HITS = {
    "hits": {
        "hits": [
            {
                "_id": "0001193125-24-000001:doc1.htm",
                "_source": {
                    "file_type": "S-1",
                    "file_date": "2024-11-01",
                    "display_names": ["Acme Rockets Inc.  (CIK 0001234567)"],
                },
            }
        ]
    }
}

_FTS_EMPTY = {"hits": {"hits": []}}


@pytest.mark.unit
class TestSearchS1Filings:
    def test_parses_filing_hits(self):
        with patch.object(edgar, "_fts_request", return_value=_FTS_WITH_HITS):
            filings = edgar.search_s1_filings("Acme Rockets")
        assert filings == [
            {
                "form": "S-1",
                "filed": "2024-11-01",
                "company": "Acme Rockets Inc.  (CIK 0001234567)",
                "accession": "0001193125-24-000001:doc1.htm",
            }
        ]

    def test_empty_when_no_hits(self):
        with patch.object(edgar, "_fts_request", return_value=_FTS_EMPTY):
            assert edgar.search_s1_filings("Nobody") == []


@pytest.mark.unit
class TestGetS1Summary:
    def test_reports_not_found_when_no_filings(self):
        with patch.object(edgar, "search_s1_filings", return_value=[]):
            summary = edgar.get_s1_summary("SpaceX")
        assert "No S-1/F-1" in summary
        assert "SpaceX" in summary

    def test_formats_found_filings(self):
        filings = [{"form": "S-1", "filed": "2024-11-01", "company": "Acme Rockets Inc.", "accession": "X"}]
        with patch.object(edgar, "search_s1_filings", return_value=filings):
            summary = edgar.get_s1_summary("Acme Rockets")
        assert "S-1" in summary
        assert "2024-11-01" in summary

    def test_degrades_gracefully_on_http_error(self):
        with patch.object(edgar, "search_s1_filings", side_effect=RuntimeError("boom")):
            summary = edgar.get_s1_summary("Acme Rockets")
        assert "EDGAR" in summary
        # never raises; returns informative text
        assert isinstance(summary, str)


@pytest.mark.unit
class TestFtsRequestBuildsRequest:
    def test_sends_user_agent_and_forms(self):
        fake_resp = MagicMock()
        fake_resp.json.return_value = _FTS_EMPTY
        fake_resp.raise_for_status.return_value = None
        with patch.object(edgar.requests, "get", return_value=fake_resp) as mock_get:
            edgar._fts_request("Acme Rockets", forms=("S-1", "F-1"))
        _, kwargs = mock_get.call_args
        assert "User-Agent" in kwargs["headers"]
        assert kwargs["params"]["forms"] == "S-1,F-1"
