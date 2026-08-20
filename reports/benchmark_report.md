# Benchmark Report — Single-Agent vs Multi-Agent

> Quality is a transparent heuristic proxy unless a human/LLM judge is added. Final submission should record the provider used.

| Run | Latency (s) | Tokens | Cost (USD) | Quality /10 | Citation cov. | Failure | Sources | Routes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| single-agent | 15.498 | 5010 |  | 3.50 | 0% | 0% | 6 | 2 |
| multi-agent | 129.326 | 13197 |  | 9.50 | 100% | 0% | 6 | 5 |
| single-agent | 93.102 | 2969 |  | 6.50 | 50% | 0% | 6 | 2 |
| multi-agent | 231.475 | 14731 |  | 8.00 | 75% | 0% | 6 | 5 |
| single-agent | 55.352 | 3953 |  | 9.50 | 100% | 0% | 6 | 2 |
| multi-agent | 154.432 | 14578 |  | 9.00 | 100% | 0% | 6 | 5 |
| single-agent | 64.722 | 4716 |  | 9.25 | 100% | 0% | 6 | 2 |
| multi-agent | 217.664 | 15741 |  | 6.50 | 50% | 0% | 6 | 5 |
| single-agent | 98.158 | 5002 |  | 9.50 | 100% | 0% | 6 | 2 |
| multi-agent | 129.329 | 14241 |  | 9.00 | 100% | 0% | 6 | 5 |
| single-agent | 62.200 | 5240 |  | 9.50 | 100% | 0% | 6 | 2 |
| multi-agent | 198.668 | 16283 |  | 9.50 | 100% | 0% | 6 | 5 |

## Aggregate

- **single-agent**: mean latency 64.839s; mean quality 7.96/10; mean citation coverage 75%; mean tokens 4482; failure rate 0%.
- **multi-agent**: mean latency 176.816s; mean quality 8.58/10; mean citation coverage 88%; mean tokens 14795; failure rate 0%.

## Interpretation

- Multi-agent is justified only if its quality/citation gains compensate for extra token, latency, handoff, and integration cost.
- The single-agent baseline is intentionally retained because narrow tasks may not benefit from decomposition.
- Failure analysis should inspect the saved route/event trace rather than infer causality from the final answer alone.

## Failure Mode and Fix

**Failure mode:** duplicated or weak evidence can be amplified across handoffs and look like consensus.

**Fix:** the Researcher preserves source IDs, the Analyst explicitly compares evidence quality, the Writer must cite source IDs, and the Critic checks citation validity/synthetic labeling. Supervisor routing is bounded by `MAX_ITERATIONS` and provider calls use bounded retries/timeouts.

## Runtime Provider

`LLM_PROVIDER=openai`. If this is `offline`, this report is a deterministic validation run and must be rerun with Groq/OpenAI before final submission.
