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
| Scenario Analyst | accuracy + actionable | Node between the Research Manager and the Trader (`Research Manager → Scenario Analyst → Trader`). Quantified bull/base/bear price targets with probabilities and a probability-weighted expected value (computed deterministically in the renderer). Structured output (`ScenarioAnalysis`); the Trader and Portfolio Manager both weigh the EV. Deep tier, always on. No new data vendor. |

## Tier 1 — build next (no new data, high leverage)

_(empty — the Tier 1 candidates, Scenario Analyst included, have shipped.)_

## Tier 3 — valuable but data-gated (the vendor is the hard part)

### Peer Comparables — *coverage*
Relative valuation vs. a peer set. yfinance has partial peer/multiples data;
moderate wiring.

### Short Interest — *coverage*
Squeeze/sentiment signal. Needs a short-interest feed (FINRA/exchange).

### Options Flow — *coverage*
Smart-money positioning. Needs an options-chain/flow vendor — heaviest lift.

## Deprioritized (overlap with shipped work)

- **Exit Strategy** — the Technical Analyst already owns stops/targets.

## Separate structural track (highest architectural value, highest effort)

- **Portfolio-level agent** — every run analyzes one ticker in isolation, with
  no reasoning about correlation, concentration, or fit with existing holdings.
  Not "another analyst" — needs a portfolio-state concept threaded through the
  graph.

## Infra / reliability backlog

Not analysts, but adjacent reliability work surfaced while building the above:

- **Extend live-model discovery to Google / Anthropic** — `live_models` currently
  covers OpenAI-compatible `/v1/models`; Gemini and Claude expose their own
  list endpoints in a different shape.
- **Config flag to disable per-tier fallback** — cross-model fallback is always
  on; a `model_fallback_enabled` toggle would let users pin a single model.
- **Portfolio-state groundwork** — prerequisite for the portfolio-level agent.

## Standard build flow (per shipped agents)

1. **Spike** — confirm data reachability through the existing layer before wiring.
2. **Wire** the integration points (TDD, red→green per step):
   state channel + report field → factory → barrel export → conditional →
   ToolNode → state seed → graph registration → CLI (models/utils/main).
   (A mid-pipeline synthesis node like the Scenario Analyst skips the analyst
   ToolNode/CLI-checkbox points and is wired as an always-on node instead.)
3. **Thread** the new report into downstream consumers (e.g. Bull/Bear, Trader,
   Portfolio Manager prompts).
4. **Regression** — full suite green.
