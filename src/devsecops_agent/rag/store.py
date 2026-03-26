"""Chroma vector store — persisted embeddings + metadata (the index)."""

from __future__ import annotations

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from devsecops_agent.settings import get_settings


def get_embeddings() -> OpenAIEmbeddings:
    settings = get_settings()
    return OpenAIEmbeddings(
        model=settings.openai_embedding_model,
        api_key=settings.openai_api_key,
    )


def open_vectorstore(*, allow_empty: bool = False) -> Chroma | None:
    """
    Open persisted Chroma. Returns None if index directory is missing and allow_empty.
    """
    settings = get_settings()
    path = settings.devsecops_chroma_path
    
    if not path.exists():
        if allow_empty:
            return None
        raise SystemExit(
            f"Vector index not found at {path}. Run ingest first or use --no-rag."
        )
    emb = get_embeddings()
    return Chroma(
        persist_directory=str(path),
        embedding_function=emb,
        collection_name=settings.devsecops_chroma_collection,
    )


def vectorstore_exists() -> bool:
    settings = get_settings()
    p = settings.devsecops_chroma_path
    return p.exists() and any(p.iterdir())
