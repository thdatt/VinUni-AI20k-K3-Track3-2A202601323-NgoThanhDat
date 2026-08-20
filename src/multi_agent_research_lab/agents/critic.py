"""Citation/safety critic that validates the Writer output independently."""

from time import perf_counter

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.utils.citations import (
    citation_coverage,
    extract_citation_ids,
    invalid_citations,
    source_ids,
)


class CriticAgent(BaseAgent):
    name = "critic"

    def run(self, state: ResearchState) -> ResearchState:
        started = perf_counter()
        answer = state.final_answer or ""
        invalid = invalid_citations(answer, state.sources)
        coverage = citation_coverage(answer, state.sources)
        cited = extract_citation_ids(answer)
        available = source_ids(state.sources)

        synthetic_ids = {
            str(s.metadata.get("source_id"))
            for s in state.sources
            if s.metadata.get("is_synthetic")
        }
        synthetic_cited = sorted(set(cited) & synthetic_ids)
        labels_synthetic = "synthetic" in answer.lower()

        findings = {
            "citation_coverage": coverage,
            "invalid_citations": invalid,
            "cited_source_count": len(set(cited) & available),
            "available_source_count": len(available),
            "synthetic_citations": synthetic_cited,
            "synthetic_labeled": labels_synthetic or not synthetic_cited,
        }
        if invalid:
            state.errors.append(f"Critic found invalid citations: {', '.join(invalid)}")
        if synthetic_cited and not labels_synthetic:
            state.errors.append("Critic: synthetic evidence was cited without explicit labeling.")

        content = (
            f"Citation coverage={coverage:.0%}; "
            f"invalid citations={invalid or 'none'}; "
            f"synthetic labeling={'PASS' if findings['synthetic_labeled'] else 'FAIL'}."
        )
        state.agent_results.append(
            AgentResult(agent=AgentName.CRITIC, content=content, metadata=findings)
        )
        state.add_trace_event(
            "critic.complete",
            {"duration_seconds": perf_counter() - started, **findings},
        )
        return state
