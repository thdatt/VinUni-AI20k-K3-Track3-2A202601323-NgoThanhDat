"""LangGraph workflow with bounded fallback executor."""

from __future__ import annotations

from typing import Any

from multi_agent_research_lab.agents import (
    AnalystAgent,
    CriticAgent,
    ResearcherAgent,
    SupervisorAgent,
    WriterAgent,
)
from multi_agent_research_lab.core.config import Settings, get_settings
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import save_trace
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient


class MultiAgentWorkflow:
    """Supervisor -> Researcher -> Analyst -> Writer -> optional Critic."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        llm = LLMClient(self.settings)
        search = SearchClient(self.settings)
        self.supervisor = SupervisorAgent(self.settings)
        self.researcher = ResearcherAgent(search, llm)
        self.analyst = AnalystAgent(llm)
        self.writer = WriterAgent(llm)
        self.critic = CriticAgent()
        self._compiled: Any | None = None

    @staticmethod
    def _to_state(data: ResearchState | dict[str, Any]) -> ResearchState:
        return data if isinstance(data, ResearchState) else ResearchState.model_validate(data)

    def _node_supervisor(self, data: dict[str, Any]) -> dict[str, Any]:
        return self.supervisor.run(self._to_state(data)).model_dump()

    def _node_researcher(self, data: dict[str, Any]) -> dict[str, Any]:
        return self.researcher.run(self._to_state(data)).model_dump()

    def _node_analyst(self, data: dict[str, Any]) -> dict[str, Any]:
        return self.analyst.run(self._to_state(data)).model_dump()

    def _node_writer(self, data: dict[str, Any]) -> dict[str, Any]:
        return self.writer.run(self._to_state(data)).model_dump()

    def _node_critic(self, data: dict[str, Any]) -> dict[str, Any]:
        state = self.critic.run(self._to_state(data))
        state.record_route("done")
        return state.model_dump()

    @staticmethod
    def _route(data: dict[str, Any]) -> str:
        history = data.get("route_history") or []
        return str(history[-1]) if history else "done"

    def build(self) -> object:
        """Build a real LangGraph when the optional dependency is installed."""
        try:
            from langgraph.graph import END, StateGraph
        except ImportError:
            # Unit tests can run without optional LLM extras. `run()` still exercises
            # the exact same bounded routing policy in a deterministic loop.
            return {"backend": "bounded-python-fallback"}

        graph = StateGraph(dict)
        graph.add_node("supervisor", self._node_supervisor)
        graph.add_node("researcher", self._node_researcher)
        graph.add_node("analyst", self._node_analyst)
        graph.add_node("writer", self._node_writer)
        graph.add_node("critic", self._node_critic)
        graph.set_entry_point("supervisor")

        graph.add_conditional_edges(
            "supervisor",
            self._route,
            {
                "researcher": "researcher",
                "analyst": "analyst",
                "writer": "writer",
                "critic": "critic",
                "done": END,
            },
        )
        graph.add_edge("researcher", "supervisor")
        graph.add_edge("analyst", "supervisor")
        graph.add_edge("writer", "supervisor")
        graph.add_edge("critic", END)
        self._compiled = graph.compile()
        return self._compiled

    def _run_fallback(self, state: ResearchState) -> ResearchState:
        for _ in range(self.settings.max_iterations + 3):
            self.supervisor.run(state)
            route = state.route_history[-1]
            if route == "researcher":
                self.researcher.run(state)
            elif route == "analyst":
                self.analyst.run(state)
            elif route == "writer":
                self.writer.run(state)
            elif route == "critic":
                self.critic.run(state)
                state.record_route("done")
                break
            elif route == "done":
                break
        return state

    def run(self, state: ResearchState) -> ResearchState:
        compiled = self._compiled or self.build()
        if isinstance(compiled, dict):
            result = self._run_fallback(state)
        else:
            payload = compiled.invoke(state.model_dump())
            result = ResearchState.model_validate(payload)
        save_trace(result)
        return result
