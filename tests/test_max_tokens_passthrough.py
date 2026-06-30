import pytest

from tradingagents.llm_clients.google_client import GoogleClient
from tradingagents.llm_clients.openai_client import OpenAIClient


@pytest.mark.unit
def test_google_forwards_max_output_tokens():
    llm = GoogleClient(
        "gemini-2.5-flash", api_key="x", max_output_tokens=8192
    ).get_llm()
    assert llm.max_output_tokens == 8192


@pytest.mark.unit
def test_openai_forwards_max_tokens():
    llm = OpenAIClient(
        "gpt-4.1", provider="openai", api_key="x", max_tokens=4096
    ).get_llm()
    assert llm.max_tokens == 4096
