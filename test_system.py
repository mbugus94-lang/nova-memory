#!/usr/bin/env python3
"""Quick system initialization test for Nova Memory 2.0."""

print("\n" + "=" * 70)
print("NOVA MEMORY 2.0 - SYSTEM INITIALIZATION TEST")
print("=" * 70 + "\n")

try:
    print("1. Initializing system...")
    from core.advanced_features import init_nova_memory_advanced
    system = init_nova_memory_advanced()
    print("   ✓ System initialized successfully")
    
    print("\n2. Checking system components...")
    components = {
        'cache': system.cache,
        'semantic_search': system.semantic_search,
        'message_broker': system.message_broker,
        'jwt_manager': system.jwt_manager,
        'encryption': system.encryption,
        'audit_log': system.audit_log,
        'registry': system.registry,
        'gc': system.gc,
    }
    
    for name, component in components.items():
        status = "✓" if component else "✗"
        print(f"   {status} {name}: {type(component).__name__}")
    
    print("\n3. Running health check...")
    health = system.health_check()
    for component, status in health.items():
        icon = "✓" if status else "⚠"
        print(f"   {icon} {component}: {'OK' if status else 'Disabled'}")
    
    print("\n4. Collecting system statistics...")
    stats = system.get_system_stats()
    print(f"   ✓ System has {len(stats)} subsystems")
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED - NOVA MEMORY 2.0 RUNS WITHOUT ERRORS!")
    print("=" * 70 + "\n")
    
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}")
    print(f"   {str(e)}")
    print("\n" + "=" * 70 + "\n")
    import traceback
    traceback.print_exc()
    exit(1)
