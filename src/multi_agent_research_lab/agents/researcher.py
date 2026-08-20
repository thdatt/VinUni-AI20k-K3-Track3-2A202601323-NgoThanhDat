"""Researcher agent: retrieve bounded evidence and produce provenance-preserving notes."""

from time import perf_counter

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient


class ResearcherAgent(BaseAgent):
    name = "researcher"

    def __init__(
        self,
        search_client: SearchClient | None = None,
        llm_client: LLMClient | None = None,
    ) -> None:
        self.search_client = search_client or SearchClient()
        self.llm_client = llm_client or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        started = perf_counter()
        sources = self.search_client.search(state.request.query, state.request.max_sources)
        if not sources:
            state.errors.append("Researcher found no sources.")
            state.add_trace_event("researcher.empty", {"query": state.request.query})
            return state

        state.sources = sources
        blocks = []
        for source in sources:
            sid = str(source.metadata.get("source_id") or "unknown")
            synthetic = " SYNTHETIC" if source.metadata.get("is_synthetic") else ""
            blocks.append(f"[{sid}]{synthetic} {source.title}\n{source.snippet[:1800]}")

        response = self.llm_client.complete(
            "You are the Researcher. Extract concise evidence-bearing notes. "
            "Keep inline [source_id] citations. Distinguish synthetic evidence from "
            "public-reference "
            "evidence. Do not decide the final conclusion.",
            f"Research question: {state.request.query}\n\nSOURCES:\n" + "\n\n".join(blocks),
        )
        state.research_notes = response.content
        state.add_usage(
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            cost_usd=response.cost_usd,
        )
        state.agent_results.append(
            AgentResult(
                agent=AgentName.RESEARCHER,
                content=response.content,
                metadata={
                    "source_count": len(sources),
                    "provider": response.provider,
                    "model": response.model,
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                },
            )
        )
        state.add_trace_event(
            "researcher.complete",
            {
                "duration_seconds": perf_counter() - started,
                "source_ids": [s.metadata.get("source_id") for s in sources],
                "source_count": len(sources),
            },
        )
        return state
