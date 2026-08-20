"""Deterministic Supervisor / router."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import Settings, get_settings
from multi_agent_research_lab.core.state import ResearchState


class SupervisorAgent(BaseAgent):
    """Routes from missing artifacts, making the orchestration policy inspectable."""

    name = "supervisor"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def next_route(self, state: ResearchState) -> str:
        if state.final_answer:
            return (
                "critic"
                if self.settings.enable_critic and "critic" not in state.route_history
                else "done"
            )
        if state.iteration >= self.settings.max_iterations:
            return "done"
        if not state.sources or not state.research_notes:
            return "researcher"
        if not state.analysis_notes:
            return "analyst"
        return "writer"

    def run(self, state: ResearchState) -> ResearchState:
        route = self.next_route(state)
        state.record_route(route)
        state.add_trace_event(
            "supervisor.route",
            {
                "route": route,
                "iteration": state.iteration,
                "has_sources": bool(state.sources),
                "has_research_notes": bool(state.research_notes),
                "has_analysis_notes": bool(state.analysis_notes),
                "has_final_answer": bool(state.final_answer),
            },
        )
        if route == "done" and not state.final_answer:
            state.errors.append("Stopped by max_iterations before final answer.")
        return state
