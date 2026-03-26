"""
Quick test script to verify local setup is working.
Run this before starting the full webhook server.
"""

import sys
import time
from pathlib import Path

print("🚀 DevSecOps Agent - Local Setup Test")
print("=" * 50)

# Test 1: Check Python version
print("\n1️⃣ Checking Python version...")
if sys.version_info >= (3, 10):
    print(f"   ✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
else:
    print(f"   ❌ Python {sys.version_info.major}.{sys.version_info.minor} (need 3.10+)")
    sys.exit(1)

# Test 2: Check .env file
print("\n2️⃣ Checking .env file...")
if Path(".env").exists():
    print("   ✅ .env file exists")
else:
    print("   ❌ .env file not found")
    sys.exit(1)

# Test 3: Load settings
print("\n3️⃣ Loading configuration...")
try:
    from devsecops_agent.settings import get_settings
    settings = get_settings()
    print(f"   ✅ Settings loaded")
    print(f"      - Provider: {settings.llm_provider}")
    print(f"      - Model: {settings.get_model_name()}")
    print(f"      - Port: {settings.port}")
    print(f"      - Log Level: {settings.log_level}")
    
    # Check API key based on provider
    if settings.llm_provider == "gemini":
        if not settings.gemini_api_key:
            print(f"   ⚠️  GEMINI_API_KEY not set in .env")
            print(f"      Get free key at: https://aistudio.google.com/app/apikey")
        else:
            print(f"   ✅ Gemini API key configured")
    elif settings.llm_provider == "openai":
        if not settings.openai_api_key:
            print(f"   ⚠️  OPENAI_API_KEY not set in .env")
        else:
            print(f"   ✅ OpenAI API key configured")
            
except Exception as e:
    print(f"   ❌ Failed to load settings: {e}")
    sys.exit(1)

# Test 4: Check required dependencies
print("\n4️⃣ Checking dependencies...")
required_packages = [
    "fastapi",
    "uvicorn",
    "openai",
    "langchain",
    "pydantic",
    "structlog",
    "prometheus_client",
]

missing = []
for package in required_packages:
    try:
        __import__(package)
        print(f"   ✅ {package}")
    except ImportError:
        print(f"   ❌ {package} (missing)")
        missing.append(package)

if missing:
    print(f"\n   Install missing packages: pip install {' '.join(missing)}")
    sys.exit(1)

# Test 5: Test imports
print("\n5️⃣ Testing core imports...")
try:
    from devsecops_agent.webhook.app import app
    print("   ✅ Webhook app imports successfully")
except Exception as e:
    print(f"   ❌ Failed to import webhook app: {e}")
    sys.exit(1)

# Test 6: Check example files
print("\n6️⃣ Checking example files...")
if Path("examples/test-pr-samples/vulnerable-code.py").exists():
    print("   ✅ Test samples available")
else:
    print("   ⚠️  Test samples not found (optional)")

print("\n" + "=" * 50)
print("✅ All checks passed!")
print("\n📋 Next steps:")
print("   1. Get FREE Gemini API key:")
print("      https://aistudio.google.com/app/apikey")
print("   2. Edit .env and add:")
print("      LLM_PROVIDER=gemini")
print("      GEMINI_API_KEY=AIza...")
print("      GITHUB_TOKEN=ghp_...")
print("   3. Start the agent:")
print("      python -m devsecops_agent.webhook.serve")
print("   4. In another terminal, expose with ngrok:")
print("      ngrok http 8080")
print("   5. Configure GitHub webhook with ngrok URL")
print("   6. Create a test PR!")
print("\n📖 Full guide: GEMINI_SETUP.md")
print("📖 Step-by-step: LOCAL_SETUP_STEPS.md")
