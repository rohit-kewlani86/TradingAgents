from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create a custom config
config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "google"
config["deep_think_llm"] = "gemini-2.5-pro"
config["quick_think_llm"] = "gemini-2.5-flash"
# Both tiers reason fully. An A/B eval showed disabling quick-tier thinking
# saved ~15s but cut analysis quality ~35% (the Fundamentals analyst lost its
# year-over-year statement deep dive), so the quick-tier override is left off.
config["google_thinking_level"] = "high"
# Cap output to stop a runaway analyst response (~60k tokens) from dominating
# wall-clock. This is the real win: it tames the runaway with no quality loss.
# Quick reports are 1-3k tokens; the deep judges keep ample room.
config["quick_think_max_tokens"] = 8192
config["deep_think_max_tokens"] = 32768
config["max_debate_rounds"] = 1  # Increase debate rounds

# Configure data vendors (default uses yfinance, no extra API keys needed)
config["data_vendors"] = {
    "core_stock_apis": "yfinance",           # Options: alpha_vantage, yfinance
    "technical_indicators": "yfinance",      # Options: alpha_vantage, yfinance
    "fundamental_data": "yfinance",          # Options: alpha_vantage, yfinance
    "news_data": "yfinance",                 # Options: alpha_vantage, yfinance
}

# Initialize with custom config
ta = TradingAgentsGraph(debug=True, config=config)

# forward propagate
_, decision = ta.propagate("NVDA", "2024-05-10")
print(decision)

# Memorize mistakes and reflect
# ta.reflect_and_remember(1000) # parameter is the position returns
