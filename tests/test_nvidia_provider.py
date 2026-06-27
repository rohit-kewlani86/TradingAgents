from unittest.mock import patch

import pytest

from tradingagents.llm_clients.factory import create_llm_client
from tradingagents.llm_clients.model_catalog import get_known_models, get_model_options
from tradingagents.llm_clients.openai_client import OpenAIClient


@pytest.mark.unit
def test_factory_returns_openai_client_for_nvidia():
    client = create_llm_client("nvidia", "meta/llama-3.3-70b-instruct")

    assert isinstance(client, OpenAIClient)
    assert client.provider == "nvidia"


@pytest.mark.unit
def test_get_llm_resolves_nvidia_base_url_and_api_key(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "nvidia-test-key")

    with patch(
        "tradingagents.llm_clients.openai_client.NormalizedChatOpenAI"
    ) as mock_chat:
        OpenAIClient("meta/llama-3.3-70b-instruct", provider="nvidia").get_llm()

    call_kwargs = mock_chat.call_args[1]
    assert call_kwargs["base_url"] == "https://integrate.api.nvidia.com/v1"
    assert call_kwargs["api_key"] == "nvidia-test-key"


@pytest.mark.unit
def test_catalog_includes_nvidia_models():
    nvidia_models = get_known_models()["nvidia"]

    assert "meta/llama-3.3-70b-instruct" in nvidia_models
    assert "deepseek-ai/deepseek-r1" in nvidia_models
    assert "custom" in nvidia_models


@pytest.mark.unit
def test_catalog_exposes_nvidia_quick_and_deep_options():
    assert get_model_options("nvidia", "quick")
    assert get_model_options("nvidia", "deep")


@pytest.mark.unit
def test_get_llm_raises_clear_error_when_nvidia_key_missing(monkeypatch):
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)

    with pytest.raises(ValueError, match="NVIDIA_API_KEY"):
        OpenAIClient("meta/llama-3.3-70b-instruct", provider="nvidia").get_llm()
