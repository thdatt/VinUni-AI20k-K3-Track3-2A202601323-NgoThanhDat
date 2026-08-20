"""Benchmark single-agent vs multi-agent on the same offline evidence source."""

from __future__ import annotations

from collections.abc import Callable
from time import perf_counter

from multi_agent_research_lab.core.config import Settings, get_settings
from multi_agent_research_lab.core.schemas import (
    AgentName,
    AgentResult,
    BenchmarkMetrics,
    ResearchQuery,
)
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient
from multi_agent_research_lab.utils.citations import citation_coverage, extract_citation_ids

Runner = Callable[[str], ResearchState]


def run_single_agent(query: str, settings: Settings | None = None) -> ResearchState:
    settings = settings or get_settings()
    state = ResearchState(request=ResearchQuery(query=query))
    search = SearchClient(settings)
    llm = LLMClient(settings)
    sources = search.search(query, state.request.max_sources)
    state.sources = sources
    blocks = []
    for source in sources:
        sid = source.metadata.get("source_id")
        synthetic = " SYNTHETIC" if source.metadata.get("is_synthetic") else ""
        blocks.append(f"[{sid}]{synthetic} {source.title}\n{source.snippet[:1800]}")
    response = llm.complete(
        "You are the single-agent baseline. In one pass, research, analyze, and write the answer. "
        "Use [source_id] citations, label synthetic benchmark evidence, include a counterargument, "
        "trade-offs, limitations, and measurable evaluation criteria.",
        f"QUESTION:\n{query}\n\nRETRIEVED SOURCES:\n" + "\n\n".join(blocks),
    )
    state.final_answer = response.content
    state.add_usage(
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
        cost_usd=response.cost_usd,
    )
    state.record_route("baseline")
    state.record_route("done")
    state.agent_results.append(
        AgentResult(
            agent=AgentName.BASELINE,
            content=response.content,
            metadata={"provider": response.provider, "model": response.model},
        )
    )
    state.add_trace_event("baseline.complete", {"source_count": len(sources)})
    return state


def heuristic_quality(state: ResearchState) -> float:
    """Transparent 0-10 proxy used when no external human/judge score is available."""
    answer = state.final_answer or ""
    coverage = citation_coverage(answer, state.sources)
    valid_citations = len(set(extract_citation_ids(answer)))
    source_diversity = min(1.0, valid_citations / 4)
    lower = answer.lower()
    analysis_features = (
        sum(
            int(term in lower)
            for term in [
                "trade-off",
                "tradeoff",
                "limitation",
                "counter",
                "evaluation",
                "recommend",
            ]
        )
        / 6
    )
    length_score = min(1.0, len(answer.split()) / 350)
    error_penalty = min(2.0, len(state.errors) * 0.5)

    synthetic_ids = {
        str(s.metadata.get("source_id")) for s in state.sources if s.metadata.get("is_synthetic")
    }
    cited = set(extract_citation_ids(answer))
    synthetic_used = bool(cited & synthetic_ids)
    synthetic_ok = (not synthetic_used) or ("synthetic" in lower)

    raw = (
        4.0 * coverage
        + 2.0 * source_diversity
        + 1.5 * analysis_features
        + 1.0 * length_score
        + 1.5 * float(synthetic_ok)
        - error_penalty
    )
    return max(0.0, min(10.0, raw))


def run_benchmark(
    run_name: str,
    query: str,
    runner: Runner,
) -> tuple[ResearchState, BenchmarkMetrics]:
    started = perf_counter()
    failed = False
    try:
        state = runner(query)
    except Exception:
        failed = True
        raise
    finally:
        latency = perf_counter() - started

    citation = citation_coverage(state.final_answer or "", state.sources)
    cost = state.estimated_cost_usd if state.estimated_cost_usd > 0 else None
    metrics = BenchmarkMetrics(
        run_name=run_name,
        query=query,
        latency_seconds=latency,
        input_tokens=state.input_tokens,
        output_tokens=state.output_tokens,
        total_tokens=state.input_tokens + state.output_tokens,
        estimated_cost_usd=cost,
        quality_score=heuristic_quality(state),
        citation_coverage=citation,
        failure_rate=1.0 if failed or not state.final_answer else 0.0,
        source_count=len(state.sources),
        route_count=len(state.route_history),
        notes=("errors=" + "; ".join(state.errors)) if state.errors else "",
    )
    return state, metrics
