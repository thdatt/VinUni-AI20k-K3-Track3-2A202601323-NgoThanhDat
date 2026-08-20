from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.evaluation.report import render_markdown_report


def test_report_renders_markdown() -> None:
    report = render_markdown_report(
        [
            BenchmarkMetrics(
                run_name="baseline",
                query="q",
                latency_seconds=1.23,
                total_tokens=100,
                quality_score=7.0,
            )
        ]
    )
    assert "Benchmark Report" in report
    assert "baseline" in report
    assert "Failure Mode and Fix" in report
