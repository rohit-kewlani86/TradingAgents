import pytest

from tradingagents.agents.schemas import (
    PositionSizingPlan,
    render_position_sizing_plan,
)


@pytest.mark.unit
def test_position_sizing_plan_minimal_fields():
    plan = PositionSizingPlan(
        recommended_size_pct=5.0,
        sizing_rationale="2% account risk, ATR-based stop, risk-on regime.",
    )
    assert plan.recommended_size_pct == 5.0
    assert plan.entry_price is None
    assert plan.stop_loss is None


@pytest.mark.unit
def test_render_position_sizing_plan_includes_core_fields():
    plan = PositionSizingPlan(
        recommended_size_pct=5.0,
        entry_price=450.0,
        stop_loss=435.0,
        target_price=490.0,
        risk_reward_ratio=2.6,
        sizing_rationale="ATR stop 15 pts; 2% risk on 100k = 5% position.",
    )
    md = render_position_sizing_plan(plan)

    assert "Recommended Size" in md
    assert "5.0" in md
    assert "Entry" in md and "450.0" in md
    assert "Stop Loss" in md and "435.0" in md
    assert "Target" in md and "490.0" in md
    assert "Risk/Reward" in md and "2.6" in md
    assert "ATR stop 15 pts" in md


@pytest.mark.unit
def test_render_position_sizing_plan_omits_absent_optionals():
    plan = PositionSizingPlan(
        recommended_size_pct=0.0,
        sizing_rationale="Hold — no new exposure.",
    )
    md = render_position_sizing_plan(plan)

    assert "Recommended Size" in md
    assert "Entry" not in md
    assert "Stop Loss" not in md
