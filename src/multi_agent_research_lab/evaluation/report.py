"""Benchmark report rendering."""

from __future__ import annotations

from collections import defaultdict
from statistics import mean

from multi_agent_research_lab.core.schemas import BenchmarkMetrics


def render_markdown_report(metrics: list[BenchmarkMetrics]) -> str:
    lines = [
        "# Benchmark Report — Single-Agent vs Multi-Agent",
        "",
        "> Quality is a transparent heuristic proxy unless a human/LLM judge is added. "
        "Final submission should record the provider used.",
        "",
        "| Run | Latency (s) | Tokens | Cost (USD) | Quality /10 | Citation cov. | Failure | Sources | Routes |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in metrics:
        cost = "" if item.estimated_cost_usd is None else f"{item.estimated_cost_usd:.6f}"
        quality = "" if item.quality_score is None else f"{item.quality_score:.2f}"
        citation = "" if item.citation_coverage is None else f"{item.citation_coverage:.0%}"
        failure = "" if item.failure_rate is None else f"{item.failure_rate:.0%}"
        lines.append(
            f"| {item.run_name} | {item.latency_seconds:.3f} | {item.total_tokens} | {cost} "
            f"| {quality} | {citation} | {failure} | {item.source_count} | {item.route_count} |"
        )

    grouped: dict[str, list[BenchmarkMetrics]] = defaultdict(list)
    for item in metrics:
        grouped[item.run_name].append(item)

    lines += ["", "## Aggregate", ""]
    for run_name, items in grouped.items():
        lines.append(
            f"- **{run_name}**: mean latency {mean(x.latency_seconds for x in items):.3f}s; "
            f"mean quality {mean((x.quality_score or 0) for x in items):.2f}/10; "
            f"mean citation coverage {mean((x.citation_coverage or 0) for x in items):.0%}; "
            f"mean tokens {mean(x.total_tokens for x in items):.0f}; "
            f"failure rate {mean((x.failure_rate or 0) for x in items):.0%}."
        )

    lines += [
        "",
        "## Interpretation",
        "",
        "- Multi-agent is justified only if its quality/citation gains compensate for extra token, latency, "
        "handoff, and integration cost.",
        "- The single-agent baseline is intentionally retained because narrow tasks may not benefit from decomposition.",
        "- Failure analysis should inspect the saved route/event trace rather than infer causality from the final answer alone.",
        "",
        "## Failure Mode and Fix",
        "",
        "**Failure mode:** duplicated or weak evidence can be amplified across handoffs and look like consensus.",
        "",
        "**Fix:** the Researcher preserves source IDs, the Analyst explicitly compares evidence quality, the Writer "
        "must cite source IDs, and the Critic checks citation validity/synthetic labeling. Supervisor routing is bounded "
        "by `MAX_ITERATIONS` and provider calls use bounded retries/timeouts.",
        "",
    ]
    return "\n".join(lines)
