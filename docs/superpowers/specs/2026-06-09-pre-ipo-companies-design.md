# Pre-IPO Company Analysis — Design

Date: 2026-06-09
Status: Approved (Approach A, phased build)

## Problem

The pipeline assumes a **listed ticker with price history**. The Market/Technical
Analyst runs on OHLCV + indicators (MACD/RSI), fundamentals pull from 10-K/10-Q,
insider data is SEC-sourced, and the reflection loop measures realised return vs
SPY from yfinance. A pre-IPO company (e.g. SpaceX) has none of that: no ticker,
no price, often no public filings, no exchange.

## Decisions (from brainstorming)

1. **Output**: reuse the BUY/SELL/HOLD decision schema unchanged, reinterpreted as
   *Subscribe / Wait / Skip* for the upcoming IPO. No schema changes downstream.
2. **Target**: the full spectrum from rumoured-IPO to S-1-filed; degrade gracefully
   on whatever data is available.
3. **Data sources** (layered): SEC EDGAR S-1/F-1 adapter, web/news research, and a
   funding-data API (Crunchbase-style). No manual dossier.
4. **Detection**: explicit CLI pre-IPO mode; the user enters a company name.
5. **Market Analyst**: repurposed into a **Pre-IPO Market & Valuation Analyst**
   (funding-round valuations, secondary-market marks, comparable public multiples,
   proposed IPO price range). Keeps the 4-analyst shape.
6. **Reflection**: log the decision as *pending*; resolve realised return only once
   the company lists (a `listed_ticker` becomes resolvable on yfinance).

## Approach A — Vendor-routing extension

A `company_mode` (`listed` | `pre_ipo`) flows from config → `AgentState`. The
existing data-layer router (`route_to_vendor` / `get_vendor` in
`dataflows/interface.py`) already selects a vendor per tool; we extend it so that
in `pre_ipo` mode the data tools resolve to **pre-IPO adapters**. The graph already
builds from a selectable analyst set, so we swap the Market Analyst node + its
ToolNode for the Valuation Analyst in pre-IPO mode. Everything downstream (Bull/Bear
debate, Trader, Risk team, Portfolio Manager, decision schema, logging) is unchanged.

### Components

- **Config** (`default_config.py`): `company_mode: "listed"`, `pre_ipo_company: None`.
  `pre_ipo_company` is `{"name", "cik"?, "listed_ticker"?}`.
- **State** (`agent_states.py`, `propagation.py`): add `company_mode` to `AgentState`
  and `create_initial_state`.
- **Routing** (`interface.py`): a `pre_ipo` vendor. `get_vendor` returns `pre_ipo`
  when `company_mode == "pre_ipo"`. New category `valuation_data` + method
  `get_valuation`. Methods with no `pre_ipo` impl (e.g. price/indicators) simply
  aren't offered to the valuation analyst.
- **Adapters** (`dataflows/preipo.py` + `dataflows/edgar.py`):
  - `get_fundamentals` → EDGAR S-1/F-1 financials when a filing exists; else a
    funding-derived summary; else a clear "no public financials" report.
  - `get_news` → web/news research; key-gated, graceful when no key.
  - `get_valuation` → funding rounds + secondary marks + comps; key-gated, graceful.
  - `get_insider_transactions` → "not applicable pre-IPO" report.
  - EDGAR adapter is real (free SEC API), unit-tested against mocked HTTP.
  - Crunchbase / web-search adapters are real code paths, env-key-gated, and degrade
    gracefully (informative "unavailable" text) when the key is absent — unit-tested
    with mocked HTTP. They cannot be live-verified without paid keys.
- **Valuation Analyst** (`agents/analysts/valuation_analyst.py`): factory
  `create_valuation_analyst(llm)`, mirrors the market analyst node contract (writes
  `market_report`), but is prompted for pre-IPO valuation and bound to
  `get_valuation`, `get_fundamentals`, `get_news`.
- **Graph wiring** (`graph/setup.py`, `trading_graph.py`): in `pre_ipo` mode the
  `market` slot uses the valuation analyst + a valuation ToolNode.
- **Reflection** (`trading_graph._resolve_pending_entries`): when `company_mode ==
  pre_ipo` and no `listed_ticker` resolves on yfinance, skip resolution (stay
  pending). When a `listed_ticker` resolves, resolve normally.
- **CLI** (`cli/main.py`, `cli/utils.py`): a pre-IPO prompt/flag; collect company
  name (+ optional CIK / listed ticker); set `company_mode` + `pre_ipo_company`.

### Data flow (pre-IPO run)

CLI sets `company_mode=pre_ipo` + `pre_ipo_company` → `TradingAgentsGraph` builds the
graph with the Valuation Analyst in the `market` slot → analysts (Valuation, Social,
News, Fundamentals) gather via pre-IPO adapters → Bull/Bear debate → Trader → Risk →
Portfolio Manager emits Subscribe/Wait/Skip → logged as pending → resolved once listed.

### Error handling / degradation

Every pre-IPO adapter returns informative text rather than raising when data is
absent or a key is missing, so the agents always receive an explicit signal and the
pipeline never blocks. Ticker/name still flows through `safe_ticker_component` before
any filesystem use.

### Testing

Offline, deterministic. Routing, mode plumbing, analyst node contract, graph swap,
and reflection-skip are unit-tested with no network. EDGAR + key-gated adapters are
tested against mocked HTTP responses. No test hits a live API.

### Phasing

1. Mode plumbing + routing + valuation analyst + graph swap + reflection-skip (backbone).
2. EDGAR S-1 adapter (real).
3. Web/news + funding adapters (key-gated, graceful).
4. CLI pre-IPO mode.
