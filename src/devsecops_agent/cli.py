from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from devsecops_agent.prompts import build_user_message
from devsecops_agent.schemas import ReviewResult, SeverityLevel
from devsecops_agent.services.review_service import review_code
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
        description="DevSecOps Code & PR Review Agent: Mentorship & AppSec analysis with optional RAG.",
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
        "--file",
        "-f",
        metavar="PATH",
        help="Source code file path to review directly (non-diff mode)",
    )
    parser.add_argument(
        "--snippet",
        "-s",
        metavar="CODE",
        help="Inline raw code snippet string to review directly",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json", "sarif"],
        default="markdown",
        help="Output format: markdown, json (structured), or sarif (for GitHub Security / CI upload)",
    )
    parser.add_argument(
        "--fail-on",
        choices=["CRITICAL", "HIGH", "MEDIUM", "LOW"],
        help="CI/CD gate threshold: exit code 1 if issues equal or exceed this severity",
    )
    parser.add_argument(
        "--no-prescan",
        action="store_true",
        help="Disable deterministic regex pre-scanner for secrets",
    )
    parser.add_argument(
        "--with-rea",
        action="store_true",
        help="Enable morluto/rea reverse engineering for detected binary/ASAR assets",
    )
    parser.add_argument(
        "--artifact",
        metavar="PATH",
        help="Target binary, ASAR, or packaged artifact to inspect with morluto/rea",
    )
    parser.add_argument(
        "--language",
        "-l",
        help="Language or runtime hint (e.g. python, TypeScript, Go)",
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
        help="Print the formatted user message only; do not call LLM API",
    )
    args = parser.parse_args()

    settings = get_settings()

    if args.chroma_path:
        settings.devsecops_chroma_path = Path(args.chroma_path).resolve()

    if args.ingest:
        from devsecops_agent.rag.ingest import ingest_directory
        n = ingest_directory(Path(args.ingest), reset=args.reset)
        print(f"Indexed {n} chunks into {settings.devsecops_chroma_path}")
        return

    # Determine content and input type
    is_diff = True
    if args.snippet:
        content = args.snippet
        is_diff = False
    elif args.file:
        file_path = Path(args.file)
        if not file_path.is_file():
            raise SystemExit(f"Not a file: {args.file}")
        content = file_path.read_text(encoding="utf-8", errors="replace")
        is_diff = False
        if not args.language and file_path.suffix:
            args.language = file_path.suffix.lstrip(".")
    else:
        content = _read_diff(args.diff)
        if not content.strip():
            raise SystemExit("No content to review. Provide --diff, --file, --snippet, or pipe stdin.")

    if args.dry_run:
        user_msg = build_user_message(
            content,
            is_diff=is_diff,
            language=args.language,
            extra_context=args.context,
        )
        print(user_msg)
        return

    req_format = "structured" if args.format in ["json", "sarif"] else "markdown"
    result = review_code(
        content,
        is_diff=is_diff,
        language=args.language,
        extra_context=args.context,
        use_rag=args.rag,
        rag_k=args.rag_k,
        enable_prescan=not args.no_prescan,
        with_rea=args.with_rea,
        target_artifact=args.artifact,
        output_format=req_format,
    )

    if args.format == "json":
        if isinstance(result, ReviewResult):
            print(result.model_dump_json(indent=2))
        else:
            print(json.dumps({"review": str(result)}, indent=2))
    elif args.format == "sarif":
        if isinstance(result, ReviewResult):
            print(json.dumps(result.to_sarif(), indent=2))
        else:
            print(json.dumps({"error": "SARIF format requires structured output."}, indent=2))
    else:
        # Markdown format
        if isinstance(result, ReviewResult):
            print(result.to_markdown())
        else:
            print(result)

    # CI/CD fail-on threshold check
    if args.fail_on and isinstance(result, ReviewResult):
        severity_ranks = {
            SeverityLevel.CRITICAL: 4,
            SeverityLevel.HIGH: 3,
            SeverityLevel.MEDIUM: 2,
            SeverityLevel.LOW: 1,
            SeverityLevel.INFO: 0,
        }
        threshold_rank = severity_ranks.get(SeverityLevel(args.fail_on), 3)
        found_max_rank = max(
            [severity_ranks.get(issue.severity, 0) for issue in result.issues],
            default=0,
        )
        if found_max_rank >= threshold_rank:
            sys.exit(1)


if __name__ == "__main__":
    main()
