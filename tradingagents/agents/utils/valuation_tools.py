from typing import Annotated

from langchain_core.tools import tool

from tradingagents.dataflows.interface import route_to_vendor


@tool
def get_valuation(
    company: Annotated[str, "company name, e.g. SpaceX"],
    curr_date: Annotated[str, "current date you are analysing at, yyyy-mm-dd"],
) -> str:
    """
    Retrieve pre-IPO valuation context for a private/IPO-ready company:
    latest private valuation, funding-round history, secondary-market marks,
    and comparable public-company multiples.
    Uses the configured valuation_data vendor (pre-IPO sources).
    Args:
        company (str): Company name, e.g. SpaceX
        curr_date (str): Current date you are analysing at, yyyy-mm-dd
    Returns:
        str: A formatted report of private valuation and funding history
    """
    return route_to_vendor("get_valuation", company, curr_date)
