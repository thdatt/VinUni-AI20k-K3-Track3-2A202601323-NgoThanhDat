"""Final submission gate: requires a real LLM provider, tests, benchmark, and trace artefacts."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from multi_agent_research_lab.core.config import get_settings


def run(*cmd: str) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> None:
    settings = get_settings()
    settings.validate_provider(require_real=True)

    run(sys.executable, "-m", "pytest")
    run(sys.executable, "scripts/run_benchmark.py")

    required = [
        Path("reports/benchmark_report.md"),
        Path("reports/benchmark_results.csv"),
    ]
    missing = [str(p) for p in required if not p.exists() or p.stat().st_size == 0]
    traces = list(Path("reports/traces").glob("*.html"))
    if missing:
        raise SystemExit(f"Missing required outputs: {missing}")
    if not traces:
        raise SystemExit("No HTML trace found under reports/traces.")

    text = Path("reports/benchmark_report.md").read_text(encoding="utf-8")
    if f"LLM_PROVIDER={settings.llm_provider}" not in text:
        raise SystemExit("Benchmark report provider marker is missing.")

    print("SUBMISSION_GATE: PASS")
    print("Capture a screenshot of one reports/traces/*.html file for the trace deliverable.")
    print("Review git status before commit/push; .env must remain untracked.")


if __name__ == "__main__":
    main()
