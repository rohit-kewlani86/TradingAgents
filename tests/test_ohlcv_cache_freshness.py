import pandas as pd
import pytest

from tradingagents.dataflows.stockstats_utils import _cache_is_stale


@pytest.mark.unit
def test_cache_stale_when_missing_latest_trading_day():
    # As-of Saturday 2026-06-27; latest trading day is Friday 2026-06-26.
    asof = pd.Timestamp("2026-06-27")
    assert _cache_is_stale(pd.Timestamp("2026-06-25"), asof) is True


@pytest.mark.unit
def test_cache_fresh_when_latest_trading_day_present():
    asof = pd.Timestamp("2026-06-27")
    assert _cache_is_stale(pd.Timestamp("2026-06-26"), asof) is False


@pytest.mark.unit
def test_cache_fresh_on_weekday_with_same_day_data():
    # Wednesday with Wednesday data is current.
    asof = pd.Timestamp("2026-06-24")
    assert _cache_is_stale(pd.Timestamp("2026-06-24"), asof) is False


@pytest.mark.unit
def test_cache_stale_when_empty():
    asof = pd.Timestamp("2026-06-27")
    assert _cache_is_stale(pd.NaT, asof) is True
