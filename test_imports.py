#!/usr/bin/env python3
"""Test all Nova Memory 2.0 core modules for import errors."""

import sys

modules_to_test = [
    "core.redis_cache",
    "core.semantic_search",
    "core.agent_messaging",
    "core.security",
    "core.agent_registry",
    "core.memory_management",
    "core.advanced_features",
]

print("=" * 60)
print("NOVA MEMORY 2.0 - MODULE IMPORT TEST")
print("=" * 60)

results = []
for module_name in modules_to_test:
    try:
        __import__(module_name)
        results.append(f"✓ {module_name}")
    except Exception as e:
        results.append(f"✗ {module_name}: {str(e)[:80]}")

for r in results:
    print(r)

# Summary
print("\n" + "=" * 60)
failed = [r for r in results if r.startswith("✗")]
if failed:
    print(f"⚠ {len(failed)} modules failed to import")
    sys.exit(1)
else:
    print(f"✅ All {len(results)} core modules import successfully!")
    print("=" * 60)
    sys.exit(0)
