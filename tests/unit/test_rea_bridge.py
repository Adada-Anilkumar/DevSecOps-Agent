from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from devsecops_agent.analyzers.rea_bridge import REABridge
from devsecops_agent.schemas import SeverityLevel
from devsecops_agent.utils.pre_scan import detect_binary_artifacts, scan_for_secrets


def test_detect_binary_artifacts_in_diff():
    diff = """
diff --git a/native/libcore.so b/native/libcore.so
new file mode 100644
Binary files /dev/null and b/native/libcore.so differ
diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1 +1 @@
-old
+new
"""
    binaries = detect_binary_artifacts(diff)
    assert len(binaries) == 1
    assert "native/libcore.so" in binaries[0]


def test_scan_for_secrets_flags_binary():
    diff = """
diff --git a/dist/app.asar b/dist/app.asar
new file mode 100644
Binary files /dev/null and b/dist/app.asar differ
"""
    findings = scan_for_secrets(diff)
    assert any("Committed Binary" in f.title and f.severity == SeverityLevel.HIGH for f in findings)


def test_rea_bridge_convert_clean():
    bridge = REABridge()
    fake_result = {
        "success": True,
        "data": {
            "functions": ["init", "cleanup"],
            "urls": [],
            "suspicious_symbols": [],
        },
    }
    issues = bridge.convert_analysis_to_issues("bin/tool.exe", fake_result)
    assert len(issues) == 1
    assert issues[0].severity == SeverityLevel.LOW
    assert "Binary Integrity Verified" in issues[0].title


def test_rea_bridge_convert_suspicious():
    bridge = REABridge()
    fake_result = {
        "success": True,
        "data": {
            "urls": ["http://raw.githubusercontent.com/malicious/payload"],
            "suspicious_symbols": ["system", "VirtualProtect"],
        },
    }
    issues = bridge.convert_analysis_to_issues("bin/loader.so", fake_result)
    assert len(issues) >= 2
    assert any("Suspicious Embedded Network Endpoint" in i.title for i in issues)
    assert any("Dangerous System API" in i.title for i in issues)
