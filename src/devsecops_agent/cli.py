from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from devsecops_agent.prompts import build_user_message
from devsecops_agent.rag.ingest import ingest_directory
from devsecops_agent.services.review_service import run_security_review
from devsecops_agent.settings import get_settings


def _read_diff(path: str | None) -> str:
    if path is None or path == "-":
        return sys.stdin.read()
    p = Path(path)
    if not p.is_file():
        raise SystemExit(f"Not a file: {path}")
    return p.read_text(encoding="utf-8", errors="replace")


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="DevSecOps PR review agent: LLM review with optional LangChain RAG.",
    )
    parser.add_argument(
        "--ingest",
        metavar="DIR",
        help="Index .md/.txt policies into the vector store (Chroma) and exit",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="With --ingest, delete existing index and rebuild",
    )
    parser.add_argument(
        "--diff",
        "-d",
        metavar="PATH",
        help="Unified diff file path, or '-' / omit for stdin",
    )
    parser.add_argument(
        "--language",
        "-l",
        help="Language or runtime hint (e.g. python3.12, TypeScript)",
    )
    parser.add_argument(
        "--context",
        "-c",
        help="Free-text context (deployment, threat model, team notes)",
    )
    parser.add_argument(
        "--rag",
        action="store_true",
        help="Use LangChain: retrieve policy chunks (embeddings + Chroma) then chat model",
    )
    parser.add_argument(
        "--rag-k",
        type=int,
        default=6,
        metavar="K",
        help="Top-K chunks to retrieve (default: 6)",
    )
    parser.add_argument(
        "--chroma-path",
        metavar="PATH",
        help="Override vector index directory (else DEVSECOPS_CHROMA_PATH or .devsecops/chroma)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the user message only; do not call the API",
    )
    args = parser.parse_args()

    # Get settings instance
    settings = get_settings()

    # Override chroma path if provided
    if args.chroma_path:
        settings.devsecops_chroma_path = Path(args.chroma_path).resolve()

    if args.ingest:
        n = ingest_directory(Path(args.ingest), reset=args.reset)
        print(f"Indexed {n} chunks into {settings.devsecops_chroma_path}")
        return

    diff_text = _read_diff(args.diff)
    if not diff_text.strip():
        raise SystemExit("No diff content. Pipe git diff or pass --diff FILE.")

    user_message = build_user_message(
        diff_text,
        language=args.language,
        extra_context=args.context,
    )

    if args.dry_run:
        print(user_message)
        return

    report = run_security_review(
        diff_text,
        language=args.language,
        extra_context=args.context,
        use_rag=args.rag,
        rag_k=args.rag_k,
    )
    print(report)


if __name__ == "__main__":
    main()
