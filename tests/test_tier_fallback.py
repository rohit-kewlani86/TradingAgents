"""Per-tier cross-model fallback: a failing model call falls through to the next
model in that tier's catalog; the run only breaks when every model fails."""

from unittest.mock import patch

import pytest
from langchain_core.messages import AIMessage
from langchain_core.runnables import Runnable

from tradingagents.llm_clients.fallback import FallbackLLM, build_tier_llm
from tradingagents.llm_clients.model_catalog import get_catalog_model_ids


class FakeModel:
    """Minimal stand-in for a LangChain chat model."""

    def __init__(self, name, fail=False):
        self.name = name
        self.fail = fail
        self.calls = 0
        self.bound_tools = None
        self.structured_schema = None

    def invoke(self, _input, config=None, **kwargs):
        self.calls += 1
        if self.fail:
            raise RuntimeError(f"{self.name} unavailable")
        return AIMessage(content=self.name)

    def bind_tools(self, tools, **kwargs):
        self.bound_tools = tools
        return self

    def with_structured_output(self, schema, **kwargs):
        self.structured_schema = schema
        return self


@pytest.mark.unit
class TestFallbackLLMInvoke:
    def test_is_a_runnable(self):
        # Must be a Runnable so `prompt | llm.bind_tools(...)` composes.
        assert isinstance(FallbackLLM([FakeModel("a")]), Runnable)

    def test_primary_success_does_not_call_fallback(self):
        primary, backup = FakeModel("primary"), FakeModel("backup")
        out = FallbackLLM([primary, backup]).invoke("hi")
        assert out.content == "primary"
        assert backup.calls == 0

    def test_falls_back_to_next_model_on_failure(self):
        primary, backup = FakeModel("primary", fail=True), FakeModel("backup")
        out = FallbackLLM([primary, backup]).invoke("hi")
        assert out.content == "backup"
        assert primary.calls == 1 and backup.calls == 1

    def test_walks_the_whole_chain(self):
        m1, m2, m3 = FakeModel("m1", fail=True), FakeModel("m2", fail=True), FakeModel("m3")
        out = FallbackLLM([m1, m2, m3]).invoke("hi")
        assert out.content == "m3"

    def test_raises_only_when_all_models_fail(self):
        models = [FakeModel("m1", fail=True), FakeModel("m2", fail=True)]
        with pytest.raises(RuntimeError):
            FallbackLLM(models).invoke("hi")


@pytest.mark.unit
class TestFallbackLLMComposition:
    def test_bind_tools_applies_to_every_model(self):
        m1, m2 = FakeModel("m1"), FakeModel("m2")
        bound = FallbackLLM([m1, m2]).bind_tools(["tool"])
        assert isinstance(bound, FallbackLLM)
        assert m1.bound_tools == ["tool"] and m2.bound_tools == ["tool"]

    def test_with_structured_output_applies_to_every_model(self):
        m1, m2 = FakeModel("m1"), FakeModel("m2")
        structured = FallbackLLM([m1, m2]).with_structured_output(dict)
        assert isinstance(structured, FallbackLLM)
        assert m1.structured_schema is dict and m2.structured_schema is dict

    def test_with_structured_output_skips_unsupported_models(self):
        class NoStructured(FakeModel):
            def with_structured_output(self, schema, **kwargs):
                raise NotImplementedError

        supported = FakeModel("ok")
        structured = FallbackLLM([NoStructured("no"), supported]).with_structured_output(dict)
        assert structured.invoke("hi").content == "ok"

    def test_with_structured_output_raises_when_none_supported(self):
        class NoStructured(FakeModel):
            def with_structured_output(self, schema, **kwargs):
                raise NotImplementedError

        with pytest.raises(NotImplementedError):
            FallbackLLM([NoStructured("a"), NoStructured("b")]).with_structured_output(dict)


@pytest.mark.unit
class TestBuildTierLLM:
    def test_selected_model_first_then_catalog_fallbacks(self):
        created = []

        def fake_create(provider, model, base_url=None, **kwargs):
            created.append(model)

            class C:
                def get_llm(self_inner):
                    return FakeModel(model)

            return C()

        with patch("tradingagents.llm_clients.fallback.create_llm_client", fake_create), \
             patch(
                 "tradingagents.llm_clients.fallback.get_catalog_model_ids",
                 return_value=["m-a", "m-b", "m-c"],
             ):
            build_tier_llm("openai", "m-b", "deep", None, {})

        # selected model first, no duplicates, other catalog models after
        assert created[0] == "m-b"
        assert set(created) == {"m-a", "m-b", "m-c"}
        assert len(created) == 3


@pytest.mark.unit
class TestCatalogModelIds:
    def test_excludes_custom_sentinel(self):
        ids = get_catalog_model_ids("nvidia", "deep")
        assert "custom" not in ids
        assert "deepseek-ai/deepseek-r1" in ids

    def test_unknown_provider_returns_empty(self):
        assert get_catalog_model_ids("does-not-exist", "deep") == []
