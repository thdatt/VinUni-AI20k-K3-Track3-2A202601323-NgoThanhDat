from multi_agent_research_lab.agents import SupervisorAgent
from multi_agent_research_lab.core.config import Settings
from multi_agent_research_lab.core.schemas import ResearchQuery, SourceDocument
from multi_agent_research_lab.core.state import ResearchState


def test_supervisor_routes_by_missing_artifact() -> None:
    settings = Settings(LLM_PROVIDER="offline", ENABLE_CRITIC=False)
    sup = SupervisorAgent(settings)
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))
    assert sup.next_route(state) == "researcher"
    state.sources = [SourceDocument(title="x", snippet="y", metadata={"source_id": "S1"})]
    state.research_notes = "notes [S1]"
    assert sup.next_route(state) == "analyst"
    state.analysis_notes = "analysis [S1]"
    assert sup.next_route(state) == "writer"
    state.final_answer = "answer [S1]"
    assert sup.next_route(state) == "done"
