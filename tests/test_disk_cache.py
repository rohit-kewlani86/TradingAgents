import pytest

import tradingagents.dataflows.cache as cache_mod
from tradingagents.dataflows.cache import disk_cache


@pytest.fixture(autouse=True)
def _tmp_cache_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(
        cache_mod, "get_config", lambda: {"data_cache_dir": str(tmp_path)}
    )
    return tmp_path


@pytest.mark.unit
def test_miss_calls_underlying_and_caches():
    calls = {"n": 0}

    @disk_cache
    def fetch(ticker, date):
        calls["n"] += 1
        return f"data for {ticker} {date}"

    assert fetch("AAPL", "2026-01-15") == "data for AAPL 2026-01-15"
    assert calls["n"] == 1


@pytest.mark.unit
def test_hit_returns_cached_without_calling():
    calls = {"n": 0}

    @disk_cache
    def fetch(ticker, date):
        calls["n"] += 1
        return f"data for {ticker} {date}"

    fetch("AAPL", "2026-01-15")
    second = fetch("AAPL", "2026-01-15")

    assert second == "data for AAPL 2026-01-15"
    assert calls["n"] == 1  # underlying not called again


@pytest.mark.unit
def test_distinct_args_are_cached_separately():
    calls = {"n": 0}

    @disk_cache
    def fetch(ticker, date):
        calls["n"] += 1
        return f"data for {ticker} {date}"

    fetch("AAPL", "2026-01-15")
    fetch("MSFT", "2026-01-15")

    assert calls["n"] == 2


@pytest.mark.unit
def test_error_result_not_cached():
    calls = {"n": 0}

    @disk_cache
    def fetch(ticker, date):
        calls["n"] += 1
        return "Error retrieving data: boom"

    fetch("AAPL", "2026-01-15")
    fetch("AAPL", "2026-01-15")

    assert calls["n"] == 2  # error not persisted, so refetched


@pytest.mark.unit
def test_empty_result_not_cached():
    calls = {"n": 0}

    @disk_cache
    def fetch(ticker, date):
        calls["n"] += 1
        return "   "

    fetch("AAPL", "2026-01-15")
    fetch("AAPL", "2026-01-15")

    assert calls["n"] == 2
