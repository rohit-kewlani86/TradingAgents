# Agent Backlog

Prioritized backlog of analysts/agents proposed for the TradingAgents pipeline.

The key discriminator for effort is **whether an agent needs a new data vendor
wired into `tradingagents/dataflows/`**. Agents that ride the existing data
layer (`get_stock_data`, `get_indicators`, `get_global_news`, fundamentals
tools) are cheap; agents needing a new feed carry the vendor integration as the
dominant cost.

Each agent extends the platform along one of three axes:
- **Accuracy** — sharper reasoning over signals already gathered.
- **Actionable** — turn the rating into a placeable trade.
- **Coverage** — new input signals the current bottom-up analysts miss.

## Shipped

| Agent | Axis | Notes |
|---|---|---|
| Technical Analyst | actionable | Entry/exit timing, RSI/MACD/Bollinger/ATR, ATR-based stops/targets. Gated off in pre-IPO mode (no price history). |
| Macro / Regime Analyst | coverage | Top-down rates (`^TNX`), volatility (`^VIX`), dollar (`DX-Y.NYB`), market trend (`^GSPC`), sector rotation (sector ETFs). Runs in listed and pre-IPO mode. No new data vendor. |

## Tier 1 — build next (no new data, high leverage)

### 1. Position Sizing Agent — *actionable* — RECOMMENDED NEXT
Converts the Portfolio Manager's rating into a placeable order: position size +
stop distance. Both key inputs already exist — the Technical Analyst's ATR and
the Macro Analyst's VIX regime — so this cashes in the last two builds. New node
between the risk debate and the final decision. Zero new data.

### 2. Devil's Advocate / Red Team — *accuracy*
Bull and bear each argue to win their side; nobody stress-tests the *final*
decision for groupthink. A red-team node before the Portfolio Manager ("what
must be true for this to be wrong?"). Reinforces the determinism/variance work.
Zero new data.

## Tier 2 — solid, mostly no new data

### 3. Scenario Analyst — *accuracy + actionable*
Quantified bull/base/bear price targets with rough probabilities and expected
value. Distinct from the qualitative research debate (prose, not numbers). Rides
existing data. Scope the mandate carefully to avoid restating the debate.

## Tier 3 — valuable but data-gated (the vendor is the hard part)

### 4. Peer Comparables — *coverage*
Relative valuation vs. a peer set. yfinance has partial peer/multiples data;
moderate wiring.

### 5. Short Interest — *coverage*
Squeeze/sentiment signal. Needs a short-interest feed (FINRA/exchange).

### 6. Options Flow — *coverage*
Smart-money positioning. Needs an options-chain/flow vendor — heaviest lift.

## Deprioritized (overlap with shipped work)

- **Exit Strategy** — the Technical Analyst already owns stops/targets.

## Separate structural track (highest architectural value, highest effort)

- **Portfolio-level agent** — every run analyzes one ticker in isolation, with
  no reasoning about correlation, concentration, or fit with existing holdings.
  Not "another analyst" — needs a portfolio-state concept threaded through the
  graph.

## Standard build flow (per shipped agents)

1. **Spike** — confirm data reachability through the existing layer before wiring.
2. **Wire** the 8 integration points (TDD, red→green per step):
   state channel + report field → factory → barrel export → conditional →
   ToolNode → state seed → graph registration → CLI (models/utils/main).
3. **Thread** the new report into downstream consumers (e.g. Bull/Bear prompts).
4. **Regression** — full suite green.
