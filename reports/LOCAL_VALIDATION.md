# Local Validation

## Codelab self-check (step 5)

| Check | Result |
|---|---|
| `ruff check src tests scripts` | **All checks passed!** |
| `pytest` | **6 passed** |
| `run-baseline` | **PASS** |
| `run-multi` | **PASS** — no "Expected TODO" panel |
| `grep -R "TODO(student)" -n src \| wc -l` | **0** |
| trace JSON + HTML generation | **PASS** |

## Final provider benchmark

`python scripts/run_submission.py` reports **SUBMISSION_GATE: PASS**.

The benchmark records `LLM_PROVIDER=openai` against `openai/gpt-oss-120b`, served
through OpenRouter via `OPENAI_BASE_URL`. The Groq path is unchanged and still
supported; it was not used for the final run because its free tier caps at 200k
tokens per day while a full 6-query benchmark needs roughly 111k.

| Metric | Single-agent | Multi-agent |
|---|---:|---:|
| Quality | 7.96/10 | 8.58/10 |
| Citation coverage | 75% | 88% |
| Mean tokens | 4,482 | 14,795 |
| Mean latency | 64.8s | 176.8s |
| Failure rate | 0% | 0% |

Offline mode remains available for deterministic tests only, and
`run_submission.py` refuses it.
