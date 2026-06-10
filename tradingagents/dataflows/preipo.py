"""Pre-IPO data adapters — the ``pre_ipo`` vendor implementations.

These mirror the public-equity vendor function signatures so they slot into
``route_to_vendor`` unchanged, but source data appropriate to a company that
is not yet listed:

- fundamentals      → SEC EDGAR S-1/F-1 registration statements (see ``edgar``)
- valuation         → funding-round / secondary-market data (Crunchbase-style API)
- news / sentiment  → web search (Tavily-style API)
- insider txns      → not applicable before listing

The two external services are key-gated. When the key is absent the adapter
returns informative text rather than raising, so the analysts always receive an
explicit signal and the pipeline never blocks.
"""

import os

import requests

from tradingagents.dataflows import edgar

_TIMEOUT = 20
_CRUNCHBASE_ORG_URL = "https://api.crunchbase.com/api/v4/entities/organizations"
_TAVILY_SEARCH_URL = "https://api.tavily.com/search"


# --- Fundamentals (EDGAR S-1/F-1) ---

def get_fundamentals(company: str, curr_date: str = None) -> str:
    """Pre-IPO fundamentals: registration-statement disclosure from EDGAR."""
    return get_s1_financials(company, curr_date)


def get_s1_financials(company: str, curr_date: str = None) -> str:
    summary = edgar.get_s1_summary(company)
    return (
        f"Pre-IPO fundamentals for {company} (as of {curr_date or 'latest'}):\n\n"
        f"{summary}"
    )


def get_balance_sheet(company: str, freq: str = "annual", curr_date: str = None) -> str:
    return get_s1_financials(company, curr_date)


def get_cashflow(company: str, freq: str = "annual", curr_date: str = None) -> str:
    return get_s1_financials(company, curr_date)


def get_income_statement(company: str, freq: str = "annual", curr_date: str = None) -> str:
    return get_s1_financials(company, curr_date)


# --- Insider transactions (not applicable pre-IPO) ---

def get_insider_transactions(company: str) -> str:
    return (
        f"Insider-transaction data is not applicable for {company}: as a pre-IPO "
        "company it has no SEC-reportable insider trades. Founder/employee equity "
        "and secondary-sale activity, if relevant, appear in funding and news data."
    )


# --- Valuation (funding-round / secondary-market data) ---

def get_valuation(company: str, curr_date: str = None) -> str:
    """Latest private valuation and funding history from a funding-data API."""
    api_key = os.getenv("CRUNCHBASE_API_KEY")
    if not api_key:
        return (
            f"No funding-data source configured for {company}: set CRUNCHBASE_API_KEY "
            "to retrieve private valuation, funding rounds, and secondary marks. "
            "Falling back to news-derived valuation signals only."
        )
    try:
        resp = requests.get(
            f"{_CRUNCHBASE_ORG_URL}/{company}",
            params={"user_key": api_key},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        props = resp.json().get("properties", {})
    except Exception as exc:
        return (
            f"Funding-data lookup for {company} could not be completed ({exc}). "
            "Falling back to news-derived valuation signals only."
        )

    valuation = props.get("valuation", "unknown")
    rounds = props.get("num_funding_rounds", "unknown")
    return (
        f"Private valuation for {company} (as of {curr_date or 'latest'}):\n"
        f"- Latest valuation: {valuation}\n"
        f"- Funding rounds to date: {rounds}"
    )


# --- News / sentiment (web search) ---

def get_news(company: str, start_date: str = None, end_date: str = None) -> str:
    """Recent news for a pre-IPO company via a web-search API."""
    return _web_search(company, f"{company} IPO funding news", start_date, end_date)


def get_global_news(curr_date: str = None, look_back_days: int = 7, limit: int = 5) -> str:
    return _web_search(
        "markets",
        "IPO market conditions and macro outlook",
        None,
        curr_date,
        limit=limit,
    )


def _web_search(subject: str, query: str, start_date, end_date, limit: int = 5) -> str:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return (
            f"No web-search source configured for {subject}: set TAVILY_API_KEY to "
            "retrieve recent news and sentiment for pre-IPO companies."
        )
    try:
        resp = requests.post(
            _TAVILY_SEARCH_URL,
            json={"api_key": api_key, "query": query, "max_results": limit},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
    except Exception as exc:
        return f"Web-search lookup for {subject} could not be completed ({exc})."

    if not results:
        return f"No recent web results found for {subject}."
    lines = [f"Recent web results for {subject}:"]
    for r in results[:limit]:
        lines.append(f"- {r.get('title', 'untitled')}: {r.get('content', '')}")
    return "\n".join(lines)
