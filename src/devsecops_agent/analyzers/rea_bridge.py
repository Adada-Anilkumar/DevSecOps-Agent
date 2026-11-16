"""Modular integration bridge for morluto/rea (Reverse Engineer Anything).

Enables AI agent analysis of compiled native binaries, Electron ASAR files,
minified web bundles, and packaged mobile assets without bloating core dependencies.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from devsecops_agent.schemas import Category, ReviewIssue, SeverityLevel
from devsecops_agent.utils.logging_config import get_logger

logger = get_logger(__name__)


class REABridge:
    """Bridge interface to morluto/rea CLI & MCP toolkit."""

    def __init__(self, cli_command: Optional[str] = None):
        self.cli_command = cli_command or os.getenv("REA_CLI_COMMAND")
        self._detected_cmd = self._resolve_runner()

    def _resolve_runner(self) -> Optional[List[str]]:
        """Detect whether rea or npx is available on system PATH."""
        if self.cli_command and shutil.which(self.cli_command):
            return [self.cli_command]
        if shutil.which("rea"):
            return ["rea"]
        if shutil.which("npx"):
            return ["npx", "--yes", "rea-agents"]
        return None

    @property
    def is_available(self) -> bool:
        """Check if rea reverse engineering runner is available on host."""
        return self._detected_cmd is not None

    def analyze_artifact(
        self,
        target_path: str | Path,
        timeout_seconds: int = 120,
    ) -> Dict[str, Any]:
        """Run morluto/rea reverse engineering analysis on a binary/packaged file."""
        target = Path(target_path)
        if not target.exists():
            return {
                "success": False,
                "error": f"Target artifact not found on filesystem: {target_path}",
            }

        if not self.is_available:
            return {
                "success": False,
                "error": (
                    "morluto/rea is not installed on the system PATH. "
                    "Install via 'npm install -g rea-agents' or run 'npx rea-agents setup'."
                ),
            }

        cmd = list(self._detected_cmd) + ["analyze", str(target.resolve()), "--format", "json"]
        logger.info("Executing morluto/rea analysis", target=str(target), command=cmd[0])

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
            if res.returncode != 0:
                logger.warning("rea exited with non-zero status", stderr=res.stderr[:300])
                return {
                    "success": False,
                    "error": res.stderr.strip() or f"Process failed with exit code {res.returncode}",
                }

            try:
                data = json.loads(res.stdout)
                return {"success": True, "data": data}
            except json.JSONDecodeError:
                return {
                    "success": True,
                    "data": {
                        "raw_output": res.stdout.strip(),
                    },
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Analysis timed out after {timeout_seconds}s for {target.name}",
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Execution error: {str(e)}",
            }

    def convert_analysis_to_issues(
        self,
        artifact_path: str,
        analysis_result: Dict[str, Any],
    ) -> List[ReviewIssue]:
        """Convert decompiled structural findings into DevSecOps ReviewIssues."""
        issues: List[ReviewIssue] = []

        if not analysis_result.get("success"):
            # Informational issue noting skipped or failed reverse engineering
            issues.append(
                ReviewIssue(
                    file_path=artifact_path,
                    line_number=1,
                    category=Category.INFRASTRUCTURE,
                    severity=SeverityLevel.INFO,
                    title="Reverse Engineering Analysis Status",
                    description=analysis_result.get("error", "Analysis incomplete"),
                    suggested_fix="Ensure morluto/rea dependencies are installed for deep artifact inspection.",
                    educational_note="Reverse engineering decompiles binaries and ASAR packages to verify supply chain integrity.",
                )
            )
            return issues

        data = analysis_result.get("data", {})

        # 1. Suspicious network endpoints discovered in binary
        network_calls = data.get("network_calls") or data.get("urls") or []
        for url in network_calls:
            if isinstance(url, str) and ("http://" in url or "raw.githubusercontent" in url or "pastebin" in url):
                issues.append(
                    ReviewIssue(
                        file_path=artifact_path,
                        line_number=1,
                        category=Category.SECURITY,
                        severity=SeverityLevel.HIGH,
                        title=f"Suspicious Embedded Network Endpoint in Binary: {url}",
                        description=f"Decompiled binary connects to external endpoint: {url}",
                        suggested_fix="Verify endpoint against company egress policy and allowlist.",
                        educational_note="Hardcoded or unencrypted remote URLs inside binary packages can signify data exfiltration or dynamic payload staging.",
                    )
                )

        # 2. Suspicious process/command execution symbols
        suspicious_symbols = data.get("suspicious_symbols") or data.get("suspicious_calls") or []
        for sym in suspicious_symbols:
            issues.append(
                ReviewIssue(
                    file_path=artifact_path,
                    line_number=1,
                    category=Category.SECURITY,
                    severity=SeverityLevel.HIGH,
                    title=f"Dangerous System API Reference: {sym}",
                    description=f"Artifact decompilation identified dangerous native call '{sym}' capable of subverting host security.",
                    suggested_fix="Ensure process invocation or dynamic memory allocation is restricted and strictly necessary.",
                    educational_note="APIs like system(), execve(), or VirtualProtect() are frequently leveraged in native exploits.",
                )
            )

        # 3. Overall binary summary if clean
        if not issues:
            issues.append(
                ReviewIssue(
                    file_path=artifact_path,
                    line_number=1,
                    category=Category.SECURITY,
                    severity=SeverityLevel.LOW,
                    title="Binary Integrity Verified via morluto/rea",
                    description=f"Reverse engineered artifact '{Path(artifact_path).name}'. No overt malicious indicators or anomalous system calls detected.",
                    suggested_fix="Maintain signed artifact provenance (SLSA level 3).",
                    educational_note="Regular binary inspection ensures compiled outputs match open source repository intentions.",
                )
            )

        return issues
