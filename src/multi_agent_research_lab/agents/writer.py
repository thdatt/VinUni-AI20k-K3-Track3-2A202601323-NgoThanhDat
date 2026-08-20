"""Writer agent: synthesize a grounded final answer."""

from time import perf_counter

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class WriterAgent(BaseAgent):
    name = "writer"

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        started = perf_counter()
        if not state.analysis_notes:
            state.errors.append("Writer called without analysis_notes.")
            return state

        ledger = "\n".join(
            f"[{s.metadata.get('source_id')}] {s.title} "
            f"(synthetic={bool(s.metadata.get('is_synthetic'))})"
            for s in state.sources
        )
        response = self.llm_client.complete(
            "You are the Writer. Produce a clear evidence-grounded answer for technical learners. "
            "Cite factual claims with [source_id]. Explicitly label synthetic benchmark evidence when used. "
            "Include counterarguments, trade-offs, limitations, evaluation criteria, and a recommendation. "
            "Never claim universal superiority.",
            f"QUESTION:\n{state.request.query}\n\nSOURCE LEDGER:\n{ledger}\n\n"
            f"RESEARCH NOTES:\n{state.research_notes}\n\nANALYSIS:\n{state.analysis_notes}",
        )
        state.final_answer = response.content
        state.add_usage(
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            cost_usd=response.cost_usd,
        )
        state.agent_results.append(
            AgentResult(
                agent=AgentName.WRITER,
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
            "writer.complete",
            {"duration_seconds": perf_counter() - started},
        )
        return state
