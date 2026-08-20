from pathlib import Path

from multi_agent_research_lab.core.config import Settings
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow


def test_workflow_runs_end_to_end_offline(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(Path.cwd())
    settings = Settings(
        LLM_PROVIDER="offline",
        SEARCH_PROVIDER="offline",
        OFFLINE_CORPUS_PATH=Path("data/offline_corpus"),
        ENABLE_CRITIC=True,
        MAX_ITERATIONS=6,
    )
    state = ResearchState(
        request=ResearchQuery(
            query="When is a multi-agent architecture justified over a single agent?"
        )
    )
    result = MultiAgentWorkflow(settings).run(state)
    assert result.final_answer
    assert result.sources
    assert "researcher" in result.route_history
    assert "analyst" in result.route_history
    assert "writer" in result.route_history
    assert "critic" in result.route_history
    assert result.route_history[-1] == "done"
