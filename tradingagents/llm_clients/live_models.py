"""Discover a provider's *currently available* models at runtime.

A hardcoded model catalog rots: models reach end-of-life and a stale entry then
breaks a run (a retired model returns HTTP 410). For OpenAI-compatible providers
(NVIDIA NIM, OpenAI, Groq, DeepSeek, ...) the ``GET {base_url}/models`` endpoint
lists exactly what the account can call right now, so we query it and show/keep
only live models.

Everything here is best-effort: no key, no base URL, a non-OpenAI provider, or
any network/parse error yields an empty list, so the caller cleanly falls back
to the hardcoded catalog or a Custom-ID prompt and the CLI never breaks.
"""

import logging
import os

import requests

from .api_key_env import PROVIDER_API_KEY_ENV

logger = logging.getLogger(__name__)

_TIMEOUT = 10
# Session cache keyed by (provider, base_url): models don't change mid-run, and
# both the CLI picker and the graph builder ask for the same list.
_CACHE: dict[tuple[str, str | None], list[str]] = {}


def fetch_live_model_ids(base_url: str | None, api_key: str | None) -> list[str]:
    """Return model IDs from an OpenAI-compatible ``/models`` endpoint.

    Best-effort: returns ``[]`` when the key or base URL is missing, or on any
    HTTP/parse error, so a discovery failure never breaks the caller.
    """
    if not base_url or not api_key:
        return []
    try:
        url = base_url.rstrip("/") + "/models"
        resp = requests.get(
            url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json().get("data", [])
    except Exception as exc:  # network, auth, parse — never fatal
        logger.warning("could not fetch live models from %s: %s", base_url, exc)
        return []

    return [item["id"] for item in data if isinstance(item, dict) and item.get("id")]


def get_live_model_ids(provider: str, base_url: str | None) -> list[str]:
    """Live model IDs for a provider, cached per session.

    Resolves the provider's API key from ``PROVIDER_API_KEY_ENV`` and queries
    ``base_url``. Returns ``[]`` for providers without a key/base URL (which
    includes non-OpenAI-compatible providers whose model lists live elsewhere),
    so callers degrade to the hardcoded catalog.
    """
    cache_key = (provider.lower(), base_url)
    if cache_key in _CACHE:
        return _CACHE[cache_key]

    env_var = PROVIDER_API_KEY_ENV.get(provider.lower())
    api_key = os.getenv(env_var) if env_var else None
    ids = fetch_live_model_ids(base_url, api_key)
    _CACHE[cache_key] = ids
    return ids
