"""Retrieve relevant policy chunks for a diff (similarity search in the index)."""

from __future__ import annotations

from langchain_core.documents import Document

from devsecops_agent.rag.query import build_retrieval_query
from devsecops_agent.rag.store import open_vectorstore


def retrieve_context(
    diff_text: str,
    *,
    k: int = 6,
) -> str:
    """
    Data retrieval: embed query (via embedding model) + similarity search in Chroma.
    Returns formatted text for injection into the chat prompt (not the final review).
    """
    store = open_vectorstore(allow_empty=True)
    if store is None:
        return ""

    q = build_retrieval_query(diff_text)
    docs: list[Document] = store.similarity_search(q, k=k)
    if not docs:
        return ""

    parts: list[str] = []
    for i, d in enumerate(docs, 1):
        src = d.metadata.get("source", d.metadata.get("path", "unknown"))
        parts.append(f"### Chunk {i} (source: {src})\n{d.page_content.strip()}")
    return "\n\n".join(parts)
