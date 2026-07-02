# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install (editable) with all dependencies
pip install -e .

# Run the interactive CLI
tradingagents              # installed console script (cli.main:app)
python -m cli.main         # run from source
./start.sh                 # wrapper; --cli (default), --script (runs main.py), --install

# Run the example script (edit main.py to change ticker/provider/date)
python main.py

# Tests (pytest config lives in pyproject.toml; testpaths=tests)
pytest                                          # full suite
pytest tests/test_signal_processing.py          # single file
pytest tests/test_signal_processing.py::test_x  # single test
pytest -m unit                                  # by marker: unit | integration | smoke

# Docker
docker compose run --rm tradingagents
docker compose --profile ollama run --rm tradingagents-ollama   # local models
```

Tests never require real API keys: `tests/conftest.py` injects placeholder values for every provider key (autouse) and provides a `mock_llm_client` fixture. Keep tests offline — do not add tests that hit live LLM or market-data APIs without an `integration` marker.

## Architecture

TradingAgents is a multi-agent LLM trading framework built on **LangGraph**. A run analyzes one ticker on one date and produces a BUY/SELL/HOLD decision by passing state through a directed graph of agent nodes that mirror a trading firm.

### The agent pipeline (graph topology)

Defined in [tradingagents/graph/setup.py](tradingagents/graph/setup.py). The graph is a `StateGraph(AgentState)` wired in this order:

1. **Analysts** (selectable subset of `market`, `social`, `news`, `fundamentals`) run sequentially. Each analyst loops with its own `ToolNode` (conditional edge → tools → back to analyst) until it stops calling tools, then a `Msg Clear` node wipes the message history before the next analyst. Tool-call looping is governed by `should_continue_*` in [conditional_logic.py](tradingagents/graph/conditional_logic.py).
2. **Researcher debate** — Bull ↔ Bear researchers alternate for `max_debate_rounds`, then **Research Manager** judges.
3. **Trader** composes a trade plan.
4. **Risk debate** — Aggressive ↔ Conservative ↔ Neutral cycle for `max_risk_discuss_rounds`, then **Portfolio Manager** issues the final decision → `END`.

`TradingAgentsGraph` in [trading_graph.py](tradingagents/graph/trading_graph.py) is the orchestrator: it builds LLM clients, tool nodes, the graph, and runs `.propagate(ticker, date)`. The compiled graph (`self.graph`) is recompiled with a checkpointer per-run only when `checkpoint_enabled`.

### Shared state

All nodes read/write a single `AgentState` (a LangGraph `MessagesState` subclass) defined in [agent_states.py](tradingagents/agents/utils/agent_states.py). Each agent fills its slice: `market_report`, `sentiment_report`, `news_report`, `fundamentals_report`, `investment_debate_state`, `trader_investment_plan`, `risk_debate_state`, `final_trade_decision`. Agents are **factory functions** (`create_<agent>(llm)`) returning a node callable; they are barrel-exported via `from tradingagents.agents import *`.

### Structured output

Trader, Research Manager, and Portfolio Manager emit Pydantic-typed output via [structured.py](tradingagents/agents/utils/structured.py) (`bind_structured` + render-to-markdown). Schemas live in [agents/schemas.py](tradingagents/agents/schemas.py). The pattern always falls back to free-text `llm.invoke` if a provider lacks structured-output support or returns malformed JSON, so the pipeline never blocks.

### LLM provider abstraction

[tradingagents/llm_clients/](tradingagents/llm_clients/) — `create_llm_client(provider, model, base_url, **kwargs)` ([factory.py](tradingagents/llm_clients/factory.py)) returns a `BaseLLMClient`; call `.get_llm()` for the LangChain chat model. Providers are imported **lazily** inside the factory so importing it (e.g. during test collection) never pulls heavy SDKs or fails on missing keys. OpenAI/xAI/DeepSeek/Qwen/GLM/Ollama/OpenRouter all share `OpenAIClient` (OpenAI-compatible API); Anthropic, Google, and Azure have dedicated clients. Provider-specific "thinking"/reasoning knobs are mapped in `_get_provider_kwargs` (`google_thinking_level`, `openai_reasoning_effort`, `anthropic_effort`). `model_catalog.py` is the unified model list.

Two LLM tiers are used throughout: `deep_think_llm` (Research Manager, Portfolio Manager — heavy reasoning) and `quick_think_llm` (everything else).

### Data layer (vendor-routed)

[tradingagents/dataflows/](tradingagents/dataflows/) — the agent-facing tools (`get_stock_data`, `get_indicators`, `get_fundamentals`, `get_balance_sheet`, `get_cashflow`, `get_income_statement`, `get_news`, `get_global_news`, `get_insider_transactions`) live under [agents/utils/](tradingagents/agents/utils/) and are grouped into ToolNodes per analyst. Each tool routes to a vendor implementation (`yfinance` or `alpha_vantage`) based on `data_vendors` (category-level) and `tool_vendors` (tool-level override) in config. [interface.py](tradingagents/dataflows/interface.py) holds `TOOLS_CATEGORIES` and routing.

### Configuration

[default_config.py](tradingagents/default_config.py) defines `DEFAULT_CONFIG`. Copy it and override (`config = DEFAULT_CONFIG.copy()`). A **module-global** config in [dataflows/config.py](tradingagents/dataflows/config.py) (`set_config`/`get_config`) is what the data tools read at call time — `TradingAgentsGraph.__init__` calls `set_config(self.config)` to sync it. Path defaults live under `~/.tradingagents/` and are overridable via env vars: `TRADINGAGENTS_RESULTS_DIR`, `TRADINGAGENTS_CACHE_DIR`, `TRADINGAGENTS_MEMORY_LOG_PATH`.

### Persistence

- **Decision log** (always on): each run appends its decision to `~/.tradingagents/memory/trading_memory.md` via `TradingMemoryLog` ([agents/utils/memory.py](tradingagents/agents/utils/memory.py)). On the next same-ticker run, `_resolve_pending_entries` fetches realized return (raw + alpha vs SPY), generates a reflection ([graph/reflection.py](tradingagents/graph/reflection.py)), and injects recent decisions/lessons into the Portfolio Manager prompt via `past_context`.
- **Checkpoint resume** (opt-in `checkpoint_enabled` / `--checkpoint`): LangGraph `SqliteSaver` per ticker at `~/.tradingagents/cache/checkpoints/<TICKER>.db` ([graph/checkpointer.py](tradingagents/graph/checkpointer.py)). `thread_id` keys on ticker+date so same date resumes, new date starts fresh; checkpoints clear on success.

### Security note

Tickers flow into filesystem paths (results dir, checkpoint DB). Always sanitize ticker path components with `safe_ticker_component` ([dataflows/utils.py](tradingagents/dataflows/utils.py)) before joining — see the existing call sites in `trading_graph._log_state`.
</content>
