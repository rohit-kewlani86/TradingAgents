"""Live model discovery: query the provider's /v1/models so retired models
never appear in the CLI picker or the fallback chain. Best-effort: any failure
(no key, network, non-OpenAI provider) degrades to an empty list."""

from unittest.mock import MagicMock, patch

import pytest

from tradingagents.llm_clients import live_models
from tradingagents.llm_clients.live_models import fetch_live_model_ids, get_live_model_ids


@pytest.fixture(autouse=True)
def _clear_cache():
    live_models._CACHE.clear()
    yield
    live_models._CACHE.clear()


@pytest.mark.unit
class TestFetchLiveModelIds:
    def test_parses_openai_style_model_list(self):
        resp = MagicMock()
        resp.json.return_value = {
            "data": [
                {"id": "meta/llama-3.3-70b-instruct"},
                {"id": "deepseek-ai/deepseek-r1"},
            ]
        }
        resp.raise_for_status.return_value = None
        with patch.object(live_models.requests, "get", return_value=resp) as get:
            ids = fetch_live_model_ids("https://integrate.api.nvidia.com/v1", "key")
        assert ids == ["meta/llama-3.3-70b-instruct", "deepseek-ai/deepseek-r1"]
        # queries the /models endpoint with a bearer token
        url = get.call_args[0][0]
        assert url.endswith("/models")
        assert get.call_args[1]["headers"]["Authorization"] == "Bearer key"

    def test_returns_empty_on_any_failure(self):
        with patch.object(live_models.requests, "get", side_effect=RuntimeError("boom")):
            assert fetch_live_model_ids("https://x/v1", "key") == []

    def test_returns_empty_without_key(self):
        assert fetch_live_model_ids("https://x/v1", None) == []

    def test_returns_empty_without_base_url(self):
        assert fetch_live_model_ids(None, "key") == []


@pytest.mark.unit
class TestGetLiveModelIds:
    def test_resolves_key_from_provider_env_and_caches(self, monkeypatch):
        monkeypatch.setenv("NVIDIA_API_KEY", "secret")
        calls = []

        def fake_fetch(base_url, api_key):
            calls.append((base_url, api_key))
            return ["a", "b"]

        with patch.object(live_models, "fetch_live_model_ids", side_effect=fake_fetch):
            first = get_live_model_ids("nvidia", "https://integrate.api.nvidia.com/v1")
            second = get_live_model_ids("nvidia", "https://integrate.api.nvidia.com/v1")

        assert first == ["a", "b"] == second
        assert len(calls) == 1  # cached: fetched once
        assert calls[0] == ("https://integrate.api.nvidia.com/v1", "secret")

    def test_empty_when_no_key_configured(self, monkeypatch):
        monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
        assert get_live_model_ids("nvidia", "https://integrate.api.nvidia.com/v1") == []

    def test_empty_when_no_base_url(self):
        assert get_live_model_ids("openai", None) == []


@pytest.mark.unit
class TestSelectableModelOptions:
    def test_shows_curated_live_and_drops_retired(self):
        from tradingagents.llm_clients.model_catalog import get_selectable_model_options

        # nvidia deep catalog includes deepseek-r1 + llama-3.1-405b + nemotron;
        # live list omits nemotron, so it must not appear.
        live = ["deepseek-ai/deepseek-r1", "meta/llama-3.1-405b-instruct"]
        with patch("tradingagents.llm_clients.model_catalog.get_live_model_ids", return_value=live):
            opts = get_selectable_model_options("nvidia", "deep", "https://x/v1")
        values = [v for _, v in opts]
        assert "deepseek-ai/deepseek-r1" in values
        assert "nvidia/llama-3.1-nemotron-70b-instruct" not in values
        assert values[-1] == "custom"  # custom fallback always last

    def test_raw_live_when_no_curated_survive(self):
        from tradingagents.llm_clients.model_catalog import get_selectable_model_options

        live = ["some/brand-new-model"]  # none of the curated IDs are live
        with patch("tradingagents.llm_clients.model_catalog.get_live_model_ids", return_value=live):
            opts = get_selectable_model_options("nvidia", "deep", "https://x/v1")
        values = [v for _, v in opts]
        assert values == ["some/brand-new-model", "custom"]

    def test_falls_back_to_hardcoded_catalog_when_no_live(self):
        from tradingagents.llm_clients.model_catalog import (
            get_model_options,
            get_selectable_model_options,
        )

        with patch("tradingagents.llm_clients.model_catalog.get_live_model_ids", return_value=[]):
            opts = get_selectable_model_options("nvidia", "deep", None)
        assert opts == get_model_options("nvidia", "deep")
