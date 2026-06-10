"""SEC EDGAR adapter for pre-IPO registration statements (S-1 / F-1).

A company filing to go public lodges an S-1 (domestic) or F-1 (foreign) with
the SEC. This adapter queries EDGAR full-text search for those filings so the
pre-IPO analysts can cite real, audited disclosure when it exists. Companies
that have not filed yet (e.g. SpaceX) simply return "no filing found", which is
itself a meaningful signal for the analysts.

The SEC requires a descriptive User-Agent on every request; set
``SEC_EDGAR_USER_AGENT`` to your "name contact@email" per SEC fair-access rules.
"""

import os
from typing import List, Optional

import requests

EDGAR_FTS_URL = "https://efts.sec.gov/LATEST/search-index"
_DEFAULT_USER_AGENT = "TradingAgents research tradingagents@example.com"
_TIMEOUT = 15


def _user_agent() -> str:
    return os.getenv("SEC_EDGAR_USER_AGENT", _DEFAULT_USER_AGENT)


def _fts_request(company_name: str, forms=("S-1", "F-1")) -> dict:
    """Query EDGAR full-text search and return the raw JSON payload."""
    resp = requests.get(
        EDGAR_FTS_URL,
        params={"q": f'"{company_name}"', "forms": ",".join(forms)},
        headers={"User-Agent": _user_agent()},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def search_s1_filings(company_name: str, forms=("S-1", "F-1")) -> List[dict]:
    """Return registration-statement filings for ``company_name``.

    Each item: {form, filed, company, accession}. Empty list when none exist.
    """
    payload = _fts_request(company_name, forms=forms)
    hits = payload.get("hits", {}).get("hits", [])
    filings = []
    for hit in hits:
        src = hit.get("_source", {})
        names = src.get("display_names") or [""]
        filings.append(
            {
                "form": src.get("file_type") or src.get("form") or "?",
                "filed": src.get("file_date") or "?",
                "company": names[0],
                "accession": hit.get("_id", "?"),
            }
        )
    return filings


def get_s1_summary(company_name: str) -> str:
    """Human-readable summary of a company's registration filings.

    Never raises: network/parse failures and "no filing" both return
    informative prose so the agent always receives an explicit signal.
    """
    try:
        filings = search_s1_filings(company_name)
    except Exception as exc:  # network, parse, rate-limit
        return (
            f"EDGAR lookup for {company_name} could not be completed ({exc}). "
            "Proceed using funding-round and news data only."
        )

    if not filings:
        return (
            f"No S-1/F-1 registration statement found on SEC EDGAR for "
            f"{company_name}. The company has likely not filed to go public yet, "
            "so no audited public financials are available; rely on funding-round "
            "valuations, secondary-market marks, and news."
        )

    lines = [f"SEC EDGAR registration filings for {company_name}:"]
    for f in filings[:5]:
        lines.append(
            f"- {f['form']} filed {f['filed']} ({f['company']}) — accession {f['accession']}"
        )
    return "\n".join(lines)
