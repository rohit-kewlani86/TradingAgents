"""Per-tier cross-model fallback for LLM calls.

Each tier (deep / quick) is normally a single model. If that model's API call
fails (rate limit, outage, model retired, transport error), the whole run
breaks. ``FallbackLLM`` wraps the tier's catalog models in priority order and
retries the *next* model on any failure, so a run only breaks when every model
in that tier's catalog is failing.

It is a ``Runnable`` (so ``prompt | llm.bind_tools(...)`` still composes) and
forwards ``bind_tools`` / ``with_structured_output`` to every wrapped model, so
the fallback survives tool-binding and structured-output binding — exactly the
shapes the agents use.
"""

import logging
from typing import Any

from langchain_core.runnables import Runnable

from .factory import create_llm_client
from .live_models import get_live_model_ids
from .model_catalog import get_catalog_model_ids

logger = logging.getLogger(__name__)


class FallbackLLM(Runnable):
    """Ordered list of chat models tried in turn until one succeeds."""

    def __init__(self, models: list[Any]):
        if not models:
            raise ValueError("FallbackLLM requires at least one model")
        self._models = list(models)

    def bind_tools(self, *args, **kwargs) -> "FallbackLLM":
        """Bind the same tools to every model, preserving the fallback chain."""
        return FallbackLLM([m.bind_tools(*args, **kwargs) for m in self._models])

    def with_structured_output(self, *args, **kwargs) -> "FallbackLLM":
        """Bind structured output on every model that supports it.

        Models that cannot do structured output are dropped from the chain
        rather than aborting it. If none support it, raise ``NotImplementedError``
        so callers (``bind_structured``) fall back to free-text — the existing
        behaviour for a single unsupported model.
        """
        structured = []
        for model in self._models:
            try:
                structured.append(model.with_structured_output(*args, **kwargs))
            except (NotImplementedError, AttributeError) as exc:
                logger.warning(
                    "tier model %r has no structured-output support (%s); "
                    "excluding it from the structured fallback chain",
                    getattr(model, "model_name", model),
                    exc,
                )
        if not structured:
            raise NotImplementedError(
                "no model in this tier supports with_structured_output"
            )
        return FallbackLLM(structured)

    def invoke(self, input: Any, config=None, **kwargs) -> Any:
        """Try each model in order; return the first success.

        Any exception from a model call triggers a fall-through to the next
        model. Only when every model fails is the last error re-raised.
        """
        failures: list[tuple[str, Exception]] = []
        total = len(self._models)
        for index, model in enumerate(self._models, start=1):
            try:
                return model.invoke(input, config=config, **kwargs)
            except Exception as exc:  # any failure → next model
                name = (
                    getattr(model, "model_name", None)
                    or getattr(model, "model", None)
                    or getattr(model, "name", None)
                    or f"model#{index}"
                )
                failures.append((str(name), exc))
                logger.warning(
                    "tier model %d/%d (%s) failed (%s); falling back to the next model",
                    index,
                    total,
                    name,
                    exc,
                )
        # Every model failed. Surface all causes so the primary model's real
        # error is never masked by whichever model happened to be tried last.
        detail = "; ".join(f"{name}: {type(exc).__name__}: {exc}" for name, exc in failures)
        raise RuntimeError(
            f"all {total} model(s) in this tier failed — {detail}"
        ) from failures[-1][1]

    def __getattr__(self, name: str) -> Any:
        # Delegate unknown attribute reads (e.g. model_name) to the primary
        # model. Guard _models to avoid recursion before __init__ completes.
        if name == "_models":
            raise AttributeError(name)
        return getattr(self._models[0], name)


def build_tier_llm(
    provider: str,
    model: str,
    mode: str,
    base_url: str | None,
    client_kwargs: dict,
) -> FallbackLLM:
    """Build a ``FallbackLLM`` for one tier.

    The selected ``model`` is tried first, followed by the other models in that
    provider's catalog for ``mode`` (deep/quick), so a failed call falls through
    to the next available model. A model whose client can't even be constructed
    is skipped. All models share the same ``client_kwargs`` (per-tier
    temperature, max_tokens, callbacks, etc.).
    """
    # Restrict fallbacks to models the provider currently serves, so a retired
    # catalog entry (e.g. an EOL model returning HTTP 410) can never enter the
    # chain. When live discovery is unavailable, keep the full catalog.
    live = set(get_live_model_ids(provider, base_url))
    ordered_ids = [model]
    for catalog_id in get_catalog_model_ids(provider, mode):
        if catalog_id in ordered_ids:
            continue
        if live and catalog_id not in live:
            continue
        ordered_ids.append(catalog_id)

    models: list[Any] = []
    for model_id in ordered_ids:
        try:
            client = create_llm_client(provider, model_id, base_url, **client_kwargs)
            models.append(client.get_llm())
        except Exception as exc:
            logger.warning(
                "could not build tier model %r for provider %r: %s",
                model_id,
                provider,
                exc,
            )

    if not models:
        # No fallback could be built — surface the selected model's own error.
        client = create_llm_client(provider, model, base_url, **client_kwargs)
        models = [client.get_llm()]

    return FallbackLLM(models)
