"""News must be pinned to the trade-date window and cached per (subject, as-of
date), so a rerun for the same ticker/date is deterministic.

Regression context: two runs of the same ticker/date 27 minutes apart cited
completely different macro drivers because news was fetched "latest" and kept
drifting through the day. Pinning the window to the as-of date (not "now")
and caching the raw vendor response per (subject, date) makes a rerun
byte-identical and stops the report from flip-flopping.
"""
import json
import time
from datetime import datetime

import pytest

import tradingagents.dataflows.alpha_vantage_news as av_news
import tradingagents.dataflows.yfinance_news as ynews
from tradingagents.dataflows.config import set_config


def _epoch(date_str: str) -> int:
    return int(time.mktime(datetime.strptime(date_str, "%Y-%m-%d").timetuple()))


# ---------------------------------------------------------------------------
# (a) + (b): window anchored to the as-of/trade date, not "now"; articles
# dated after the as-of date are excluded even if they are in the past
# relative to the real wall-clock "now".
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_ticker_news_window_anchored_to_trade_date_not_now(monkeypatch, tmp_path):
    set_config({"data_cache_dir": str(tmp_path)})

    in_window = {
        "title": "IN WINDOW", "publisher": "P", "link": "l",
        "providerPublishTime": _epoch("2025-05-05"),
    }
    after_asof = {
        "title": "AFTER AS-OF", "publisher": "P", "link": "l",
        # Dated after the trade date's end_date, but still in the past
        # relative to the real "now" the test is run under — this must be
        # excluded purely because it postdates the as-of date, not because
        # of any comparison against the real clock.
        "providerPublishTime": _epoch("2025-05-08"),
    }

    class FakeTicker:
        def __init__(self, symbol):
            pass

        def get_news(self, count):
            return [in_window, after_asof]

    monkeypatch.setattr(ynews.yf, "Ticker", FakeTicker)
    monkeypatch.setattr(ynews, "yf_retry", lambda fn: fn())

    out = ynews.get_news_yfinance("AAPL", "2025-05-01", "2025-05-06")

    assert "IN WINDOW" in out
    assert "AFTER AS-OF" not in out


@pytest.mark.unit
def test_global_news_window_excludes_articles_after_asof_date(monkeypatch, tmp_path):
    set_config({"data_cache_dir": str(tmp_path)})

    past_article = {
        "title": "PAST GLOBAL", "publisher": "P", "link": "l",
        "providerPublishTime": _epoch("2025-05-05"),
    }
    future_article = {
        "title": "FUTURE GLOBAL", "publisher": "P", "link": "l",
        "providerPublishTime": _epoch("2025-05-20"),
    }

    class FakeSearch:
        def __init__(self, *a, **k):
            self.news = [past_article, future_article]

    monkeypatch.setattr(ynews.yf, "Search", FakeSearch)

    out = ynews.get_global_news_yfinance("2025-05-09", look_back_days=7, limit=10)

    assert "PAST GLOBAL" in out
    assert "FUTURE GLOBAL" not in out


# ---------------------------------------------------------------------------
# (c) caching: same (subject, as-of date) -> identical results, fetch called once.
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_ticker_news_second_call_served_from_cache(monkeypatch, tmp_path):
    set_config({"data_cache_dir": str(tmp_path)})
    call_count = {"n": 0}

    class FakeTicker:
        def __init__(self, symbol):
            pass

        def get_news(self, count):
            call_count["n"] += 1
            return [{
                "title": f"ARTICLE {call_count['n']}", "publisher": "P", "link": "l",
                "providerPublishTime": _epoch("2025-05-05"),
            }]

    monkeypatch.setattr(ynews.yf, "Ticker", FakeTicker)
    monkeypatch.setattr(ynews, "yf_retry", lambda fn: fn())

    first = ynews.get_news_yfinance("AAPL", "2025-05-01", "2025-05-06")
    second = ynews.get_news_yfinance("AAPL", "2025-05-01", "2025-05-06")

    assert call_count["n"] == 1
    assert first == second
    assert "ARTICLE 1" in first
    assert "ARTICLE 1" in second


@pytest.mark.unit
def test_ticker_news_cache_is_keyed_per_asof_date(monkeypatch, tmp_path):
    set_config({"data_cache_dir": str(tmp_path)})
    call_count = {"n": 0}

    class FakeTicker:
        def __init__(self, symbol):
            pass

        def get_news(self, count):
            call_count["n"] += 1
            return [{
                "title": f"ARTICLE {call_count['n']}", "publisher": "P", "link": "l",
                "providerPublishTime": _epoch("2025-05-05"),
            }]

    monkeypatch.setattr(ynews.yf, "Ticker", FakeTicker)
    monkeypatch.setattr(ynews, "yf_retry", lambda fn: fn())

    ynews.get_news_yfinance("AAPL", "2025-05-01", "2025-05-06")
    ynews.get_news_yfinance("AAPL", "2025-06-01", "2025-06-06")

    assert call_count["n"] == 2


@pytest.mark.unit
def test_global_news_second_call_served_from_cache(monkeypatch, tmp_path):
    set_config({"data_cache_dir": str(tmp_path)})
    call_count = {"n": 0}

    class FakeSearch:
        def __init__(self, *a, **k):
            call_count["n"] += 1
            self.news = [{
                "title": f"GLOBAL {call_count['n']}", "publisher": "P", "link": "l",
                "providerPublishTime": _epoch("2025-05-05"),
            }]

    monkeypatch.setattr(ynews.yf, "Search", FakeSearch)

    first = ynews.get_global_news_yfinance("2025-05-09", look_back_days=7, limit=10)
    second = ynews.get_global_news_yfinance("2025-05-09", look_back_days=7, limit=10)

    queries = 5  # len(default global_news_queries) — each query is one Search() call
    assert call_count["n"] == queries
    assert first == second
    assert "GLOBAL 1" in first
    assert "GLOBAL 1" in second


@pytest.mark.unit
def test_alpha_vantage_ticker_news_second_call_served_from_cache(monkeypatch, tmp_path):
    set_config({"data_cache_dir": str(tmp_path)})
    call_count = {"n": 0}

    def fake_make_api_request(function_name, params):
        call_count["n"] += 1
        return json.dumps({"feed": [{"title": f"AV ARTICLE {call_count['n']}"}]})

    monkeypatch.setattr(av_news, "_make_api_request", fake_make_api_request)

    first = av_news.get_news("AAPL", "2025-05-01", "2025-05-06")
    second = av_news.get_news("AAPL", "2025-05-01", "2025-05-06")

    assert call_count["n"] == 1
    assert first == second


@pytest.mark.unit
def test_alpha_vantage_global_news_second_call_served_from_cache(monkeypatch, tmp_path):
    set_config({"data_cache_dir": str(tmp_path)})
    call_count = {"n": 0}

    def fake_make_api_request(function_name, params):
        call_count["n"] += 1
        return json.dumps({"feed": [{"title": f"AV GLOBAL {call_count['n']}"}]})

    monkeypatch.setattr(av_news, "_make_api_request", fake_make_api_request)

    first = av_news.get_global_news("2025-05-09", look_back_days=7, limit=50)
    second = av_news.get_global_news("2025-05-09", look_back_days=7, limit=50)

    assert call_count["n"] == 1
    assert first == second
