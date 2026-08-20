"""Citation parsing and coverage helpers."""

import re

from multi_agent_research_lab.core.schemas import SourceDocument

CITATION_RE = re.compile(r"\[([A-Za-z0-9_.:-]+)\]")

# LLMs routinely typeset IDs with non-ASCII dashes (non-breaking hyphen, en/em
# dash, minus sign). Left as-is they make namespaced ids such as
# "AIAGENT-16:A03" fail CITATION_RE entirely and undercount coverage.
_DASHES = dict.fromkeys(map(ord, "‐‑‒–—―−"), "-")

# The Writer prompt asks for an explicit "synthetic" label, so the bracketed
# label is expected prose rather than a hallucinated source id.
RESERVED_LABELS = frozenset({"synthetic"})


def normalize_dashes(text: str) -> str:
    return (text or "").translate(_DASHES)


def extract_citation_ids(text: str) -> list[str]:
    found = CITATION_RE.findall(normalize_dashes(text))
    return list(dict.fromkeys(c for c in found if c.lower() not in RESERVED_LABELS))


def source_ids(sources: list[SourceDocument]) -> set[str]:
    ids: set[str] = set()
    for source in sources:
        sid = normalize_dashes(str(source.metadata.get("source_id") or "")).strip()
        if sid:
            ids.add(sid)
    return ids


def citation_coverage(text: str, sources: list[SourceDocument]) -> float:
    available = source_ids(sources)
    if not available:
        return 0.0
    cited = set(extract_citation_ids(text))
    valid = cited & available
    return min(1.0, len(valid) / max(1, min(4, len(available))))


def invalid_citations(text: str, sources: list[SourceDocument]) -> list[str]:
    available = source_ids(sources)
    return sorted(set(extract_citation_ids(text)) - available)
