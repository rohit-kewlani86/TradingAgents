"""Pre-IPO mode threaded through the initial agent state."""

import pytest

from tradingagents.graph.propagation import Propagator


@pytest.mark.unit
class TestInitialStateCompanyMode:
    def test_defaults_to_listed_when_not_passed(self):
        state = Propagator().create_initial_state("NVDA", "2026-01-15")
        assert state["company_mode"] == "listed"

    def test_carries_pre_ipo_mode_when_passed(self):
        state = Propagator().create_initial_state(
            "SpaceX", "2026-01-15", company_mode="pre_ipo"
        )
        assert state["company_mode"] == "pre_ipo"
