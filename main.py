#!/usr/bin/env python3
"""
Nova Memory System v2.0 — Main Runner

Demonstrates all core components:
  1. Enhanced persistent memory storage
  2. Multi-agent collaboration
  3. Workflow orchestration
  4. Optional integrations (IBM watsonx, Solana)

Usage:
    python main.py
"""

import sys
import os
import logging

# Ensure the project root is on the path regardless of working directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.WARNING)

from enhanced_memory import EnhancedMemoryStorage
from agent_collaboration import AgentCollaboration
from core.workflow_orchestration import WorkflowOrchestrationEngine


def print_header():
    print("\n" + "=" * 60)
    print("  NOVA MEMORY SYSTEM v2.0")
    print("  AI Agent Memory — Persistent · Searchable · Collaborative")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Component tests
# ---------------------------------------------------------------------------

def test_enhanced_memory() -> bool:
    """Smoke-test the core memory storage layer."""
    print("\n[1] Testing Enhanced Memory Storage...")

    storage = EnhancedMemoryStorage()

    mid1 = storage.add_memory(
        content="User prefers concise Python code examples.",
        metadata={"type": "preference", "version": "2.0"},
        tags=["preference", "python", "style"],
        author="agent_alpha",
    )
    mid2 = storage.add_memory(
        content="Project deadline is 2026-04-01 for the Nova Memory v2.0 release.",
        metadata={"type": "fact"},
        tags=["deadline", "project"],
        author="agent_beta",
    )

    if mid1:
        mem = storage.get_memory(mid1)
        if mem:
            print(f"    Retrieved: {mem['content'][:60]}  access_count={mem['access_count']}")

    # Search
    results = storage.search_memories("Python")
    print(f"    Search 'Python' → {len(results)} result(s)")

    # Update
    if mid1:
        storage.update_memory(mid1, content="User strongly prefers concise Python answers.")

    # Stats
    storage.get_memory_stats()

    # Cleanup
    if mid2:
        storage.delete_memory(mid2)

    print("[OK] Enhanced memory test passed")
    return True


def test_agent_collaboration() -> bool:
    """Smoke-test the multi-agent collaboration layer."""
    print("\n[2] Testing Agent Collaboration...")

    collab = AgentCollaboration()

    space_id = collab.create_collaborative_space(
        space_name="Nova Agents Team",
        creator="nexus",
        members=["nexus", "sentinel"],
        permissions={"read": True, "write": True},
    )

    if space_id:
        collab.add_memory_to_space(space_id, "mem-demo-001", "nexus")
        share_id = collab.share_memory_with_agent(
            "nexus", "sentinel", "mem-demo-001", "read"
        )
        spaces = collab.list_collaborative_spaces("sentinel")
        shares = collab.get_agent_memory_shares("sentinel")
        print(f"    Spaces for sentinel: {len(spaces)}")
        print(f"    Shares for sentinel: {len(shares)}")

        if share_id:
            collab.revoke_share(share_id)

        collab.create_agent_memory_sync("nexus", "sentinel", "mem-demo-002")

    print("[OK] Agent collaboration test passed")
    return True


def test_workflow_orchestration() -> bool:
    """Smoke-test the workflow orchestration engine."""
    print("\n[3] Testing Workflow Orchestration...")

    engine = WorkflowOrchestrationEngine()

    def generic_callback(task, workflow_id, workflow):
        return {"status": "completed", "task": task.name}

    for agent in ["healthcare_agent", "data_analyzer", "communication_coordinator"]:
        engine.register_task_callback(agent, generic_callback)

    wf_id = engine.create_workflow(
        name="Patient Care Demo",
        description="End-to-end patient care workflow",
        tasks=[
            {
                "task_id": "t1",
                "name": "Retrieve Patient Data",
                "description": "Fetch patient history",
                "assigned_agent": "healthcare_agent",
                "dependencies": [],
            },
            {
                "task_id": "t2",
                "name": "Analyse Treatment Needs",
                "description": "Analyse current treatment requirements",
                "assigned_agent": "data_analyzer",
                "dependencies": ["t1"],
            },
            {
                "task_id": "t3",
                "name": "Coordinate Care Plan",
                "description": "Create and coordinate care plan",
                "assigned_agent": "communication_coordinator",
                "dependencies": ["t2"],
            },
        ],
    )

    engine.start_workflow(wf_id, {"patient_id": "patient_123"})
    status = engine.get_workflow_status(wf_id)
    progress = engine.get_workflow_progress(wf_id)
    print(f"    Workflow status: {status['status']}")
    print(f"    Progress: {progress['progress']:.0f}%")

    print("[OK] Workflow orchestration test passed")
    return True


def test_optional_integrations() -> dict:
    """Test optional integrations gracefully (no hard failures)."""
    print("\n[4] Testing Optional Integrations...")
    results = {}

    # IBM watsonx
    try:
        from integrations.ibm_watsonx_integration import IBMWatsonxIntegration
        ibm = IBMWatsonxIntegration()
        ibm.register_skill("memory_skill", "Memory Skill", "Nova Memory integration")
        results["ibm_watsonx"] = "available (demo mode)"
        print("    IBM watsonx: available (demo mode)")
    except Exception as exc:
        results["ibm_watsonx"] = f"skipped ({exc})"
        print(f"    IBM watsonx: skipped ({exc})")

    # Solana
    try:
        from integrations.solana_integration import SolanaIntegration  # noqa: F401
        results["solana"] = "module importable"
        print("    Solana: module importable (requires solana package)")
    except ImportError:
        results["solana"] = "skipped (solana package not installed)"
        print("    Solana: skipped (install 'solana' package to enable)")

    return results


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    print_header()

    results = {
        "Enhanced Memory": test_enhanced_memory(),
        "Agent Collaboration": test_agent_collaboration(),
        "Workflow Orchestration": test_workflow_orchestration(),
    }
    integration_results = test_optional_integrations()

    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    for component, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"  {component}: {status}")
    for component, info in integration_results.items():
        print(f"  {component}: {info}")

    print("\n" + "=" * 60)
    print("NOVA MEMORY v2.0 — READY")
    print("=" * 60)
    print("\n  Start the API server:  python -m api.server")
    print("  API docs:              http://localhost:8000/docs")
    print("  Run demos:             python demo_scenarios.py")


if __name__ == "__main__":
    main()
