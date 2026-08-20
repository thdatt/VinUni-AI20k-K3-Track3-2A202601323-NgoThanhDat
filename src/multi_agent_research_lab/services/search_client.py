"""Search abstraction with a production-safe offline corpus implementation."""

from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from multi_agent_research_lab.core.config import Settings, get_settings
from multi_agent_research_lab.core.schemas import SourceDocument

TOKEN_RE = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_-]{1,}")


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text or "")]


@dataclass
class _IndexedDocument:
    source: SourceDocument
    terms: Counter[str]
    length: int
    topic_title: str


class SearchClient:
    """Provider-agnostic search client.

    The lab defaults to the uploaded 30-topic offline research corpus. This makes
    retrieval deterministic, preserves provenance, and requires no browser/search API.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._docs: list[_IndexedDocument] = []
        self._idf: dict[str, float] = {}
        self._avg_len = 1.0
        self._loaded = False

    def _resolve_corpus_dir(self) -> Path:
        path = self.settings.offline_corpus_path
        if not path.is_absolute():
            path = Path.cwd() / path
        if not path.exists():
            raise FileNotFoundError(
                f"Offline corpus directory not found: {path}. "
                "Extract the supplied data ZIP to data/offline_corpus."
            )
        return path

    def _load(self) -> None:
        if self._loaded:
            return
        if self.settings.search_provider.lower() != "offline":
            raise NotImplementedError(
                "This completed submission intentionally uses the supplied offline corpus. "
                "Set SEARCH_PROVIDER=offline."
            )

        corpus = self._resolve_corpus_dir()
        topic_files = sorted((corpus / "topics").glob("*.json"))
        if not topic_files:
            raise FileNotFoundError(f"No topic JSON files found under {corpus / 'topics'}.")

        raw_docs: list[tuple[SourceDocument, str, str]] = []
        for path in topic_files:
            obj = json.loads(path.read_text(encoding="utf-8"))
            topic_id = str(obj["topic"].get("topic_id") or obj["benchmark_metadata"].get("topic_id") or "")
            title = str(obj["topic"].get("title") or "")
            kb = obj["knowledge_base"]

            for doc in kb.get("source_documents", []):
                sid = str(doc.get("document_id") or doc.get("source_id") or "")
                text = str(doc.get("full_text") or "")
                source = SourceDocument(
                    title=str(doc.get("title") or sid),
                    url=doc.get("provenance_url"),
                    snippet=text,
                    metadata={
                        "source_id": sid,
                        "topic_id": topic_id,
                        "topic_title": title,
                        "document_class": doc.get("document_class"),
                        "is_synthetic": bool(doc.get("is_synthetic")),
                        "year": doc.get("year"),
                        "kind": "source_document",
                    },
                )
                raw_docs.append((source, text, title))

            for article in kb.get("knowledge_articles", []):
                aid = str(article.get("article_id") or "")
                # Article IDs repeat across topics, so namespace them.
                sid = f"{topic_id}:{aid}"
                text = str(article.get("content") or "")
                source = SourceDocument(
                    title=str(article.get("title") or sid),
                    url=f"offline://{path.name}#{aid}",
                    snippet=text,
                    metadata={
                        "source_id": sid,
                        "topic_id": topic_id,
                        "topic_title": title,
                        "document_class": "knowledge_article",
                        "is_synthetic": False,
                        "kind": "knowledge_article",
                    },
                )
                raw_docs.append((source, text, title))

        df: defaultdict[str, int] = defaultdict(int)
        indexed: list[_IndexedDocument] = []
        total_len = 0
        for source, text, topic_title in raw_docs:
            terms = Counter(_tokens(f"{topic_title} {source.title} {text}"))
            length = max(1, sum(terms.values()))
            indexed.append(_IndexedDocument(source=source, terms=terms, length=length, topic_title=topic_title))
            total_len += length
            for term in terms:
                df[term] += 1

        n = max(1, len(indexed))
        self._idf = {term: math.log(1.0 + (n - freq + 0.5) / (freq + 0.5)) for term, freq in df.items()}
        self._avg_len = total_len / n
        self._docs = indexed
        self._loaded = True

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        self._load()
        q_terms = Counter(_tokens(query))
        if not q_terms:
            return []

        k1, b = 1.5, 0.75
        scored: list[tuple[float, _IndexedDocument]] = []
        query_text = " ".join(q_terms)

        for doc in self._docs:
            score = 0.0
            for term, qtf in q_terms.items():
                tf = doc.terms.get(term, 0)
                if not tf:
                    continue
                denom = tf + k1 * (1 - b + b * doc.length / self._avg_len)
                score += self._idf.get(term, 0.0) * ((tf * (k1 + 1)) / denom) * min(2, qtf)

            title_tokens = set(_tokens(doc.topic_title))
            overlap = len(set(q_terms) & title_tokens)
            score += overlap * 1.1

            # Prefer public/reference material by default, but do not hide synthetic evidence.
            if doc.source.metadata.get("document_class") == "public_reference_summary":
                score += 0.25
            if doc.source.metadata.get("is_synthetic") and "synthetic" not in query_text:
                score -= 0.10

            if score > 0:
                scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)

        results: list[SourceDocument] = []
        seen: set[str] = set()
        for score, doc in scored:
            sid = str(doc.source.metadata.get("source_id"))
            if sid in seen:
                continue
            seen.add(sid)
            payload = doc.source.model_copy(deep=True)
            payload.metadata["retrieval_score"] = round(score, 4)
            # Keep enough content for evidence while bounding context.
            payload.snippet = payload.snippet[:4500]
            results.append(payload)
            if len(results) >= max_results:
                break
        return results
