#!/usr/bin/env python3
"""Quick system initialization test for Nova Memory 2.0."""

import os
from pathlib import Path


def _get_bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _load_env_files() -> None:
    project_root = Path(__file__).resolve().parent
    env_paths = [
        project_root / ".env.central",
        project_root / ".env",
    ]

    for env_path in env_paths:
        if not env_path.exists():
            continue
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


print("\n" + "=" * 70)
print("NOVA MEMORY 2.0 - SYSTEM INITIALIZATION TEST")
print("=" * 70 + "\n")

try:
    print("1. Initializing system...")
    from core.advanced_features import init_nova_memory_advanced
    _load_env_files()
    system = init_nova_memory_advanced(
        redis_host=os.getenv("REDIS_HOST", "localhost"),
        redis_port=_get_int_env("REDIS_PORT", 6379),
        redis_db=_get_int_env("REDIS_DB", 0),
        redis_password=os.getenv("REDIS_PASSWORD") or None,
        cache_ttl=_get_int_env("REDIS_CACHE_TTL", 3600),
        enable_cache=_get_bool_env("NOVA_CACHE_ENABLED", False),
        enable_semantic_search=_get_bool_env("NOVA_ENABLE_SEMANTIC_SEARCH", False),
        enable_encryption=_get_bool_env("NOVA_ENABLE_ENCRYPTION", False),
        enable_messaging=_get_bool_env("NOVA_ENABLE_MESSAGING", True),
        semantic_model=os.getenv("MODEL_NAME") or os.getenv("EMBEDDING_MODEL"),
    )
    print("   OK System initialized successfully")

    print("\n2. Checking system components...")
    components = {
        "cache": system.cache,
        "semantic_search": system.semantic_search,
        "message_broker": system.message_broker,
        "jwt_manager": system.jwt_manager,
        "encryption": system.encryption,
        "audit_log": system.audit_log,
        "registry": system.registry,
        "gc": system.gc,
    }

    for name, component in components.items():
        status = "OK" if component else "NO"
        print(f"   {status} {name}: {type(component).__name__}")

    print("\n3. Running health check...")
    health = system.health_check()
    for component, status in health.items():
        icon = "OK" if status else "OFF"
        print(f"   {icon} {component}: {'OK' if status else 'Disabled'}")

    print("\n4. Collecting system statistics...")
    stats = system.get_system_stats()
    print(f"   OK System has {len(stats)} subsystems")

    print("\n" + "=" * 70)
    print("ALL TESTS PASSED - NOVA MEMORY 2.0 RUNS WITHOUT ERRORS!")
    print("=" * 70 + "\n")

except Exception as e:
    print(f"\nERROR: {type(e).__name__}")
    print(f"   {str(e)}")
    print("\n" + "=" * 70 + "\n")
    import traceback
    traceback.print_exc()
    exit(1)
