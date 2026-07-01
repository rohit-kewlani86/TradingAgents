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
| Position Sizing Agent | actionable | Decision node after the Portfolio Manager (`PM → Position Sizer → END`). Converts the rating into a placeable order — size %, entry, ATR-based stop, target, risk/reward. Structured output (`PositionSizingPlan`). Consumes Technical ATR + Macro VIX regime + risk-debate conviction. Always on. No new data vendor. |
| Devil's Advocate / Red Team | accuracy | Node between the risk debate and the Portfolio Manager (`risk debate → Devil's Advocate → PM → Position Sizer → END`). Pre-mortem stress-test of the emerging consensus for groupthink; the PM must address its critique. Deep tier, free-text prose. Always on. No new data vendor. |

## Tier 1 — build next (no new data, high leverage)

### 1. Scenario Analyst — *accuracy + actionable* — RECOMMENDED NEXT
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
