import os

_TRADINGAGENTS_HOME = os.path.join(os.path.expanduser("~"), ".tradingagents")

DEFAULT_CONFIG = {
    "project_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
    "results_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", os.path.join(_TRADINGAGENTS_HOME, "logs")),
    "data_cache_dir": os.getenv("TRADINGAGENTS_CACHE_DIR", os.path.join(_TRADINGAGENTS_HOME, "cache")),
    "memory_log_path": os.getenv("TRADINGAGENTS_MEMORY_LOG_PATH", os.path.join(_TRADINGAGENTS_HOME, "memory", "trading_memory.md")),
    # Optional cap on the number of resolved memory log entries. When set,
    # the oldest resolved entries are pruned once this limit is exceeded.
    # Pending entries are never pruned. None disables rotation entirely.
    "memory_log_max_entries": None,
    # Company mode: "listed" (default, public equity) or "pre_ipo" (private/IPO-ready).
    # In pre_ipo mode the data tools route to pre-IPO adapters and the Market
    # Analyst is replaced by the Pre-IPO Market & Valuation Analyst.
    "company_mode": "listed",
    # Pre-IPO company identity, used only when company_mode == "pre_ipo".
    # Shape: {"name": str, "cik": str | None, "listed_ticker": str | None}.
    # "listed_ticker" lets the reflection loop resolve realised return once the
    # company actually lists; until then its decisions stay pending.
    "pre_ipo_company": None,
    # LLM settings
    "llm_provider": "openai",
    "deep_think_llm": "gpt-5.4",
    "quick_think_llm": "gpt-5.4-mini",
    # When None, each provider's client falls back to its own default endpoint
    # (api.openai.com for OpenAI, generativelanguage.googleapis.com for Gemini, ...).
    # The CLI overrides this per provider when the user picks one. Keeping a
    # provider-specific URL here would leak (e.g. OpenAI's /v1 was previously
    # being forwarded to Gemini, producing malformed request URLs).
    "backend_url": None,
    # Provider-specific thinking configuration (applies to the deep tier).
    "google_thinking_level": None,      # "high", "minimal", etc.
    "openai_reasoning_effort": None,    # "medium", "high", "low"
    "anthropic_effort": None,           # "high", "medium", "low"
    # Quick-tier overrides: analysts/debaters rarely need extended reasoning,
    # so a lower thinking budget here cuts latency without touching the deep
    # judges. Each falls back to its global value above when None.
    "quick_think_thinking_level": None,
    "quick_think_reasoning_effort": None,
    "quick_think_effort": None,
    # Per-tier temperature. 0.0 pins the deep-tier judges to deterministic
    # output; 0.3 keeps analyst prose varied while still reducing run-to-run
    # variance. Providers that don't support temperature (e.g. o-series with
    # fixed temp=1) silently ignore this value in their client.
    "deep_think_temperature": 0.0,
    "quick_think_temperature": 0.3,
    # Per-tier output caps (None = provider default). Bounds runaway responses
    # that would otherwise dominate wall-clock; keep the deep cap generous so a
    # judge's thinking + answer always fit.
    "deep_think_max_tokens": None,
    "quick_think_max_tokens": None,
    # Checkpoint/resume: when True, LangGraph saves state after each node
    # so a crashed run can resume from the last successful step.
    "checkpoint_enabled": False,
    # Output language for analyst reports and final decision
    # Internal agent debate stays in English for reasoning quality
    "output_language": "English",
    # Debate and discussion settings. Two rounds give each side a rebuttal turn,
    # building more stable consensus before the judges weigh in.
    "max_debate_rounds": 2,
    "max_risk_discuss_rounds": 2,
    "max_recur_limit": 100,
    # Data vendor configuration
    # Category-level configuration (default for all tools in category)
    "data_vendors": {
        "core_stock_apis": "yfinance",       # Options: alpha_vantage, yfinance
        "technical_indicators": "yfinance",  # Options: alpha_vantage, yfinance
        "fundamental_data": "yfinance",      # Options: alpha_vantage, yfinance
        "news_data": "yfinance",             # Options: alpha_vantage, yfinance
    },
    # Tool-level configuration (takes precedence over category-level)
    "tool_vendors": {
        # Example: "get_stock_data": "alpha_vantage",  # Override category default
    },
}
