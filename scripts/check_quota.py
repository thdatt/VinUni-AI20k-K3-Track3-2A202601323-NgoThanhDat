"""Preflight: is there enough provider quota to complete a full benchmark run?

The benchmark is all-or-nothing (the report is written only after every query
finishes), so starting it without quota wastes both time and tokens.
"""

from __future__ import annotations

import json
import re
import sys

import httpx

from multi_agent_research_lab.core.config import get_settings

# Measured from reports/traces: ~4k tokens per single-agent run and ~14.6k per
# multi-agent run, across the 6 benchmark queries in configs/lab_default.yaml.
ESTIMATED_BENCHMARK_TOKENS = 111_400


def main() -> int:
    settings = get_settings()
    provider = settings.llm_provider.lower().strip()
    if provider != "groq":
        print(f"Quota preflight only implemented for groq (LLM_PROVIDER={provider}).")
        return 0

    response = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {settings.groq_api_key}"},
        json={
            "model": settings.groq_model,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 1,
        },
        timeout=settings.timeout_seconds,
    )

    print(f"model            : {settings.groq_model}")
    print(f"benchmark needs  : ~{ESTIMATED_BENCHMARK_TOKENS:,} tokens")

    if response.status_code == 429:
        message = json.loads(response.text)["error"]["message"]
        used = re.search(r"Used (\d+)", message)
        limit = re.search(r"Limit (\d+)", message)
        again = re.search(r"try again in ([^.]+\.\d+s)", message)
        if used and limit:
            print(f"daily usage      : {int(used.group(1)):,} / {int(limit.group(1)):,}")
        if again:
            print(f"retry after      : {again.group(1)}")
        print("\nNOT READY - quota exhausted. Do not start run_submission.py yet.")
        return 1

    if response.status_code != 200:
        print(f"\nProvider error {response.status_code}: {response.text[:300]}")
        return 1

    tpm = response.headers.get("x-ratelimit-limit-tokens")
    print(f"tokens/min limit : {tpm}")
    print(
        "\nREADY - no daily quota error. Note the per-day budget is not exposed in\n"
        "headers, so a long run can still exhaust it partway through."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
