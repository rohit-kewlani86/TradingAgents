import pytest

from cli.main import MessageBuffer, update_analyst_statuses


@pytest.mark.unit
def test_all_selected_analysts_in_progress_when_none_done():
    """Analysts run in parallel, so before any report arrives every selected
    analyst should display as in_progress, not just the first one."""
    buf = MessageBuffer()
    buf.init_for_analysis(["market", "social", "news", "fundamentals"])

    update_analyst_statuses(buf, {})

    assert buf.agent_status["Market Analyst"] == "in_progress"
    assert buf.agent_status["Social Analyst"] == "in_progress"
    assert buf.agent_status["News Analyst"] == "in_progress"
    assert buf.agent_status["Fundamentals Analyst"] == "in_progress"


@pytest.mark.unit
def test_technical_analyst_in_progress_when_selected_and_no_report():
    """Technical Analyst should appear in_progress like the others when selected."""
    buf = MessageBuffer()
    buf.init_for_analysis(["market", "social", "news", "fundamentals", "technical"])

    update_analyst_statuses(buf, {})

    assert buf.agent_status["Technical Analyst"] == "in_progress"


@pytest.mark.unit
def test_technical_analyst_type_exists():
    from cli.models import AnalystType

    assert AnalystType.TECHNICAL == "technical"


@pytest.mark.unit
def test_technical_analyst_in_cli_utils_order():
    from cli.utils import ANALYST_ORDER
    from cli.models import AnalystType

    keys = [key for _, key in ANALYST_ORDER]
    assert AnalystType.TECHNICAL in keys
