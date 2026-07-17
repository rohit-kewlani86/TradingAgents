"""Progress panel windowing: the table follows the in-progress agent instead of
clipping the later teams off the bottom of a fixed-height panel."""

import pytest

from cli.main import (
    progress_focus_index,
    progress_viewport_rows,
    select_visible_progress_rows,
)


@pytest.mark.unit
class TestProgressFocusIndex:
    def test_first_in_progress_wins(self):
        # parallel analysts: several in_progress -> anchor on the first
        statuses = ["completed", "in_progress", "in_progress", "pending", "pending"]
        assert progress_focus_index(statuses) == 1

    def test_first_pending_when_none_in_progress(self):
        statuses = ["completed", "completed", "pending", "pending"]
        assert progress_focus_index(statuses) == 2

    def test_last_row_when_all_completed(self):
        statuses = ["completed", "completed", "completed"]
        assert progress_focus_index(statuses) == 2

    def test_empty_is_zero(self):
        assert progress_focus_index([]) == 0


@pytest.mark.unit
class TestSelectVisibleRows:
    def test_shows_all_when_it_fits(self):
        rows = list(range(5))
        visible, above, below = select_visible_progress_rows(rows, focus_index=2, max_rows=10)
        assert visible == rows and above == 0 and below == 0

    def test_focus_is_first_visible_row(self):
        rows = list(range(20))
        visible, above, below = select_visible_progress_rows(rows, focus_index=10, max_rows=8)
        assert visible[0] == 10          # focus anchored at the very top
        assert above == 10
        assert above + len(visible) + below == 20

    def test_focus_at_zero(self):
        rows = list(range(20))
        visible, above, below = select_visible_progress_rows(rows, focus_index=0, max_rows=8)
        assert above == 0 and visible[0] == 0 and len(visible) == 8

    def test_survives_when_focus_near_end(self):
        rows = list(range(20))
        visible, above, below = select_visible_progress_rows(rows, focus_index=19, max_rows=8)
        assert visible[0] == 19 and below == 0

    def test_focus_is_first_row_across_all_positions(self):
        rows = list(range(30))
        for focus in range(30):
            visible, _, _ = select_visible_progress_rows(rows, focus, max_rows=7)
            assert visible[0] == rows[focus]  # top-anchored: survives bottom-crop


@pytest.mark.unit
class TestViewportRows:
    def test_taller_console_gives_more_rows(self):
        assert progress_viewport_rows(60) > progress_viewport_rows(24)

    def test_never_below_floor(self):
        assert progress_viewport_rows(10) >= 6
        assert progress_viewport_rows(1) >= 6
