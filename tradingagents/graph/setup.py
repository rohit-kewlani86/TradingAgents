# TradingAgents/graph/setup.py

from typing import Any, Dict
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from tradingagents.agents import *
from tradingagents.agents.utils.agent_states import AgentState

from .conditional_logic import ConditionalLogic


def _analyst_done(state):
    """No-op barrier node marking an analyst's tool loop as finished.

    Reports are written to state by the analyst itself; this node only
    exists as a fan-in synchronization point for the Bull Researcher.
    """
    return {}


class GraphSetup:
    """Handles the setup and configuration of the agent graph."""

    def __init__(
        self,
        quick_thinking_llm: Any,
        deep_thinking_llm: Any,
        tool_nodes: Dict[str, ToolNode],
        conditional_logic: ConditionalLogic,
        company_mode: str = "listed",
    ):
        """Initialize with required components."""
        self.quick_thinking_llm = quick_thinking_llm
        self.deep_thinking_llm = deep_thinking_llm
        self.tool_nodes = tool_nodes
        self.conditional_logic = conditional_logic
        self.company_mode = company_mode

    def setup_graph(
        self,
        selected_analysts=["market", "social", "news", "fundamentals", "technical", "macro"],
    ):
        """Set up and compile the agent workflow graph.

        Args:
            selected_analysts (list): List of analyst types to include. Options are:
                - "market": Market analyst (or Valuation in pre-IPO mode)
                - "social": Social media analyst
                - "news": News analyst
                - "fundamentals": Fundamentals analyst
                - "technical": Technical analyst (entry/exit timing; skipped in pre-IPO mode)
                - "macro": Macro/regime analyst (top-down rates/vol/dollar/sector context)
        """
        if len(selected_analysts) == 0:
            raise ValueError("Trading Agents Graph Setup Error: no analysts selected!")

        # Create analyst nodes
        analyst_nodes = {}
        tool_nodes = {}

        if "market" in selected_analysts:
            # In pre-IPO mode there is no price history, so the technical
            # Market Analyst is replaced by the Pre-IPO Valuation Analyst.
            # Both write the same ``market_report`` slot, so downstream wiring
            # (node label, tool loop, conditional edge) is unchanged.
            if self.company_mode == "pre_ipo":
                analyst_nodes["market"] = create_valuation_analyst(
                    self.quick_thinking_llm
                )
            else:
                analyst_nodes["market"] = create_market_analyst(
                    self.quick_thinking_llm
                )
            tool_nodes["market"] = self.tool_nodes["market"]

        if "social" in selected_analysts:
            analyst_nodes["social"] = create_social_media_analyst(
                self.quick_thinking_llm
            )
            tool_nodes["social"] = self.tool_nodes["social"]

        if "news" in selected_analysts:
            analyst_nodes["news"] = create_news_analyst(
                self.quick_thinking_llm
            )
            tool_nodes["news"] = self.tool_nodes["news"]

        if "fundamentals" in selected_analysts:
            analyst_nodes["fundamentals"] = create_fundamentals_analyst(
                self.quick_thinking_llm
            )
            tool_nodes["fundamentals"] = self.tool_nodes["fundamentals"]

        if "technical" in selected_analysts and self.company_mode != "pre_ipo":
            analyst_nodes["technical"] = create_technical_analyst(
                self.quick_thinking_llm
            )
            tool_nodes["technical"] = self.tool_nodes["technical"]

        if "macro" in selected_analysts:
            # Macro/regime context applies in both listed and pre-IPO mode, so
            # unlike Technical it is not gated on company_mode.
            analyst_nodes["macro"] = create_macro_analyst(self.quick_thinking_llm)
            tool_nodes["macro"] = self.tool_nodes["macro"]

        # Create researcher and manager nodes
        bull_researcher_node = create_bull_researcher(self.quick_thinking_llm)
        bear_researcher_node = create_bear_researcher(self.quick_thinking_llm)
        research_manager_node = create_research_manager(self.deep_thinking_llm)
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
        # barrier node: the analyst runs its tool loop in parallel, then exits
        # to its Done node. A single list-edge from all Done nodes to the Bull
        # Researcher makes the debate wait for every analyst to finish exactly
        # once (a true fan-in barrier). Routing the analysts straight to the
        # Bull Researcher instead would re-trigger it as each analyst finishes,
        # colliding with the debate's writes to investment_debate_state.
        for analyst_type, node in analyst_nodes.items():
            workflow.add_node(f"{analyst_type.capitalize()} Analyst", node)
            workflow.add_node(f"tools_{analyst_type}", tool_nodes[analyst_type])
            workflow.add_node(f"{analyst_type.capitalize()} Done", _analyst_done)

        # Add other nodes
        workflow.add_node("Bull Researcher", bull_researcher_node)
        workflow.add_node("Bear Researcher", bear_researcher_node)
        workflow.add_node("Research Manager", research_manager_node)
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
        for analyst_type in selected_analysts:
            current_analyst = f"{analyst_type.capitalize()} Analyst"
            current_tools = f"tools_{analyst_type}"
            current_done = f"{analyst_type.capitalize()} Done"

            workflow.add_edge(START, current_analyst)
            workflow.add_conditional_edges(
                current_analyst,
                getattr(self.conditional_logic, f"should_continue_{analyst_type}"),
                [current_tools, current_done],
            )
            workflow.add_edge(current_tools, current_analyst)
            done_nodes.append(current_done)

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
        workflow.add_edge("Research Manager", "Trader")
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
