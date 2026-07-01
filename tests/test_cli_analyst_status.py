import pytest

from cli.main import MessageBuffer, update_analyst_statuses, ANALYST_AGENT_NAMES, _analyst_team_names


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
def test_update_report_section_technical_does_not_crash():
    """updating technical_report must not raise KeyError in _update_current_report."""
    buf = MessageBuffer()
    buf.init_for_analysis(["market", "social", "news", "fundamentals", "technical"])

    # This crashed before the fix: KeyError: 'technical_report'
    buf.update_report_section("technical_report", "RSI at 72, entry zone $450–$455.")

    assert buf.current_report is not None
    assert "Technical" in buf.current_report


@pytest.mark.unit
def test_final_report_includes_technical_report():
    """technical_report content must appear in the assembled final report."""
    buf = MessageBuffer()
    buf.init_for_analysis(["market", "social", "news", "fundamentals", "technical"])
    buf.update_report_section("technical_report", "RSI at 72, entry zone $450–$455.")

    assert buf.final_report is not None
    assert "RSI at 72" in buf.final_report


@pytest.mark.unit
def test_all_analyst_names_in_panel_team_list():
    """Every analyst in ANALYST_AGENT_NAMES must appear in the Analyst Team
    source list used by update_display — so adding a new analyst to the mapping
    automatically makes it visible in the Rich progress panel."""
    team_names = _analyst_team_names()
    for key, display_name in ANALYST_AGENT_NAMES.items():
        assert display_name in team_names, (
            f"'{display_name}' (key={key!r}) is missing from _analyst_team_names(); "
            "it will never appear in the UI progress panel"
        )


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


@pytest.mark.unit
def test_macro_analyst_in_progress_when_selected_and_no_report():
    """Macro Analyst should appear in_progress like the others when selected."""
    buf = MessageBuffer()
    buf.init_for_analysis(["market", "social", "news", "fundamentals", "technical", "macro"])

    update_analyst_statuses(buf, {})

    assert buf.agent_status["Macro Analyst"] == "in_progress"


@pytest.mark.unit
def test_macro_analyst_type_exists():
    from cli.models import AnalystType

    assert AnalystType.MACRO == "macro"


@pytest.mark.unit
def test_macro_analyst_in_cli_utils_order():
    from cli.utils import ANALYST_ORDER
    from cli.models import AnalystType

    keys = [key for _, key in ANALYST_ORDER]
    assert AnalystType.MACRO in keys


@pytest.mark.unit
def test_position_sizer_in_agent_status_after_init():
    """Position Sizer is a fixed (always-run) agent, so it must show in the panel."""
    buf = MessageBuffer()
    buf.init_for_analysis(["market", "social", "news", "fundamentals", "technical", "macro"])

    assert "Position Sizer" in buf.agent_status


@pytest.mark.unit
def test_position_sizer_in_panel_team_list():
    """Position Sizer must appear in a team group so update_display can render it."""
    from cli.main import MessageBuffer as MB

    team_agents = [a for agents in MB.FIXED_AGENTS.values() for a in agents]
    assert "Position Sizer" in team_agents


@pytest.mark.unit
def test_update_report_section_position_sizing_does_not_crash():
    buf = MessageBuffer()
    buf.init_for_analysis(["market", "social", "news", "fundamentals", "technical", "macro"])

    buf.update_report_section("position_sizing_plan", "Recommended Size: 5% of portfolio")

    assert buf.current_report is not None
    assert "Position Sizing" in buf.current_report


@pytest.mark.unit
def test_final_report_includes_position_sizing():
    buf = MessageBuffer()
    buf.init_for_analysis(["market", "social", "news", "fundamentals", "technical", "macro"])
    buf.update_report_section("position_sizing_plan", "Recommended Size: 5% of portfolio")

    assert buf.final_report is not None
    assert "5% of portfolio" in buf.final_report


@pytest.mark.unit
def test_update_report_section_macro_does_not_crash():
    """updating macro_report must not raise KeyError in _update_current_report."""
    buf = MessageBuffer()
    buf.init_for_analysis(["market", "social", "news", "fundamentals", "technical", "macro"])

    buf.update_report_section("macro_report", "10y at 4.3% rising; VIX 18; net HEADWIND.")

    assert buf.current_report is not None
    assert "Macro" in buf.current_report


@pytest.mark.unit
def test_final_report_includes_macro_report():
    """macro_report content must appear in the assembled final report."""
    buf = MessageBuffer()
    buf.init_for_analysis(["market", "social", "news", "fundamentals", "technical", "macro"])
    buf.update_report_section("macro_report", "10y at 4.3% rising; VIX 18; net HEADWIND.")

    assert buf.final_report is not None
    assert "net HEADWIND" in buf.final_report
