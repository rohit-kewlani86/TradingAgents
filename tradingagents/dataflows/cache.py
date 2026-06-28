"""Per-call disk cache for slow, string-returning dataflow fetchers.

Parallel analysts issue many concurrent yfinance calls; each retry sleeps
seconds on rate limits. Caching a fetcher's output by its arguments cuts
repeated slow I/O within a run (two analysts asking for the same news) and
across re-runs of the same (ticker, date).

The cache key hashes the function name and arguments, so the ticker never
becomes a filesystem path component (no traversal risk). Only successful,
non-empty results are stored, so transient failures are never persisted.
"""

import functools
import hashlib
import os

from .config import get_config


def _cache_key(args, kwargs) -> str:
    raw = repr(args) + repr(sorted(kwargs.items()))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _cache_path(func_name: str, key: str) -> str:
    cache_dir = os.path.join(get_config()["data_cache_dir"], "tools")
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, f"{func_name}-{key}.txt")


def _is_cacheable(result) -> bool:
    return (
        isinstance(result, str)
        and bool(result.strip())
        and not result.lstrip().startswith("Error")
    )


def disk_cache(func):
    """Cache a string-returning fetcher's output on disk, keyed by its args."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        path = _cache_path(func.__name__, _cache_key(args, kwargs))
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return f.read()

        result = func(*args, **kwargs)
        if _is_cacheable(result):
            with open(path, "w", encoding="utf-8") as f:
                f.write(result)
        return result

    return wrapper
