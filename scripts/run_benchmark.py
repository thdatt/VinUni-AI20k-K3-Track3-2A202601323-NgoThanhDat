"""Run the same query set through baseline and multi-agent and write the report."""

from __future__ import annotations

import csv
from pathlib import Path

import yaml

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import run_benchmark, run_single_agent
from multi_agent_research_lab.evaluation.report import render_markdown_report
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow


def main() -> None:
    settings = get_settings()
    config = yaml.safe_load(Path("configs/lab_default.yaml").read_text(encoding="utf-8"))
    queries = list(config["benchmark"]["queries"])

    workflow = MultiAgentWorkflow(settings)
    metrics = []
    rows = []

    for query in queries:
        baseline_state, baseline_metric = run_benchmark(
            "single-agent",
            query,
            lambda q: run_single_agent(q, settings),
        )
        multi_state, multi_metric = run_benchmark(
            "multi-agent",
            query,
            lambda q: workflow.run(ResearchState(request=ResearchQuery(query=q))),
        )
        metrics.extend([baseline_metric, multi_metric])
        for state, metric in [
            (baseline_state, baseline_metric),
            (multi_state, multi_metric),
        ]:
            rows.append(
                {
                    **metric.model_dump(),
                    "final_answer": state.final_answer or "",
                    "route_history": " -> ".join(state.route_history),
                    "errors": " | ".join(state.errors),
                }
            )

    Path("reports").mkdir(exist_ok=True)
    with Path("reports/benchmark_results.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    report = render_markdown_report(metrics)
    provider_note = (
        f"\n## Runtime Provider\n\n`LLM_PROVIDER={settings.llm_provider}`. "
        "If this is `offline`, this report is a deterministic validation run and must be rerun "
        "with Groq/OpenAI before final submission.\n"
    )
    Path("reports/benchmark_report.md").write_text(report + provider_note, encoding="utf-8")
    print("Benchmark complete: reports/benchmark_results.csv + reports/benchmark_report.md")


if __name__ == "__main__":
    main()
