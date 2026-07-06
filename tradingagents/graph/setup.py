# TradingAgents/graph/setup.py

from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from tradingagents.agents import (
    create_aggressive_debator,
    create_bear_researcher,
    create_bull_researcher,
    create_conservative_debator,
    create_devils_advocate,
    create_fundamentals_analyst,
    create_market_analyst,
    create_neutral_debator,
    create_news_analyst,
    create_portfolio_manager,
    create_position_sizer,
    create_research_manager,
    create_scenario_analyst,
    create_macro_analyst,
    create_sentiment_analyst,
    create_technical_analyst,
    create_trader,
    create_valuation_analyst,
)
from tradingagents.agents.utils.agent_states import AgentState

from .analyst_execution import build_analyst_execution_plan
from .conditional_logic import ConditionalLogic


def _analyst_done(state):
    """No-op barrier node marking an analyst's tool loop as finished.

    Reports are written to state by the analyst itself; this node only exists
    as a fan-in synchronization point for the Bull Researcher.
    """
    return {}


class GraphSetup:
    """Handles the setup and configuration of the agent graph."""

    def __init__(
        self,
        quick_thinking_llm: Any,
        deep_thinking_llm: Any,
        tool_nodes: dict[str, ToolNode],
        conditional_logic: ConditionalLogic,
        asset_type: str = "stock",
    ):
        """Initialize with required components.

        ``asset_type`` selects the analyst mix. For ``"pre_ipo"`` the market
        slot is filled by the Valuation Analyst (private-market reasoning)
        instead of the Market Analyst, since a pre-listing company has no price
        history; both write the same ``market_report`` on ``market_messages``.
        """
        self.quick_thinking_llm = quick_thinking_llm
        self.deep_thinking_llm = deep_thinking_llm
        self.tool_nodes = tool_nodes
        self.conditional_logic = conditional_logic
        self.asset_type = asset_type

    def setup_graph(
        self, selected_analysts=("market", "social", "news", "fundamentals")
    ):
        """Set up and compile the agent workflow graph.

        Args:
            selected_analysts (list): List of analyst types to include. Options are:
                - "market": Market analyst
                - "social": Social media analyst
                - "news": News analyst
                - "fundamentals": Fundamentals analyst
        """
        plan = build_analyst_execution_plan(selected_analysts)

        # Pre-IPO companies have no price history, so the market slot reasons
        # about private valuation instead of technicals. Same node, channel,
        # and report_key — only the analyst body differs.
        market_factory = (
            create_valuation_analyst
            if self.asset_type == "pre_ipo"
            else create_market_analyst
        )

        analyst_factories = {
            "market": lambda: market_factory(self.quick_thinking_llm),
            "social": lambda: create_sentiment_analyst(self.quick_thinking_llm),
            "news": lambda: create_news_analyst(self.quick_thinking_llm),
            "fundamentals": lambda: create_fundamentals_analyst(self.quick_thinking_llm),
            "technical": lambda: create_technical_analyst(self.quick_thinking_llm),
            "macro": lambda: create_macro_analyst(self.quick_thinking_llm),
        }

        # Create researcher and manager nodes
        bull_researcher_node = create_bull_researcher(self.quick_thinking_llm)
        bear_researcher_node = create_bear_researcher(self.quick_thinking_llm)
        research_manager_node = create_research_manager(self.deep_thinking_llm)
        scenario_analyst_node = create_scenario_analyst(self.deep_thinking_llm)
        trader_node = create_trader(self.quick_thinking_llm)

        # Create risk analysis nodes
        aggressive_analyst = create_aggressive_debator(self.quick_thinking_llm)
        neutral_analyst = create_neutral_debator(self.quick_thinking_llm)
        conservative_analyst = create_conservative_debator(self.quick_thinking_llm)
        portfolio_manager_node = create_portfolio_manager(self.deep_thinking_llm)
        position_sizer_node = create_position_sizer(self.quick_thinking_llm)
        devils_advocate_node = create_devils_advocate(self.deep_thinking_llm)

        # Create workflow
        workflow = StateGraph(AgentState)

        # Add analyst nodes to the graph. Each analyst gets a private "Done"
        # barrier node: the analyst runs its tool loop in parallel on its own
        # message channel, then exits to its Done node. A single list-edge from
        # all Done nodes to the Bull Researcher makes the debate wait for every
        # analyst exactly once (a true fan-in barrier).
        for spec in plan.specs:
            workflow.add_node(spec.agent_node, analyst_factories[spec.key]())
            workflow.add_node(spec.done_node, _analyst_done)
            workflow.add_node(spec.tool_node, self.tool_nodes[spec.key])

        # Add other nodes
        workflow.add_node("Bull Researcher", bull_researcher_node)
        workflow.add_node("Bear Researcher", bear_researcher_node)
        workflow.add_node("Research Manager", research_manager_node)
        workflow.add_node("Scenario Analyst", scenario_analyst_node)
        workflow.add_node("Trader", trader_node)
        workflow.add_node("Aggressive Analyst", aggressive_analyst)
        workflow.add_node("Neutral Analyst", neutral_analyst)
        workflow.add_node("Conservative Analyst", conservative_analyst)
        workflow.add_node("Devil's Advocate", devils_advocate_node)
        workflow.add_node("Portfolio Manager", portfolio_manager_node)
        workflow.add_node("Position Sizer", position_sizer_node)

        # Define edges
        # Fan out: every analyst starts in parallel from START, runs its own
        # tool-call loop on a private message channel, then exits to its Done
        # node. The Bull Researcher joins on all Done nodes (barrier) so the
        # debate begins only after every analyst has finished.
        done_nodes = []
        for spec in plan.specs:
            workflow.add_edge(START, spec.agent_node)
            workflow.add_conditional_edges(
                spec.agent_node,
                getattr(self.conditional_logic, f"should_continue_{spec.key}"),
                [spec.tool_node, spec.done_node],
            )
            workflow.add_edge(spec.tool_node, spec.agent_node)
            done_nodes.append(spec.done_node)

        # Fan in: the Bull Researcher waits for every analyst's Done node.
        workflow.add_edge(done_nodes, "Bull Researcher")

        # Add remaining edges
        workflow.add_conditional_edges(
            "Bull Researcher",
            self.conditional_logic.should_continue_debate,
            {
                "Bear Researcher": "Bear Researcher",
                "Research Manager": "Research Manager",
            },
        )
        workflow.add_conditional_edges(
            "Bear Researcher",
            self.conditional_logic.should_continue_debate,
            {
                "Bull Researcher": "Bull Researcher",
                "Research Manager": "Research Manager",
            },
        )
        # The Scenario Analyst quantifies bull/base/bear outcomes between the
        # Research Manager's synthesis and the Trader's plan.
        workflow.add_edge("Research Manager", "Scenario Analyst")
        workflow.add_edge("Scenario Analyst", "Trader")
        workflow.add_edge("Trader", "Aggressive Analyst")
        workflow.add_conditional_edges(
            "Aggressive Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Conservative Analyst": "Conservative Analyst",
                "Devil's Advocate": "Devil's Advocate",
            },
        )
        workflow.add_conditional_edges(
            "Conservative Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Neutral Analyst": "Neutral Analyst",
                "Devil's Advocate": "Devil's Advocate",
            },
        )
        workflow.add_conditional_edges(
            "Neutral Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Aggressive Analyst": "Aggressive Analyst",
                "Devil's Advocate": "Devil's Advocate",
            },
        )

        # The Devil's Advocate red-teams the emerging decision, then the Portfolio
        # Manager finalises it, and the Position Sizer turns the rating into a
        # placeable order before the graph ends.
        workflow.add_edge("Devil's Advocate", "Portfolio Manager")
        workflow.add_edge("Portfolio Manager", "Position Sizer")
        workflow.add_edge("Position Sizer", END)

        return workflow
