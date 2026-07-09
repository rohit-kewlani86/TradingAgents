"""Tests for the configurable sampling temperature (#178/#168).

Temperature is a cross-provider knob: when set it must reach the underlying
chat client; when unset the provider keeps its own default.
"""

import importlib

import pytest

from tradingagents.llm_clients.factory import create_llm_client


@pytest.mark.unit
class TestTemperatureForwarding:
    @pytest.mark.parametrize(
        "provider,model",
        [
            ("openai", "gpt-4.1"),
            ("anthropic", "claude-sonnet-4-6"),
            ("google", "gemini-2.5-flash"),
            ("deepseek", "deepseek-chat"),
        ],
    )
    def test_temperature_reaches_client_when_set(self, provider, model):
        llm = create_llm_client(
            provider=provider, model=model, temperature=0.0, api_key="placeholder"
        ).get_llm()
        assert llm.temperature == 0.0

    def test_temperature_omitted_leaves_provider_default(self):
        # Not passing temperature must not force it to a value.
        llm = create_llm_client(
            provider="openai", model="gpt-4.1", api_key="placeholder"
        ).get_llm()
        # langchain's default is unset/None, not 0.0
        assert llm.temperature is None


@pytest.mark.unit
class TestTemperatureEnvOverlay:
    def test_env_sets_temperature(self, monkeypatch):
        import tradingagents.default_config as dc
        monkeypatch.setenv("TRADINGAGENTS_TEMPERATURE", "0.2")
        importlib.reload(dc)
        # Stored on config (string from env is fine; consumed via float()).
        assert dc.DEFAULT_CONFIG["temperature"] in ("0.2", 0.2)
        assert float(dc.DEFAULT_CONFIG["temperature"]) == 0.2
        monkeypatch.delenv("TRADINGAGENTS_TEMPERATURE", raising=False)
        importlib.reload(dc)

    def test_default_temperature_is_none(self, monkeypatch):
        import tradingagents.default_config as dc
        monkeypatch.delenv("TRADINGAGENTS_TEMPERATURE", raising=False)
        importlib.reload(dc)
        assert dc.DEFAULT_CONFIG["temperature"] is None


@pytest.mark.unit
class TestProviderKwargsTemperature:
    """_get_provider_kwargs float-coerces and forwards temperature, or omits it."""

    def _kwargs_for(self, temperature):
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        # Call the method without constructing the full graph.
        graph = TradingAgentsGraph.__new__(TradingAgentsGraph)
        graph.config = {"llm_provider": "openai", "temperature": temperature}
        return TradingAgentsGraph._get_provider_kwargs(graph)

    def test_float_string_coerced(self):
        assert self._kwargs_for("0.3")["temperature"] == 0.3

    def test_float_passthrough(self):
        assert self._kwargs_for(0.0)["temperature"] == 0.0

    def test_none_omitted(self):
        assert "temperature" not in self._kwargs_for(None)

    def test_empty_string_omitted(self):
        assert "temperature" not in self._kwargs_for("")


@pytest.mark.unit
class TestPerTierTemperature:
    """Per-tier temperature: deterministic deep-tier judges (0.0) and
    lower-variance quick-tier analysts (0.3), each falling back to the global
    ``temperature`` when its per-tier key is unset."""

    def _kwargs_for(self, tier, config):
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        graph = TradingAgentsGraph.__new__(TradingAgentsGraph)
        graph.config = {"llm_provider": "openai", **config}
        return TradingAgentsGraph._get_provider_kwargs(graph, tier)

    def test_default_config_has_per_tier_temperatures(self):
        from tradingagents.default_config import DEFAULT_CONFIG
        assert DEFAULT_CONFIG["deep_think_temperature"] == 0.0
        # Both tiers default to 0.0 for reproducibility (sampling variance was a
        # source of run-to-run drift). The mechanism still forwards any value.
        assert DEFAULT_CONFIG["quick_think_temperature"] == 0.0

    def test_deep_tier_uses_deep_temperature(self):
        cfg = {"deep_think_temperature": 0.0, "quick_think_temperature": 0.3}
        assert self._kwargs_for("deep", cfg)["temperature"] == 0.0

    def test_quick_tier_uses_quick_temperature(self):
        cfg = {"deep_think_temperature": 0.0, "quick_think_temperature": 0.3}
        assert self._kwargs_for("quick", cfg)["temperature"] == 0.3

    def test_per_tier_falls_back_to_global_temperature(self):
        cfg = {"temperature": 0.5}  # no per-tier keys
        assert self._kwargs_for("deep", cfg)["temperature"] == 0.5
        assert self._kwargs_for("quick", cfg)["temperature"] == 0.5

    def test_no_tier_arg_preserves_global_behaviour(self):
        # Back-compat: calling without a tier still forwards the global value.
        cfg = {"temperature": 0.2}
        assert self._kwargs_for(None, cfg)["temperature"] == 0.2


@pytest.mark.unit
class TestDebateRoundDefaults:
    def test_default_debate_rounds_is_two(self):
        from tradingagents.default_config import DEFAULT_CONFIG
        assert DEFAULT_CONFIG["max_debate_rounds"] == 2

    def test_default_risk_rounds_is_two(self):
        from tradingagents.default_config import DEFAULT_CONFIG
        assert DEFAULT_CONFIG["max_risk_discuss_rounds"] == 2
