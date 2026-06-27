# NVIDIA LLM Provider — Design

**Date:** 2026-06-27
**Status:** Approved, pending implementation

## Goal

Add NVIDIA as a selectable LLM provider so the framework can run inference
through the NVIDIA API, on equal footing with the existing providers.

## Background

NVIDIA's hosted inference API (`https://integrate.api.nvidia.com/v1`) speaks the
OpenAI-compatible Chat Completions protocol. The codebase already routes every
OpenAI-compatible provider through a single `OpenAIClient`
(`tradingagents/llm_clients/openai_client.py`) listed in `_OPENAI_COMPATIBLE`
(`factory.py`). Adding NVIDIA therefore needs no new client class — it mirrors
the DeepSeek/Qwen/GLM wiring exactly.

## Non-goals

- No changes to agent logic, the data layer, or other providers.
- No NVIDIA-specific reasoning/thinking knobs (no provider subclass).
- No dynamic model fetching (unlike OpenRouter).

## Design

### Provider wiring

1. `factory.py` — add `"nvidia"` to `_OPENAI_COMPATIBLE` so the factory returns
   an `OpenAIClient(provider="nvidia")`.
2. `openai_client.py` — add to `_PROVIDER_CONFIG`:
   `"nvidia": ("https://integrate.api.nvidia.com/v1", "NVIDIA_API_KEY")`.
   An explicit `base_url` on the client still takes precedence (corporate NIM
   gateways), consistent with the existing override behavior.

### Model catalog

`model_catalog.py` — add an `"nvidia"` block. NIM model IDs are namespaced
(`meta/...`, `deepseek-ai/...`, `nvidia/...`, `qwen/...`, `mistralai/...`).

- **quick:** Nemotron Nano 8B, Llama 3.3 70B Instruct, Qwen2.5 Coder 32B,
  Mistral Small 24B, Custom model ID
- **deep:** Nemotron Super 49B, DeepSeek-R1, Llama 3.1 405B Instruct,
  Nemotron 70B, QwQ 32B, Custom model ID

### Validation

NVIDIA stays out of the lenient set in `validators.py` (like DeepSeek/Qwen/GLM):
unknown models warn but do not block, and the `Custom model ID` entry lets users
supply any model string.

### CLI

`cli/utils.py` — add `("NVIDIA", "nvidia", "https://integrate.api.nvidia.com/v1")`
to the provider selection menu.

### Tests and docs

- `tests/conftest.py` — add `NVIDIA_API_KEY` to the autouse placeholder fixture
  so the suite stays offline-safe.
- `.env.example` / `.env.enterprise.example` — document `NVIDIA_API_KEY`.

## Acceptance criteria

- `create_llm_client("nvidia", model)` returns an `OpenAIClient` with
  `provider == "nvidia"`.
- `OpenAIClient("nvidia", ...).get_llm()` resolves base URL
  `https://integrate.api.nvidia.com/v1` and reads `NVIDIA_API_KEY` from the env.
- `get_known_models()` includes an `"nvidia"` entry with the curated models.
- The CLI provider menu lists NVIDIA.
- `pytest` passes with no real API keys present.

## TDD plan

Failing-test-first for each behavior unit:

1. factory returns `OpenAIClient(provider="nvidia")` for `"nvidia"`.
2. `get_llm()` resolves the NVIDIA base URL and API key from env.
3. catalog / `get_known_models()` includes nvidia models.

The CLI menu entry and `.env` docs are pure config — test-exempt per the
project's TDD rule.

## Security note

The API key is read from `NVIDIA_API_KEY` at runtime; it is never stored in the
repo. (A key pasted in chat during planning should be rotated.)
