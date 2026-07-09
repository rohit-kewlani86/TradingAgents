"""Tests for the settled-trade-date helper (fix/settled-trade-date).

Runs default to the in-progress trading day, whose daily bar is still
forming — price/volume (and accumulating news) change intraday, so the
recommendation flips run-to-run. `last_completed_session` is a pure helper
that returns the last COMPLETED trading session on or before a reference
date, so a normal run never analyzes the still-forming current day.

Definition encoded here: the helper looks at the calendar day *before* the
reference date and walks backward until it lands on a non-weekend day. The
reference day itself is never returned (it may still be in progress), and
Saturday/Sunday are treated as non-trading days.
"""

import unittest
from unittest import mock

import pytest

from cli.utils import last_completed_session


@pytest.mark.unit
class TestLastCompletedSession:
    def test_weekday_reference_returns_prior_weekday(self):
        # 2026-07-08 is a Wednesday; the prior weekday is Tuesday 2026-07-07.
        assert last_completed_session("2026-07-08") == "2026-07-07"

    def test_tuesday_reference_returns_prior_monday(self):
        assert last_completed_session("2026-07-07") == "2026-07-06"

    def test_saturday_reference_returns_prior_friday(self):
        # 2026-07-11 is a Saturday.
        assert last_completed_session("2026-07-11") == "2026-07-10"

    def test_sunday_reference_returns_prior_friday(self):
        # 2026-07-12 is a Sunday.
        assert last_completed_session("2026-07-12") == "2026-07-10"

    def test_monday_reference_skips_entire_weekend_to_prior_friday(self):
        # 2026-07-13 is a Monday; the day before is Sunday, so we must walk
        # back through Saturday to reach Friday 2026-07-10.
        assert last_completed_session("2026-07-13") == "2026-07-10"

    def test_never_returns_the_reference_date_itself(self):
        for reference in ("2026-07-06", "2026-07-07", "2026-07-11", "2026-07-12"):
            assert last_completed_session(reference) != reference

    def test_never_returns_a_weekend_date(self):
        import datetime

        for reference in (
            "2026-07-06",
            "2026-07-07",
            "2026-07-08",
            "2026-07-09",
            "2026-07-10",
            "2026-07-11",
            "2026-07-12",
            "2026-07-13",
        ):
            result = last_completed_session(reference)
            weekday = datetime.datetime.strptime(result, "%Y-%m-%d").weekday()
            assert weekday < 5

    def test_returns_yyyy_mm_dd_string(self):
        result = last_completed_session("2026-07-08")
        assert isinstance(result, str)
        assert len(result) == 10
        assert result[4] == "-" and result[7] == "-"

    def test_holiday_set_is_skipped_when_provided(self):
        # 2026-07-08 (Wednesday) with 2026-07-07 marked as a holiday should
        # fall back further to 2026-07-06 (Monday). This keeps the function
        # structured so a US-market-holiday calendar can be plugged in later
        # without changing the weekend-skipping behavior.
        assert last_completed_session(
            "2026-07-08", holidays=frozenset({"2026-07-07"})
        ) == "2026-07-06"


@pytest.mark.unit
class TestCliAnalysisDateDefaultsToSettledSession(unittest.TestCase):
    """cli.main.get_analysis_date should default to the last completed
    session (not the in-progress current day), and warn — without
    blocking — when the user explicitly enters today's date."""

    def test_prompt_default_is_last_completed_session_not_today(self):
        import cli.main as m

        with mock.patch.object(m.typer, "prompt", return_value="2026-07-07") as prompt_fn:
            m.get_analysis_date(today="2026-07-08")

        _, kwargs = prompt_fn.call_args
        self.assertEqual(kwargs["default"], "2026-07-07")

    def test_warns_when_user_enters_the_in_progress_day(self):
        import cli.main as m

        with mock.patch.object(m.typer, "prompt", return_value="2026-07-08"), \
             mock.patch.object(m.console, "print") as mock_print:
            result = m.get_analysis_date(today="2026-07-08")

        self.assertEqual(result, "2026-07-08")
        printed = " ".join(str(call.args[0]) for call in mock_print.call_args_list if call.args)
        self.assertIn("not settled", printed.lower())

    def test_no_warning_for_a_settled_prior_date(self):
        import cli.main as m

        with mock.patch.object(m.typer, "prompt", return_value="2026-07-07"), \
             mock.patch.object(m.console, "print") as mock_print:
            m.get_analysis_date(today="2026-07-08")

        printed = " ".join(str(call.args[0]) for call in mock_print.call_args_list if call.args)
        self.assertNotIn("not settled", printed.lower())
