# Lab 20 — Multi-Agent Research System (Completed)

Student: **Ngo Thanh Dat**

This completed implementation preserves the starter architecture but fills the student logic required by the Lab 20 guide: real-provider LLM abstraction, deterministic Supervisor routing, Researcher/Analyst/Writer agents, optional Critic, bounded workflow, offline corpus retrieval, trace artefacts, and a single-vs-multi benchmark.

## Architecture

```text
User Query
   |
   +---------------- Single-Agent baseline ----------------+
   |                                                        |
   v                                                        v
Supervisor -> Researcher -> Analyst -> Writer -> Critic -> Answer
                 |           |          |
                 +---- shared ResearchState + source IDs ----+
```

The uploaded `AI Agent Offline Research Corpus Benchmark v2` is extracted under `data/offline_corpus/`. It contains 30 topic JSON files and is the only retrieval source used by the default SearchClient.

## Why the offline corpus matters

The corpus explicitly says browser/web search should be disabled for this benchmark and final reports should cite embedded `document_id/source_id` or namespaced `article_id`. Synthetic sources retain `is_synthetic=true`; the Writer and Critic are instructed to preserve that distinction.

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev,llm]"
Copy-Item .env.example .env
```

Fill `.env`. Recommended if you already use Groq:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=...
GROQ_MODEL=openai/gpt-oss-120b
SEARCH_PROVIDER=offline
OFFLINE_CORPUS_PATH=data/offline_corpus
```

`OPENAI_API_KEY` is only needed when `LLM_PROVIDER=openai`.

`OPENAI_BASE_URL` points the OpenAI-compatible path at any such endpoint. Leave it
blank for real OpenAI; set it to reach OpenRouter, Together, or a local server:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-or-...
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=openai/gpt-oss-120b
```

The committed benchmark was produced through this path (OpenRouter serving
`openai/gpt-oss-120b`) because the Groq free tier caps at 200k tokens/day and a
full benchmark needs ~111k. The Groq path is unchanged and still supported.

## Deterministic local validation

No API key is required for unit tests:

```powershell
$env:LLM_PROVIDER="offline"
pytest
python -m multi_agent_research_lab.cli baseline --query "When is a multi-agent research system justified?"
python -m multi_agent_research_lab.cli multi-agent --query "When is a multi-agent research system justified?"
python scripts/run_benchmark.py
```

Offline mode is intentionally rejected by `scripts/run_submission.py`; it is only a test fallback, not the claimed final LLM benchmark.

## Final run

After filling a real provider in `.env`:

```powershell
python scripts/run_submission.py
```

The final gate:

1. refuses `LLM_PROVIDER=offline`;
2. runs pytest;
3. benchmarks identical queries through single and multi-agent;
4. writes `reports/benchmark_results.csv`;
5. writes `reports/benchmark_report.md`;
6. requires at least one HTML trace.

## Deliverables

- GitHub repo.
- `reports/benchmark_report.md`.
- `reports/benchmark_results.csv`.
- screenshot or link for a `reports/traces/*.html` trace.
- failure mode analysis inside the benchmark report.
- completed design: `docs/design.md`.
- exit ticket: `docs/exit_ticket.md`.

## Guardrails

- deterministic Supervisor routing;
- `MAX_ITERATIONS`;
- provider timeout;
- bounded retries;
- Pydantic input/state;
- shared provenance-rich state;
- citation validation;
- synthetic-source labeling check;
- local trace JSON + HTML;
- final submission gate refuses fake/offline benchmark mode.

## Submission safety

Never commit `.env`. Before pushing:

```powershell
git status --short
git check-ignore -v .env
python scripts/run_submission.py
```

Only push after `SUBMISSION_GATE: PASS`.
