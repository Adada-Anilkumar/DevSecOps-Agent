# DevSecOps agent — model roles, RAG, LangChain

## Which model is used where

| Component | Model env | Default | Purpose |
|-----------|-----------|---------|---------|
| **Chat / reasoning** | `OPENAI_MODEL` | `gpt-4o-mini` | Writes the PR security report (structured Markdown). This is the only model that *generates* review text. |
| **Embeddings** | `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Turns text into vectors for (1) indexing policies at ingest and (2) embedding the retrieval query built from the diff. Does **not** generate prose. |

Both call OpenAI-compatible APIs (`OPENAI_API_KEY`; optional `OPENAI_BASE_URL` for proxies or Azure-style endpoints where supported by LangChain).

## Where embeddings are used

1. **Ingest** (`--ingest DIR`): Each policy chunk is embedded and stored in **Chroma** (on-disk vector index under `DEVSECOPS_CHROMA_PATH`).
2. **Review with `--rag`**: The diff is summarized into a **retrieval query** (`rag/query.py`); that string is embedded; **similarity search** returns top-K chunks.

## Data indexing and retrieval

- **Indexing**: Markdown/text under a directory → split → embed → **Chroma** persistence. This is your org’s “policy brain” (standards, runbooks, CWE notes).
- **Retrieval**: Similarity search only; no keyword index. Retrieved chunks are **prepended to the user message** as context. The chat model is instructed that the **diff remains authoritative** for what changed.

## Where LangChain is used

- **Without `--rag`**: LangChain `ChatOpenAI` + messages for a single generation step (`reviewer.py`).
- **With `--rag`**: LCEL chain in `chains/review_chain.py`: `RunnablePassthrough` → augment with retrieved text → `ChatPromptTemplate` → `ChatOpenAI` → `StrOutputParser`.

## Operational notes

- **Cost**: Ingest is one-time (or on policy updates). Each `--rag` review adds embedding calls for the query + chat tokens for the report.
- **Privacy**: Diffs and policies leave your network only to the configured API endpoint; do not log raw secrets.
- **Deterministic checks**: Keep Semgrep/Gitleaks/Trivy in CI; this agent is for reasoning + policy alignment, not replacement for SAST/DAST.
