"""Raw-vs-verified market data source-of-truth reconciliation.

Reproduces the drift observed in production: `get_stock_data` (raw OHLCV CSV,
via ``get_YFin_data_online``) and `get_verified_market_snapshot` (via
``load_ohlcv``) disagreed on the close/volume for the SAME (ticker, as-of
date) because the raw path returned Yahoo's in-progress current-day bar,
which changes intraday, while the verified path happened to be more stable.

The fix: both paths funnel through ``filter_to_settled_bars``, which drops
any bar dated the real "today" (a still-forming trading day) before either
path can report it. Both then agree on the same last SETTLED bar for a given
as-of date.
"""

from __future__ import annotations

import pandas as pd
import pytest

import tradingagents.dataflows.stockstats_utils as su
import tradingagents.dataflows.y_finance as yfin
from tradingagents.dataflows.config import set_config
from tradingagents.dataflows.market_data_validator import build_verified_market_snapshot

FROZEN_NOW = pd.Timestamp("2026-07-08 14:30:00")  # a Wednesday, mid trading day


def _frozen_now() -> pd.Timestamp:
    return FROZEN_NOW


def _history_frame() -> pd.DataFrame:
    """Simulates a yfinance frame whose LAST row is today's forming bar.

    2026-07-07 (Tue) is the last fully settled close. 2026-07-08 (today, per
    FROZEN_NOW) is still in progress and carries a different, drifting close
    than the settled bar — exactly the AMD-style symptom from production.
    """
    idx = pd.to_datetime(
        ["2026-07-06", "2026-07-07", "2026-07-08"]
    )
    return pd.DataFrame(
        {
            "Open": [503.10, 504.20, 510.00],
            "High": [507.50, 508.90, 519.00],
            "Low": [501.00, 503.00, 505.00],
            "Close": [505.10, 506.36, 517.41],
            "Volume": [7_500_000, 7_873_096, 23_720_000],
        },
        index=idx,
    )


@pytest.mark.unit
class TestFilterToSettledBars:
    def test_drops_row_dated_the_real_current_day(self, monkeypatch):
        monkeypatch.setattr(su, "_current_timestamp", _frozen_now)
        data = _history_frame()

        out = su.filter_to_settled_bars(data, "2026-07-08")

        assert list(out.index) == [pd.Timestamp("2026-07-06"), pd.Timestamp("2026-07-07")]
        assert out.iloc[-1]["Close"] == 506.36
        assert out.iloc[-1]["Volume"] == 7_873_096

    def test_leaves_fully_historical_dates_untouched(self, monkeypatch):
        """No behavior change for an as-of date that is already in the past —
        there is no forming bar to worry about."""
        monkeypatch.setattr(su, "_current_timestamp", _frozen_now)
        data = _history_frame()

        out = su.filter_to_settled_bars(data, "2026-07-07")

        assert list(out.index) == [pd.Timestamp("2026-07-06"), pd.Timestamp("2026-07-07")]

    def test_works_with_date_column_instead_of_index(self, monkeypatch):
        monkeypatch.setattr(su, "_current_timestamp", _frozen_now)
        data = _history_frame().reset_index().rename(columns={"index": "Date"})

        out = su.filter_to_settled_bars(data, "2026-07-08")

        assert out["Date"].max() == pd.Timestamp("2026-07-07")
        assert out.iloc[-1]["Close"] == 506.36

    def test_empty_frame_passes_through(self, monkeypatch):
        monkeypatch.setattr(su, "_current_timestamp", _frozen_now)
        out = su.filter_to_settled_bars(pd.DataFrame(), "2026-07-08")
        assert out.empty


@pytest.mark.unit
class TestLoadOhlcvExcludesFormingBar:
    def test_load_ohlcv_drops_todays_partial_bar(self, monkeypatch, tmp_path):
        monkeypatch.setattr(su, "_current_timestamp", _frozen_now)
        set_config({"data_cache_dir": str(tmp_path)})

        def fake_download(symbol, start, end, **kwargs):
            return _history_frame()

        monkeypatch.setattr(su.yf, "download", fake_download)

        data = su.load_ohlcv("AMD", "2026-07-08")

        assert data["Date"].max() == pd.Timestamp("2026-07-07")
        last_row = data.iloc[-1]
        assert last_row["Close"] == 506.36
        assert last_row["Volume"] == 7_873_096


@pytest.mark.unit
class TestGetYFinDataOnlineExcludesFormingBar:
    def test_raw_csv_path_drops_todays_partial_bar(self, monkeypatch):
        monkeypatch.setattr(su, "_current_timestamp", _frozen_now)

        class FakeTicker:
            def __init__(self, symbol):
                pass

            def history(self, start, end):
                return _history_frame()

        monkeypatch.setattr(yfin.yf, "Ticker", FakeTicker)

        out = yfin.get_YFin_data_online("AMD", "2026-07-01", "2026-07-08")
        csv_rows = out.split("\n\n", 1)[1]  # drop the header block

        assert "2026-07-08" not in csv_rows  # today's forming bar is not a data row
        assert "506.36" in csv_rows
        assert "7873096" in csv_rows
        assert "517.41" not in csv_rows  # the in-progress, drifting close never surfaces


@pytest.mark.unit
class TestRawAndVerifiedPathsAgree:
    """The central regression test: feed the SAME underlying vendor frame to
    both the raw OHLCV path and the verified-snapshot path and assert they
    report the SAME settled close/volume for the SAME as-of date — the raw
    path must no longer diverge onto an in-progress bar.
    """

    def test_raw_and_verified_report_the_same_settled_bar(self, monkeypatch, tmp_path):
        monkeypatch.setattr(su, "_current_timestamp", _frozen_now)
        set_config({"data_cache_dir": str(tmp_path)})

        class FakeTicker:
            def __init__(self, symbol):
                pass

            def history(self, start, end):
                return _history_frame()

        monkeypatch.setattr(yfin.yf, "Ticker", FakeTicker)
        monkeypatch.setattr(su.yf, "download", lambda symbol, start, end, **kw: _history_frame())

        raw_csv = yfin.get_YFin_data_online("AMD", "2026-07-01", "2026-07-08")
        verified = build_verified_market_snapshot("AMD", "2026-07-08")

        # Same settled bar (2026-07-07, close 506.36, volume 7,873,096) in both.
        assert "506.36" in raw_csv
        assert "506.36" in verified
        assert "7873096" in raw_csv
        assert "7873096" in verified

        # Neither surfaces the drifting in-progress bar.
        assert "517.41" not in raw_csv
        assert "517.41" not in verified
