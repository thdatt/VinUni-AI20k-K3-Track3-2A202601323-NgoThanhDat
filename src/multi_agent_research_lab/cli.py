"""Command-line entrypoint."""

from typing import Annotated

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.panel import Panel

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import run_single_agent
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.observability.tracing import save_trace

app = typer.Typer(help="Completed Multi-Agent Research Lab CLI")
console = Console()


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


def _parse_query(query: str) -> ResearchQuery:
    try:
        return ResearchQuery(query=query)
    except ValidationError as exc:
        console.print(
            Panel.fit(
                f"Invalid query: {exc.errors()[0]['msg']}",
                title="Input Error",
                style="red",
            )
        )
        raise typer.Exit(code=1) from exc


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the single-agent baseline against the same offline corpus."""
    _init()
    _parse_query(query)
    state = run_single_agent(query)
    json_path, html_path = save_trace(state)
    console.print(Panel.fit(state.final_answer or "", title="Single-Agent Baseline"))
    console.print(f"Trace: {html_path} ({json_path})")


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run Supervisor -> Researcher -> Analyst -> Writer -> Critic."""
    _init()
    state = ResearchState(request=_parse_query(query))
    result = MultiAgentWorkflow().run(state)
    console.print(Panel.fit(result.final_answer or "(no final answer)", title="Multi-Agent Answer"))
    console.print(f"Routes: {' -> '.join(result.route_history)}")
    console.print(f"Tokens: {result.input_tokens + result.output_tokens}")
    console.print(f"Errors: {result.errors or 'none'}")


if __name__ == "__main__":
    app()
