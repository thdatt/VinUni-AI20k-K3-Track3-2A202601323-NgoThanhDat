# Benchmark Report — Single-Agent vs Multi-Agent

> Quality is a transparent heuristic proxy unless a human/LLM judge is added. Final submission should record the provider used.

| Run | Latency (s) | Tokens | Cost (USD) | Quality /10 | Citation cov. | Failure | Sources | Routes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| single-agent | 80.135 | 4649 |  | 3.50 | 0% | 0% | 6 | 2 |
| multi-agent | 149.466 | 15263 |  | 6.50 | 50% | 0% | 6 | 5 |
| single-agent | 28.890 | 4760 |  | 3.50 | 0% | 0% | 6 | 2 |
| multi-agent | 131.993 | 12347 |  | 3.25 | 0% | 0% | 6 | 5 |
| single-agent | 29.718 | 4488 |  | 3.50 | 0% | 0% | 6 | 2 |
| multi-agent | 78.806 | 15932 |  | 3.50 | 0% | 0% | 6 | 5 |
| single-agent | 79.203 | 4983 |  | 3.25 | 0% | 0% | 6 | 2 |
| multi-agent | 132.738 | 12933 |  | 3.50 | 0% | 0% | 6 | 5 |
| single-agent | 69.443 | 4836 |  | 3.25 | 0% | 0% | 6 | 2 |
| multi-agent | 193.759 | 11416 |  | 5.00 | 25% | 0% | 6 | 5 |
| single-agent | 40.217 | 4734 |  | 3.25 | 0% | 0% | 6 | 2 |
| multi-agent | 115.064 | 15229 |  | 5.00 | 25% | 0% | 6 | 5 |

## Aggregate

- **single-agent**: mean latency 54.601s; mean quality 3.38/10; mean citation coverage 0%; mean tokens 4742; failure rate 0%.
- **multi-agent**: mean latency 133.638s; mean quality 4.46/10; mean citation coverage 17%; mean tokens 13853; failure rate 0%.

## Interpretation

- Multi-agent is justified only if its quality/citation gains compensate for extra token, latency, handoff, and integration cost.
- The single-agent baseline is intentionally retained because narrow tasks may not benefit from decomposition.
- Failure analysis should inspect the saved route/event trace rather than infer causality from the final answer alone.

## Failure Mode and Fix

**Failure mode:** duplicated or weak evidence can be amplified across handoffs and look like consensus.

**Fix:** the Researcher preserves source IDs, the Analyst explicitly compares evidence quality, the Writer must cite source IDs, and the Critic checks citation validity/synthetic labeling. Supervisor routing is bounded by `MAX_ITERATIONS` and provider calls use bounded retries/timeouts.

## Runtime Provider

`LLM_PROVIDER=openai`. If this is `offline`, this report is a deterministic validation run and must be rerun with Groq/OpenAI before final submission.
