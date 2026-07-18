"""#4 guardrail: warn when the requested trade date's daily bar is not yet
published, so an early-morning run doesn't silently price an older day than a
later run once the vendor posts the bar."""

import logging

import pandas as pd
import pytest

import tradingagents.dataflows.stockstats_utils as su


@pytest.fixture(autouse=True)
def _freeze_today(monkeypatch):
    # "today" = 2026-07-17 (Fri) -> settled cutoff = 2026-07-16 (Thu)
    monkeypatch.setattr(su, "_current_timestamp", lambda: pd.Timestamp("2026-07-17"))


def _frame(dates):
    return pd.DataFrame({"Date": dates, "Close": [1.0] * len(dates), "Volume": [1] * len(dates)})


@pytest.mark.unit
class TestSettledBarWarning:
    def test_warns_when_requested_bar_not_published(self, caplog):
        # bars only through Jul 15; requested Jul 16 (a settled day) is missing
        data = _frame(["2026-07-14", "2026-07-15"])
        with caplog.at_level(logging.WARNING, logger=su.logger.name):
            out = su.filter_to_settled_bars(data, "2026-07-16")
        assert pd.to_datetime(out["Date"]).max().normalize() == pd.Timestamp("2026-07-15")
        assert any("2026-07-16" in r.message and "2026-07-15" in r.message for r in caplog.records)

    def test_no_warning_when_requested_bar_present(self, caplog):
        data = _frame(["2026-07-15", "2026-07-16"])
        with caplog.at_level(logging.WARNING, logger=su.logger.name):
            su.filter_to_settled_bars(data, "2026-07-16")
        assert not caplog.records

    def test_no_warning_when_requesting_the_in_progress_day(self, caplog):
        # requesting today (Jul 17) legitimately returns the last settled bar;
        # that's expected, not a missing-publication case -> no warning
        data = _frame(["2026-07-15", "2026-07-16"])
        with caplog.at_level(logging.WARNING, logger=su.logger.name):
            su.filter_to_settled_bars(data, "2026-07-17")
        assert not caplog.records
