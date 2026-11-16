import pytest
from devsecops_agent.schemas import SeverityLevel
from devsecops_agent.utils.pre_scan import scan_for_secrets


def test_scan_detects_aws_key():
    diff_text = """
diff --git a/config.py b/config.py
--- a/config.py
+++ b/config.py
@@ -1,3 +1,4 @@
 import os
+AWS_KEY = "AKIAIOSFODNN7EXAMPLE"
 print("Init")
"""
    findings = scan_for_secrets(diff_text)
    assert len(findings) == 1
    assert findings[0].severity == SeverityLevel.CRITICAL
    assert "AWS Access Key ID" in findings[0].title
    assert findings[0].file_path == "config.py"


def test_scan_detects_private_key():
    content = """
-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA0m...
-----END RSA PRIVATE KEY-----
"""
    findings = scan_for_secrets(content, default_filename="id_rsa")
    assert len(findings) >= 1
    assert any(f.severity == SeverityLevel.CRITICAL for f in findings)


def test_scan_clean_content():
    content = """
def hello_world():
    api_key = os.environ.get("API_KEY")
    return f"Hello, {api_key}"
"""
    findings = scan_for_secrets(content)
    assert len(findings) == 0

