from pathlib import Path

from multi_agent_research_lab.core.config import Settings
from multi_agent_research_lab.services.search_client import SearchClient


def test_offline_corpus_search_returns_provenance() -> None:
    settings = Settings(
        LLM_PROVIDER="offline",
        SEARCH_PROVIDER="offline",
        OFFLINE_CORPUS_PATH=Path("data/offline_corpus"),
    )
    results = SearchClient(settings).search(
        "single agent multi agent coordination overhead",
        max_results=5,
    )
    assert results
    assert all(r.metadata.get("source_id") for r in results)
    assert all("is_synthetic" in r.metadata for r in results)
