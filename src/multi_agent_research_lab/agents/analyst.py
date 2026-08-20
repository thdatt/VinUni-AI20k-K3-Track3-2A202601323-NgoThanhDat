"""Analyst agent: compare evidence, expose conflicts, and calibrate claims."""

from time import perf_counter

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class AnalystAgent(BaseAgent):
    name = "analyst"

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        started = perf_counter()
        if not state.research_notes:
            state.errors.append("Analyst called without research_notes.")
            return state

        source_ledger = "\n".join(
            f"[{s.metadata.get('source_id')}] class={s.metadata.get('document_class')} "
            f"synthetic={bool(s.metadata.get('is_synthetic'))}"
            for s in state.sources
        )
        response = self.llm_client.complete(
            "You are the Analyst. Compare evidence quality, identify disagreements, "
            "test counterarguments, flag weak/synthetic evidence, and keep [source_id] "
            "provenance. Do not write the final report.",
            f"QUESTION:\n{state.request.query}\n\nSOURCE LEDGER:\n{source_ledger}\n\n"
            f"RESEARCH NOTES:\n{state.research_notes}",
        )
        state.analysis_notes = response.content
        state.add_usage(
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            cost_usd=response.cost_usd,
        )
        state.agent_results.append(
            AgentResult(
                agent=AgentName.ANALYST,
                content=response.content,
                metadata={
                    "provider": response.provider,
                    "model": response.model,
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                },
            )
        )
        state.add_trace_event(
            "analyst.complete",
            {"duration_seconds": perf_counter() - started},
        )
        return state
