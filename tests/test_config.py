from multi_agent_research_lab.core.config import Settings


def test_settings_defaults() -> None:
    settings = Settings(LLM_PROVIDER="offline")
    assert settings.openai_model
    assert settings.max_iterations >= 1
    assert settings.search_provider == "offline"
