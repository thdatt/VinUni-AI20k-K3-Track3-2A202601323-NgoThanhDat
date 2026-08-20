# Lab 20 Design — Multi-Agent Offline Research System

## Problem

Build a research assistant that answers long technical questions from the supplied 30-topic offline corpus, preserves evidence provenance, exposes intermediate state for debugging, and compares a single-agent baseline with a bounded multi-agent workflow.

## Why multi-agent?

The multi-agent design is used only where decomposition creates distinct work: the Researcher retrieves and records evidence, the Analyst evaluates evidence quality/conflicts, and the Writer synthesizes. The Supervisor is a deterministic router rather than another free-form LLM. A single-agent baseline remains first-class because narrow tasks may not justify coordination overhead.

## Agent roles

| Agent | Responsibility | Input | Output | Main failure mode |
|---|---|---|---|---|
| Supervisor | Inspect state and route bounded next step | ResearchState | route_history | looping / unnecessary calls |
| Researcher | Retrieve bounded offline evidence, preserve IDs | query | sources + research_notes | weak source selection / duplicated evidence |
| Analyst | Compare claims, evidence quality, conflicts | source ledger + research_notes | analysis_notes | false consensus / overgeneralization |
| Writer | Produce final grounded response | evidence + analysis | final_answer | unsupported claim / missing citation |
| Critic | Independently validate citation IDs and synthetic labeling | final_answer + source ledger | findings/errors | superficial agreement |

## Shared state

`ResearchState` keeps request, run_id, iteration, route_history, sources, research_notes, analysis_notes, final_answer, agent_results, trace, errors, token counters, and estimated cost. Provenance is retained inside each `SourceDocument.metadata.source_id`.

## Routing policy

```text
Supervisor
  ├─ no evidence → Researcher → Supervisor
  ├─ no analysis → Analyst → Supervisor
  ├─ no answer   → Writer → Supervisor
  ├─ answer + critic enabled → Critic → DONE
  └─ max_iterations → DONE with error
```

## Guardrails

- **Max iterations:** default 6.
- **Timeout:** provider client timeout default 90 s.
- **Retry:** bounded provider retry, default 3.
- **Fallback:** deterministic offline mode for tests only; it is rejected by the final submission gate.
- **Validation:** Pydantic schemas; citation ID validation; synthetic-source labeling check.
- **Search boundary:** no browser/web search is required; retrieval is limited to the supplied corpus.

## Benchmark plan

Run the same six queries through both architectures and record latency, total token usage, optional estimated provider cost, transparent quality proxy, citation coverage, failure rate, source count, and route count. The benchmark report explicitly notes that quality is a proxy unless externally judged.
