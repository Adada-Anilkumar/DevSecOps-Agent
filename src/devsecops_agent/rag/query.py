"""Build a retrieval query from a unified diff (no LLM — deterministic)."""

from __future__ import annotations

import re


def extract_paths_from_diff(diff_text: str, limit: int = 40) -> list[str]:
    """Parse `+++ b/path` / `--- a/path` style headers."""
    paths: list[str] = []
    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            p = line[6:].strip()
            if p != "/dev/null":
                paths.append(p)
        elif line.startswith("--- a/") and not line.startswith("--- /dev/null"):
            p = line[6:].strip()
            if p != "/dev/null":
                paths.append(p)
    # De-dupe preserving order
    seen: set[str] = set()
    out: list[str] = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out[:limit]


def build_retrieval_query(diff_text: str, *, max_chars: int = 2500) -> str:
    """
    Single string for similarity_search: paths + truncated diff body.
    Embeddings model will vectorize this whole string.
    """
    paths = extract_paths_from_diff(diff_text)
    path_line = "Changed files: " + ", ".join(paths) if paths else "Changed files: (unknown)"
    body = diff_text.strip()[:max_chars]
    return f"{path_line}\n\n{body}"
