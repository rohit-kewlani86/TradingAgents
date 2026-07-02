"""NVIDIA NIM models are offered as a curated CLI list, not just Custom ID."""

import pytest

from tradingagents.llm_clients.model_catalog import (
    get_known_models,
    get_model_options,
)


@pytest.mark.unit
class TestNvidiaCatalog:
    def test_deep_tier_lists_flagship_models(self):
        values = {value for _, value in get_model_options("nvidia", "deep")}
        assert "deepseek-ai/deepseek-r1" in values
        assert "meta/llama-3.1-405b-instruct" in values

    def test_quick_tier_lists_fast_models(self):
        values = {value for _, value in get_model_options("nvidia", "quick")}
        assert "meta/llama-3.3-70b-instruct" in values
        assert "meta/llama-3.1-8b-instruct" in values

    def test_custom_id_still_available(self):
        for mode in ("quick", "deep"):
            values = {value for _, value in get_model_options("nvidia", mode)}
            assert "custom" in values

    def test_more_than_just_custom(self):
        for mode in ("quick", "deep"):
            options = get_model_options("nvidia", mode)
            assert len(options) > 1  # curated models + custom, not custom-only

    def test_nvidia_ids_are_known_models(self):
        known = get_known_models()["nvidia"]
        assert "deepseek-ai/deepseek-r1" in known
        assert "meta/llama-3.3-70b-instruct" in known
