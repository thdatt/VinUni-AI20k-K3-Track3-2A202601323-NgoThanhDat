"""Local JSON/HTML tracing with optional LangSmith-friendly environment metadata."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from multi_agent_research_lab.core.state import ResearchState


def save_trace(state: ResearchState, root: str | Path = "reports/traces") -> tuple[Path, Path]:
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    json_path = root / f"{state.run_id}.json"
    html_path = root / f"{state.run_id}.html"

    payload = {
        "run_id": state.run_id,
        "query": state.request.query,
        "route_history": state.route_history,
        "errors": state.errors,
        "input_tokens": state.input_tokens,
        "output_tokens": state.output_tokens,
        "estimated_cost_usd": state.estimated_cost_usd,
        "events": state.trace,
    }
    json_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

    cards = []
    for i, event in enumerate(state.trace, start=1):
        cards.append(
            "<section><h3>"
            + html.escape(f"{i}. {event.get('name', 'event')}")
            + "</h3><pre>"
            + html.escape(json.dumps(event.get("payload", {}), indent=2, ensure_ascii=False, default=str))
            + "</pre></section>"
        )
    html_doc = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Lab20 Trace {html.escape(state.run_id)}</title>
<style>
body{{font-family:system-ui;max-width:1050px;margin:30px auto;padding:0 18px;background:#f7f7f9}}
section{{background:white;border:1px solid #ddd;border-radius:10px;padding:16px;margin:12px 0}}
pre{{white-space:pre-wrap;word-break:break-word}} code{{font-family:ui-monospace}}
.badge{{display:inline-block;padding:4px 8px;background:#eee;border-radius:6px;margin-right:6px}}
</style></head><body>
<h1>Multi-Agent Trace</h1>
<p><span class="badge">run_id={html.escape(state.run_id)}</span>
<span class="badge">routes={len(state.route_history)}</span>
<span class="badge">tokens={state.input_tokens + state.output_tokens}</span></p>
<h2>Query</h2><p>{html.escape(state.request.query)}</p>
<h2>Route history</h2><pre>{html.escape(" → ".join(state.route_history))}</pre>
{''.join(cards)}
</body></html>"""
    html_path.write_text(html_doc, encoding="utf-8")
    return json_path, html_path
