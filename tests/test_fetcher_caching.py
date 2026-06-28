import pytest

import tradingagents.dataflows.cache as cache_mod
import tradingagents.dataflows.y_finance as yfin
import tradingagents.dataflows.yfinance_news as ynews

WRAPPED = [
    (yfin, "get_fundamentals"),
    (yfin, "get_balance_sheet"),
    (yfin, "get_cashflow"),
    (yfin, "get_income_statement"),
    (yfin, "get_insider_transactions"),
    (ynews, "get_news_yfinance"),
    (ynews, "get_global_news_yfinance"),
]


@pytest.fixture(autouse=True)
def _tmp_cache_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(
        cache_mod, "get_config", lambda: {"data_cache_dir": str(tmp_path)}
    )
    return tmp_path


@pytest.mark.unit
@pytest.mark.parametrize("mod,name", WRAPPED, ids=[n for _, n in WRAPPED])
def test_fetcher_is_disk_cached(mod, name):
    fn = getattr(mod, name)
    assert hasattr(fn, "__wrapped__"), f"{name} is not wrapped by disk_cache"


@pytest.mark.unit
def test_news_fetcher_hits_yfinance_once(monkeypatch):
    calls = {"n": 0}

    class FakeTicker:
        def __init__(self, ticker):
            pass

        def get_news(self, count=20):
            calls["n"] += 1
            return [
                {
                    "content": {
                        "title": "Big news",
                        "summary": "summary",
                        "provider": {"displayName": "Publisher"},
                        "canonicalUrl": {"url": "http://example.com"},
                        "pubDate": "",
                    }
                }
            ]

    monkeypatch.setattr(ynews.yf, "Ticker", FakeTicker)

    first = ynews.get_news_yfinance("AAPL", "2026-01-01", "2026-01-31")
    second = ynews.get_news_yfinance("AAPL", "2026-01-01", "2026-01-31")

    assert first == second
    assert calls["n"] == 1  # second call served from disk cache
