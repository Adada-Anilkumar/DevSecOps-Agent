"""Index markdown/text policy files into Chroma (embedding + persistence)."""

from __future__ import annotations

from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from devsecops_agent.settings import get_settings


GLOBS = ("**/*.md", "**/*.mdx", "**/*.txt")


def _load_files(root: Path) -> list[Document]:
    docs: list[Document] = []
    for pattern in GLOBS:
        for path in sorted(root.glob(pattern)):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            rel = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
            docs.append(
                Document(
                    page_content=text,
                    metadata={"source": rel, "path": str(path)},
                )
            )
    return docs


def ingest_directory(
    source_dir: Path,
    *,
    reset: bool = False,
    chunk_size: int = 1200,
    chunk_overlap: int = 200,
) -> int:
    """
    Split documents, embed with embedding model, persist to Chroma.
    Returns number of chunks stored.
    """
    settings = get_settings()
    
    if not settings.openai_api_key:
        raise SystemExit("OPENAI_API_KEY is required for ingest (embeddings API).")

    root = source_dir.resolve()
    if not root.is_dir():
        raise SystemExit(f"Not a directory: {root}")

    raw_docs = _load_files(root)
    if not raw_docs:
        raise SystemExit(f"No .md/.mdx/.txt files under {root}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    splits: list[Document] = []
    for doc in raw_docs:
        for chunk in splitter.split_documents([doc]):
            splits.append(chunk)

    persist = settings.devsecops_chroma_path
    persist.parent.mkdir(parents=True, exist_ok=True)

    emb = OpenAIEmbeddings(
        model=settings.openai_embedding_model,
        api_key=settings.openai_api_key,
    )

    if persist.exists() and not reset:
        raise SystemExit(
            f"Index already exists at {persist}. Pass --reset to rebuild, or delete the folder."
        )

    if reset and persist.exists():
        import shutil
        shutil.rmtree(persist)

    Chroma.from_documents(
        documents=splits,
        embedding=emb,
        persist_directory=str(persist),
        collection_name=settings.devsecops_chroma_collection,
    )
    return len(splits)
