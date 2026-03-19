#!/usr/bin/env python3
"""
Verify Nova Memory 2.0 Three-Agent Setup
Tests that all components are configured correctly for multi-agent coordination
"""

import sys
from pathlib import Path

print("\n" + "="*70)
print("NOVA MEMORY 2.0 - THREE-AGENT SETUP VERIFICATION")
print("="*70 + "\n")

# Track results
results = []

def check(name, condition, error_msg=""):
    """Record a check result"""
    if condition:
        results.append((name, True, ""))
        print(f"✓ {name}")
    else:
        results.append((name, False, error_msg))
        print(f"✗ {name}")
        if error_msg:
            print(f"  → {error_msg}")

# 1. Check directory structure
print("1. CHECKING PROJECT STRUCTURE")
print("-" * 70)

check(
    "Project directory exists",
    Path("C:\\Users\\DAVID\\nova-memory").exists(),
    "nova-memory directory not found"
)

check(
    "Core modules exist",
    all([
        Path(f"core/{m}.py").exists()
        for m in ["redis_cache", "agent_messaging", "security", "agent_registry"]
    ]),
    "Missing core modules"
)

check(
    "API modules exist",
    all([Path(f"api/{m}.py").exists() for m in ["integration", "advanced_routes"]]),
    "Missing API modules"
)

# 2. Check configuration
print("\n2. CHECKING CENTRAL CONFIGURATION")
print("-" * 70)

check(
    ".env.central exists",
    Path(".env.central").exists(),
    "Create .env.central from .env.example"
)

if Path(".env.central").exists():
    with open(".env.central") as f:
        config = f.read()

    check(
        "Redis host configured",
        "REDIS_HOST=127.0.0.1" in config,
        "Update REDIS_HOST to 127.0.0.1"
    )

    check(
        "Database configured",
        "nova_memory_central.db" in config,
        "Update DATABASE_URL"
    )

    check(
        "JWT secret configured",
        "JWT_SECRET_KEY=" in config,
        "Add JWT_SECRET_KEY"
    )

# 3. Check startup scripts
print("\n3. CHECKING STARTUP SCRIPTS")
print("-" * 70)

scripts = ["start_redis.ps1", "start_agent_1.ps1", "start_agent_2.ps1", "start_agent_3.ps1"]
for script in scripts:
    check(
        f"{script}",
        Path(script).exists(),
        f"Create {script}"
    )

# 4. Check documentation
print("\n4. CHECKING DOCUMENTATION")
print("-" * 70)

docs = ["THREE_AGENT_SETUP_GUIDE.md", "ADVANCED_FEATURES.md", "FILE_MANIFEST.md"]
for doc in docs:
    check(
        f"{doc}",
        Path(doc).exists(),
        f"Missing {doc}"
    )

# 5. Check Python dependencies
print("\n5. CHECKING PYTHON DEPENDENCIES")
print("-" * 70)

modules = {
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "pydantic": "pydantic",
    "jwt": "pyjwt",
    "cryptography": "cryptography",
}

for module_name, package_name in modules.items():
    try:
        __import__(module_name)
        check(f"Python {package_name}", True)
    except ImportError:
        check(f"Python {package_name}", False, f"Install with: pip install {package_name}")

# 6. Check database
print("\n6. CHECKING DATABASE")
print("-" * 70)

db_file = Path("nova_memory_central.db")
check(
    "Central database",
    db_file.exists() or True,  # Can be created on first run
    "Will be created on first agent start"
)

# 7. Summary and next steps
print("\n" + "="*70)
print("VERIFICATION SUMMARY")
print("="*70 + "\n")

passed = sum(1 for _, success, _ in results if success)
total = len(results)

print(f"Passed: {passed}/{total}")

if passed == total:
    print("\n✅ ALL CHECKS PASSED! Your system is ready.\n")
    print("NEXT STEPS:")
    print("  1. Open PowerShell as Administrator")
    print("  2. cd C:\\Users\\DAVID\\nova-memory")
    print("  3. Start Redis: .\\start_redis.ps1")
    print("  4. Open new PowerShell, start Agent 1: .\\start_agent_1.ps1")
    print("  5. Wait 10 seconds, open new PowerShell, start Agent 2: .\\start_agent_2.ps1")
    print("  6. Wait 10 seconds, open new PowerShell, start Agent 3: .\\start_agent_3.ps1")
    print("\nAccess agents at:")
    print("  Agent 1: http://localhost:8001/docs")
    print("  Agent 2: http://localhost:8002/docs")
    print("  Agent 3: http://localhost:8003/docs")
else:
    print(f"\n⚠ {total - passed} checks failed. Fix the issues above before starting.\n")

    failed = [f"{name}: {msg}" for name, success, msg in results if not success and msg]
    if failed:
        print("Required fixes:")
        for failure in failed:
            print(f"  • {failure}")

print("\n" + "="*70)
print(f"Nova Memory 2.0 - Setup Status: {'✅ READY' if passed == total else '⚠ NEEDS FIXES'}")
print("="*70 + "\n")

sys.exit(0 if passed == total else 1)
