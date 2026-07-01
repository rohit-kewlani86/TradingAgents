"""Per-tier max output-token cap.

Bounds a runaway generation (one analyst can otherwise spiral into a very large
response that dominates wall-clock) without touching the deep judges. The cap is
per tier (``deep_think_max_tokens`` / ``quick_think_max_tokens``) and maps to the
provider-native kwarg (``max_output_tokens`` for Google, ``max_tokens`` else).
"""

import pytest

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph


def _kwargs_for(tier, config, provider="openai"):
    graph = TradingAgentsGraph.__new__(TradingAgentsGraph)
    graph.config = {"llm_provider": provider, **config}
    return TradingAgentsGraph._get_provider_kwargs(graph, tier)


@pytest.mark.unit
class TestMaxOutputTokens:
    def test_default_config_has_per_tier_max_tokens_none(self):
        assert DEFAULT_CONFIG["deep_think_max_tokens"] is None
        assert DEFAULT_CONFIG["quick_think_max_tokens"] is None

    def test_deep_tier_forwards_deep_max_tokens(self):
        cfg = {"deep_think_max_tokens": 8000, "quick_think_max_tokens": 2000}
        assert _kwargs_for("deep", cfg)["max_tokens"] == 8000

    def test_quick_tier_forwards_quick_max_tokens(self):
        cfg = {"deep_think_max_tokens": 8000, "quick_think_max_tokens": 2000}
        assert _kwargs_for("quick", cfg)["max_tokens"] == 2000

    def test_google_uses_max_output_tokens(self):
        cfg = {"deep_think_max_tokens": 8000}
        kwargs = _kwargs_for("deep", cfg, provider="google")
        assert kwargs["max_output_tokens"] == 8000
        assert "max_tokens" not in kwargs

    def test_none_is_omitted(self):
        cfg = {"deep_think_max_tokens": None, "quick_think_max_tokens": None}
        assert "max_tokens" not in _kwargs_for("deep", cfg)
        assert "max_tokens" not in _kwargs_for("quick", cfg)
