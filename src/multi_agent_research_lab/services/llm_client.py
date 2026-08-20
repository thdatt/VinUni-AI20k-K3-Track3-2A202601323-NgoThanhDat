"""Provider-agnostic LLM client with bounded retries, timeout, and usage accounting."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass

from multi_agent_research_lab.core.config import Settings, get_settings
from multi_agent_research_lab.core.errors import AgentExecutionError


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None
    model: str | None = None
    provider: str | None = None


class LLMClient:
    """LLM client supporting OpenAI, Groq's OpenAI-compatible endpoint, and offline tests."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        return max(1, len(text or "") // 4)

    def _cost(self, input_tokens: int, output_tokens: int) -> float | None:
        if self.settings.input_cost_per_1m is None or self.settings.output_cost_per_1m is None:
            return None
        return (
            input_tokens * self.settings.input_cost_per_1m
            + output_tokens * self.settings.output_cost_per_1m
        ) / 1_000_000

    def _offline_complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Deterministic fallback used by unit tests, never presented as a real LLM run."""
        citations = list(dict.fromkeys(re.findall(r"\[([A-Za-z0-9_.:-]+)\]", user_prompt)))
        cited = " ".join(f"[{c}]" for c in citations[:6])
        lower = system_prompt.lower()

        if "researcher" in lower:
            content = (
                "Evidence notes:\n"
                "- The retrieved corpus contains architecture, evaluation, and failure-mode "
                "evidence. "
                f"{cited}\n"
                "- Prefer public-reference evidence for general claims and label synthetic "
                "benchmark "
                "evidence explicitly.\n"
                "- Preserve disagreements and source provenance across handoffs."
            )
        elif "analyst" in lower:
            content = (
                "Analysis:\n"
                "- Multi-agent gains are conditional on meaningful task decomposition and "
                "independent "
                f"verification; coordination adds latency and token cost. {cited}\n"
                "- A single-agent baseline remains preferable for narrow tasks with little "
                "decomposition value.\n"
                "- Treat synthetic benchmark evidence as illustrative rather than a real "
                "publication.\n"
                "- Evaluate quality, citation coverage, latency, token usage, and failure "
                "propagation together."
            )
        elif "critic" in lower:
            content = (
                "Critic review: preserve source IDs, avoid universal superiority claims, "
                "explicitly label "
                f"synthetic evidence, and retain limitations. {cited}"
            )
        else:
            content = (
                "## Executive Summary\n"
                "A multi-agent research workflow is justified when decomposition creates genuinely "
                "different "
                "evidence or verification needs; otherwise coordination overhead can erase gains. "
                f"{cited}\n\n"
                "## Evidence and Trade-offs\n"
                "Specialized research and independent analysis can improve coverage and expose "
                "unsupported "
                "claims, but handoffs can duplicate work, drift context, and increase latency and "
                "token usage. "
                "A strong single-agent baseline should therefore remain part of every "
                "evaluation.\n\n"
                "## Recommendation\n"
                "Use bounded routing, shared provenance-rich state, explicit citation validation, "
                "and a "
                "multi-dimensional benchmark. Label synthetic evidence and preserve unresolved "
                "conflicts."
            )

        inp = self._estimate_tokens(system_prompt + user_prompt)
        out = self._estimate_tokens(content)
        return LLMResponse(
            content=content,
            input_tokens=inp,
            output_tokens=out,
            cost_usd=self._cost(inp, out),
            model="offline-deterministic",
            provider="offline",
        )

    @staticmethod
    def _retry_after_seconds(exc: Exception) -> float | None:
        """Read a provider-supplied retry delay from a 429 response, if present."""
        response = getattr(exc, "response", None)
        headers = getattr(response, "headers", None) or {}
        for header in ("retry-after", "x-ratelimit-reset-tokens", "x-ratelimit-reset-requests"):
            raw = headers.get(header)
            if not raw:
                continue
            match = re.fullmatch(r"(?:(\d+(?:\.\d+)?)m)?(\d+(?:\.\d+)?)s?", str(raw).strip())
            if match:
                minutes = float(match.group(1) or 0)
                seconds = float(match.group(2) or 0)
                return minutes * 60 + seconds
        return None

    @staticmethod
    def _is_daily_quota(exc: Exception) -> bool:
        """A per-day quota cannot be waited out inside a run; retrying is pointless."""
        return "per day" in str(exc).lower() or "(tpd)" in str(exc).lower()

    def _backoff_seconds(self, exc: Exception, attempt: int) -> float:
        """Rate limits need the provider window to reset; other errors back off quickly."""
        status = getattr(exc, "status_code", None) or getattr(
            getattr(exc, "response", None), "status_code", None
        )
        is_rate_limit = status == 429 or "ratelimit" in type(exc).__name__.lower()
        if not is_rate_limit:
            return min(8.0, 1.5 * (2**attempt))

        # Groq free tier resets tokens-per-minute on a 60s window; waiting less
        # than that guarantees the retry burns an attempt on the same 429.
        wait = self._retry_after_seconds(exc)
        if wait is None:
            wait = 60.0
        return min(90.0, max(5.0, wait + 2.0))

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        provider = self.settings.llm_provider.lower().strip()
        if provider == "offline":
            return self._offline_complete(system_prompt, user_prompt)

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise AgentExecutionError(
                'Install LLM dependencies with: pip install -e ".[llm]"'
            ) from exc

        if provider == "openai":
            if not self.settings.openai_api_key:
                raise AgentExecutionError("OPENAI_API_KEY is missing.")
            client = OpenAI(
                api_key=self.settings.openai_api_key,
                base_url=self.settings.openai_base_url or None,
                timeout=self.settings.timeout_seconds,
            )
            model = self.settings.openai_model
        elif provider == "groq":
            if not self.settings.groq_api_key:
                raise AgentExecutionError("GROQ_API_KEY is missing.")
            client = OpenAI(
                api_key=self.settings.groq_api_key,
                base_url="https://api.groq.com/openai/v1",
                timeout=self.settings.timeout_seconds,
            )
            model = self.settings.groq_model
        else:
            raise AgentExecutionError(f"Unsupported LLM provider: {provider}")

        last_error: Exception | None = None
        for attempt in range(self.settings.max_retries):
            try:
                response = client.chat.completions.create(
                    model=model,
                    temperature=0.1,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                content = (response.choices[0].message.content or "").strip()
                usage = getattr(response, "usage", None)
                input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
                output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
                return LLMResponse(
                    content=content,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost_usd=self._cost(input_tokens, output_tokens),
                    model=model,
                    provider=provider,
                )
            except Exception as exc:  # provider SDK exceptions vary by version
                last_error = exc
                if self._is_daily_quota(exc):
                    raise AgentExecutionError(
                        f"{provider} daily token quota exhausted; retrying cannot help. "
                        f"Wait for the quota to reset or raise the plan limit. Detail: {exc}"
                    ) from exc
                if attempt + 1 >= self.settings.max_retries:
                    break
                time.sleep(self._backoff_seconds(exc, attempt))

        raise AgentExecutionError(
            f"LLM call failed after {self.settings.max_retries} attempts: "
            f"{type(last_error).__name__ if last_error else 'unknown'}: {last_error}"
        ) from last_error
