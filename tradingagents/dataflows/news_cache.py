"""Disk cache for news fetches, keyed by (subject, as-of date).

Mirrors the OHLCV disk-cache pattern in ``stockstats_utils.load_ohlcv``: one
JSON file per cache key under ``config["data_cache_dir"]``, so a rerun with
the same key is served from disk instead of the network.

News is the single biggest source of non-deterministic BUY/SELL/HOLD drift:
two runs for the same ticker and trade date, minutes apart, can see a
completely different "latest N" snapshot from the vendor and therefore reach
different bull/bear conclusions. Caching the raw vendor response per
(subject, as-of date) makes a rerun for the same inputs byte-identical and
avoids re-hitting the network.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from typing import Any

from .config import get_config
from .utils import safe_ticker_component

_NEWS_CACHE_SUBDIR = "news"
_KEY_PART_MAX_LEN = 64


def _cache_dir() -> str:
    config = get_config()
    news_dir = os.path.join(config["data_cache_dir"], _NEWS_CACHE_SUBDIR)
    os.makedirs(news_dir, exist_ok=True)
    return news_dir


def _cache_path(*key_parts: str) -> str:
    """Build a cache file path from sanitized key parts.

    Cache keys mix ticker symbols, query subjects, and dates — all of which
    can originate from LLM tool-call arguments — so each part is validated
    with the same path-traversal guard used for tickers elsewhere in the
    cache layer (``safe_ticker_component``).
    """
    safe_parts = [
        safe_ticker_component(str(part), max_len=_KEY_PART_MAX_LEN)
        for part in key_parts
    ]
    filename = "-".join(safe_parts) + ".json"
    return os.path.join(_cache_dir(), filename)


def get_or_fetch(key_parts: tuple[str, ...], fetch_fn: Callable[[], Any]) -> Any:
    """Return cached JSON data for ``key_parts``, calling ``fetch_fn`` only on a miss.

    A subsequent call with the same key parts is served from disk and never
    calls ``fetch_fn`` again, so a rerun for the same (subject, as-of date)
    returns byte-identical results. ``fetch_fn`` results must be JSON
    serializable; a failed fetch (an exception) is never cached.
    """
    path = _cache_path(*key_parts)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    data = fetch_fn()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return data
