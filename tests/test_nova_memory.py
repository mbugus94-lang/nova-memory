"""
Nova Memory 2.0 — Comprehensive Test Suite

Covers:
  - EnhancedMemoryStorage (CRUD, search, versioning, backup, stats)
  - AgentCollaboration (spaces, sharing, revocation, sync)
  - WorkflowOrchestrationEngine (creation, execution, dependency ordering)
  - FineTuningEngine (embedding, retrieval, fine-tuning, metrics)
  - Agent Framework Adapters (generic, LangChain, AutoGen, CrewAI)

Run:
    python -m pytest tests/test_nova_memory.py -v
    # or
    python tests/test_nova_memory.py
"""

import os
import sys
import unittest
import tempfile

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ---------------------------------------------------------------------------
# EnhancedMemoryStorage tests
# ---------------------------------------------------------------------------

class TestEnhancedMemoryStorage(unittest.TestCase):

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        os.unlink(self.db_path)  # let the class create it fresh
        from enhanced_memory import EnhancedMemoryStorage
        self.storage = EnhancedMemoryStorage(db_path=self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_add_and_get_memory(self):
        mid = self.storage.add_memory(
            content="Test memory content",
            metadata={"key": "value"},
            tags=["test", "unit"],
            author="test_agent",
        )
        self.assertIsNotNone(mid)
        mem = self.storage.get_memory(mid)
        self.assertIsNotNone(mem)
        self.assertEqual(mem["content"], "Test memory content")
        self.assertEqual(mem["author"], "test_agent")
        self.assertIn("test", mem["tags"])

    def test_add_memory_empty_content_returns_none(self):
        mid = self.storage.add_memory(content="")
        self.assertIsNone(mid)

    def test_get_nonexistent_memory_returns_none(self):
        result = self.storage.get_memory("does-not-exist")
        self.assertIsNone(result)

    def test_access_count_increments(self):
        mid = self.storage.add_memory("Access counter test")
        mem1 = self.storage.get_memory(mid)
        mem2 = self.storage.get_memory(mid)
        self.assertGreater(mem2["access_count"], mem1["access_count"])

    def test_update_memory_content(self):
        mid = self.storage.add_memory("Original content")
        success = self.storage.update_memory(mid, content="Updated content")
        self.assertTrue(success)
        mem = self.storage.get_memory(mid)
        self.assertEqual(mem["content"], "Updated content")

    def test_update_memory_metadata(self):
        mid = self.storage.add_memory("Content", metadata={"v": 1})
        self.storage.update_memory(mid, metadata={"v": 2})
        mem = self.storage.get_memory(mid)
        self.assertEqual(mem["metadata"]["v"], 2)

    def test_update_nonexistent_returns_false(self):
        result = self.storage.update_memory("ghost-id", content="x")
        self.assertFalse(result)

    def test_delete_memory(self):
        mid = self.storage.add_memory("To be deleted")
        deleted = self.storage.delete_memory(mid)
        self.assertTrue(deleted)
        self.assertIsNone(self.storage.get_memory(mid))

    def test_delete_nonexistent_returns_false(self):
        result = self.storage.delete_memory("ghost-id")
        self.assertFalse(result)

    def test_search_memories(self):
        self.storage.add_memory("Python programming tips", tags=["python"])
        self.storage.add_memory("JavaScript frameworks", tags=["js"])
        results = self.storage.search_memories("Python")
        self.assertGreater(len(results), 0)
        self.assertTrue(any("Python" in r["content"] for r in results))

    def test_search_empty_query_returns_list(self):
        self.storage.add_memory("Some content")
        results = self.storage.search_memories("")
        self.assertIsInstance(results, list)

    def test_list_memories(self):
        self.storage.add_memory("Memory A", author="agent1")
        self.storage.add_memory("Memory B", author="agent2")
        all_mems = self.storage.list_memories()
        self.assertGreaterEqual(len(all_mems), 2)

    def test_list_memories_author_filter(self):
        self.storage.add_memory("Memory A", author="agent1")
        self.storage.add_memory("Memory B", author="agent2")
        filtered = self.storage.list_memories(author="agent1")
        self.assertTrue(all(m["author"] == "agent1" for m in filtered))

    def test_get_memory_stats(self):
        self.storage.add_memory("Stats test memory")
        stats = self.storage.get_memory_stats()
        self.assertIsNotNone(stats)
        self.assertIn("total_memories", stats)
        self.assertGreaterEqual(stats["total_memories"], 1)

    def test_backup_and_restore(self):
        mid = self.storage.add_memory("Backup test content")
        backup_id = self.storage.create_backup("test_backup")
        self.assertIsNotNone(backup_id)
        # Delete the memory
        self.storage.delete_memory(mid)
        self.assertIsNone(self.storage.get_memory(mid))
        # Restore
        restored = self.storage.restore_backup(backup_id)
        self.assertTrue(restored)

    def test_compression_reduces_size(self):
        long_content = "A" * 10000
        self.storage.add_memory(long_content)
        stats = self.storage.get_memory_stats()
        self.assertLess(stats["compressed_storage_bytes"], stats["total_storage_bytes"])


# ---------------------------------------------------------------------------
# AgentCollaboration tests
# ---------------------------------------------------------------------------

class TestAgentCollaboration(unittest.TestCase):

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        os.unlink(self.db_path)
        from agent_collaboration import AgentCollaboration
        self.collab = AgentCollaboration(db_path=self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_create_collaborative_space(self):
        space_id = self.collab.create_collaborative_space(
            space_name="Test Space", creator="agent_a", members=["agent_b"]
        )
        self.assertIsNotNone(space_id)
        self.assertIsInstance(space_id, int)

    def test_duplicate_space_name_raises(self):
        self.collab.create_collaborative_space("Unique Space", creator="a")
        result = self.collab.create_collaborative_space("Unique Space", creator="b")
        self.assertIsNone(result)

    def test_add_memory_to_space(self):
        space_id = self.collab.create_collaborative_space("Space1", creator="a")
        result = self.collab.add_memory_to_space(space_id, "mem-001", "a")
        self.assertTrue(result)

    def test_list_collaborative_spaces(self):
        self.collab.create_collaborative_space("Space A", creator="nexus", members=["sentinel"])
        spaces = self.collab.list_collaborative_spaces("sentinel")
        self.assertGreater(len(spaces), 0)

    def test_list_spaces_excludes_non_member(self):
        self.collab.create_collaborative_space("Private Space", creator="nexus")
        spaces = self.collab.list_collaborative_spaces("outsider")
        self.assertEqual(len(spaces), 0)

    def test_share_memory_with_agent(self):
        share_id = self.collab.share_memory_with_agent(
            "agent_a", "agent_b", "mem-001", "read"
        )
        self.assertIsNotNone(share_id)

    def test_get_agent_memory_shares(self):
        self.collab.share_memory_with_agent("a", "b", "mem-001")
        shares = self.collab.get_agent_memory_shares("b")
        self.assertGreater(len(shares), 0)
        self.assertEqual(shares[0]["memory_id"], "mem-001")

    def test_expired_shares_excluded(self):
        self.collab.share_memory_with_agent(
            "a", "b", "mem-expired",
            expires_at="2000-01-01 00:00:00",  # already expired
        )
        shares = self.collab.get_agent_memory_shares("b")
        self.assertEqual(len(shares), 0)

    def test_revoke_share(self):
        share_id = self.collab.share_memory_with_agent("a", "b", "mem-001")
        revoked = self.collab.revoke_share(share_id)
        self.assertTrue(revoked)
        shares = self.collab.get_agent_memory_shares("b")
        self.assertEqual(len(shares), 0)

    def test_revoke_nonexistent_share_returns_false(self):
        result = self.collab.revoke_share(99999)
        self.assertFalse(result)

    def test_bidirectional_sync(self):
        result = self.collab.create_agent_memory_sync("a", "b", "mem-sync")
        self.assertTrue(result)
        shares_b = self.collab.get_agent_memory_shares("b")
        shares_a = self.collab.get_agent_memory_shares("a")
        self.assertGreater(len(shares_b), 0)
        self.assertGreater(len(shares_a), 0)


# ---------------------------------------------------------------------------
# WorkflowOrchestrationEngine tests
# ---------------------------------------------------------------------------

class TestWorkflowOrchestrationEngine(unittest.TestCase):

    def setUp(self):
        from core.workflow_orchestration import WorkflowOrchestrationEngine
        self.engine = WorkflowOrchestrationEngine()
        self.engine.register_task_callback(
            "test_agent",
            lambda task, wid, wf: {"status": "completed"},
        )

    def test_create_workflow(self):
        wf_id = self.engine.create_workflow(
            name="Test WF",
            description="Unit test workflow",
            tasks=[
                {"task_id": "t1", "name": "Task 1", "assigned_agent": "test_agent", "dependencies": []},
            ],
        )
        self.assertIsNotNone(wf_id)

    def test_start_workflow_changes_status(self):
        wf_id = self.engine.create_workflow(
            name="Status Test",
            description="",
            tasks=[
                {"task_id": "t1", "name": "T1", "assigned_agent": "test_agent", "dependencies": []},
            ],
        )
        self.engine.start_workflow(wf_id)
        status = self.engine.get_workflow_status(wf_id)
        self.assertIn(status["status"], ["active", "completed"])

    def test_dependency_ordering(self):
        """Tasks with dependencies must not run before their prerequisites."""
        execution_order = []

        def ordered_callback(task, wid, wf):
            execution_order.append(task.task_id)
            return {"status": "completed"}

        self.engine.register_task_callback("ordered_agent", ordered_callback)

        wf_id = self.engine.create_workflow(
            name="Dep Test",
            description="",
            tasks=[
                {"task_id": "t1", "name": "First",  "assigned_agent": "ordered_agent", "dependencies": []},
                {"task_id": "t2", "name": "Second", "assigned_agent": "ordered_agent", "dependencies": ["t1"]},
                {"task_id": "t3", "name": "Third",  "assigned_agent": "ordered_agent", "dependencies": ["t2"]},
            ],
        )
        self.engine.start_workflow(wf_id)

        self.assertEqual(execution_order, ["t1", "t2", "t3"])

    def test_all_tasks_complete(self):
        from core.workflow_orchestration import TaskStatus
        wf_id = self.engine.create_workflow(
            name="Completion Test",
            description="",
            tasks=[
                {"task_id": "t1", "name": "T1", "assigned_agent": "test_agent", "dependencies": []},
                {"task_id": "t2", "name": "T2", "assigned_agent": "test_agent", "dependencies": ["t1"]},
            ],
        )
        self.engine.start_workflow(wf_id)
        status = self.engine.get_workflow_status(wf_id)
        for task in status["tasks"].values():
            self.assertEqual(task["status"], TaskStatus.COMPLETED.value)

    def test_workflow_progress(self):
        wf_id = self.engine.create_workflow(
            name="Progress Test",
            description="",
            tasks=[
                {"task_id": "t1", "name": "T1", "assigned_agent": "test_agent", "dependencies": []},
            ],
        )
        self.engine.start_workflow(wf_id)
        progress = self.engine.get_workflow_progress(wf_id)
        self.assertEqual(progress["progress"], 100.0)

    def test_get_all_workflows(self):
        self.engine.create_workflow("WF1", "", [])
        self.engine.create_workflow("WF2", "", [])
        all_wfs = self.engine.get_all_workflows()
        self.assertGreaterEqual(len(all_wfs), 2)

    def test_start_nonexistent_workflow_returns_false(self):
        result = self.engine.start_workflow("ghost-id")
        self.assertFalse(result)

    def test_pause_and_resume(self):
        from core.workflow_orchestration import WorkflowStatus
        wf_id = self.engine.create_workflow(
            name="Pause Test",
            description="",
            tasks=[],
        )
        # Manually set to ACTIVE for pause test
        self.engine.workflows[wf_id].status = WorkflowStatus.ACTIVE
        paused = self.engine.pause_workflow(wf_id)
        self.assertTrue(paused)
        self.assertEqual(self.engine.workflows[wf_id].status, WorkflowStatus.PAUSED)
        resumed = self.engine.resume_workflow(wf_id)
        self.assertTrue(resumed)
        self.assertEqual(self.engine.workflows[wf_id].status, WorkflowStatus.ACTIVE)


# ---------------------------------------------------------------------------
# FineTuningEngine tests
# ---------------------------------------------------------------------------

class TestFineTuningEngine(unittest.TestCase):

    def setUp(self):
        from core.real_time_fine_tuning import FineTuningEngine
        self.engine = FineTuningEngine(model_size="small")

    def test_embed_text_returns_array(self):
        import numpy as np
        emb = self.engine.embed_text("Hello world")
        self.assertIsInstance(emb, np.ndarray)
        self.assertEqual(emb.shape[0], self.engine.hidden_size)

    def test_embed_text_normalised(self):
        import numpy as np
        emb = self.engine.embed_text("Normalised embedding test")
        norm = float(np.linalg.norm(emb))
        self.assertAlmostEqual(norm, 1.0, places=5)

    def test_store_and_retrieve_memory(self):
        self.engine.store_memory("The Eiffel Tower is in Paris.")
        self.engine.store_memory("The Colosseum is in Rome.")
        results = self.engine.retrieve_memories("Paris", top_k=1)
        self.assertEqual(len(results), 1)
        self.assertIn("Paris", results[0]["text"])

    def test_retrieve_empty_store_returns_empty(self):
        from core.real_time_fine_tuning import FineTuningEngine
        fresh = FineTuningEngine(model_size="small")
        results = fresh.retrieve_memories("anything")
        self.assertEqual(results, [])

    def test_fine_tune_on_interaction_returns_stats(self):
        stats = self.engine.fine_tune_on_interaction({
            "user_message": "What is 2+2?",
            "agent_response": "4",
            "user_feedback": "positive",
        })
        self.assertIn("loss", stats)
        self.assertIn("mode", stats)
        self.assertGreaterEqual(stats["loss"], 0.0)

    def test_fine_tune_batch(self):
        interactions = [
            {"user_message": "Q1", "agent_response": "A1", "user_feedback": "positive"},
            {"user_message": "Q2", "agent_response": "A2", "user_feedback": "negative"},
        ]
        stats = self.engine.fine_tune_batch(interactions)
        self.assertEqual(stats["num_interactions"], 2)
        self.assertIn("avg_loss", stats)

    def test_performance_metrics_after_training(self):
        self.engine.fine_tune_on_interaction({
            "user_message": "Test", "agent_response": "Response", "user_feedback": None
        })
        metrics = self.engine.get_performance_metrics()
        self.assertEqual(metrics["status"], "training_active")
        self.assertGreater(metrics["total_iterations"], 0)

    def test_invalid_model_size_raises(self):
        from core.real_time_fine_tuning import FineTuningEngine
        with self.assertRaises(ValueError):
            FineTuningEngine(model_size="xlarge")


# ---------------------------------------------------------------------------
# Agent Framework Adapters tests
# ---------------------------------------------------------------------------

class TestAgentFrameworkAdapters(unittest.TestCase):

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_generic_adapter_save_and_load(self):
        from integrations.agent_framework_adapters import GenericMemoryAdapter
        adapter = GenericMemoryAdapter(db_path=self.db_path, agent_id="test")
        mid = adapter.save("Test content", tags=["test"])
        self.assertIsNotNone(mid)
        results = adapter.load("Test content")
        self.assertGreater(len(results), 0)

    def test_generic_adapter_clear_session(self):
        from integrations.agent_framework_adapters import GenericMemoryAdapter
        adapter = GenericMemoryAdapter(db_path=self.db_path, agent_id="test")
        adapter.save("Session memory 1")
        adapter.save("Session memory 2")
        count = adapter.clear_session()
        self.assertEqual(count, 2)

    def test_langchain_adapter_save_context(self):
        from integrations.agent_framework_adapters import LangChainMemoryAdapter
        adapter = LangChainMemoryAdapter(db_path=self.db_path, agent_id="lc_test")
        adapter.save_context(
            {"input": "What is AI?"},
            {"response": "AI is artificial intelligence."},
        )
        vars_ = adapter.load_memory_variables({"input": "AI"})
        self.assertIn("history", vars_)

    def test_autogen_hook_recall(self):
        from integrations.agent_framework_adapters import AutoGenMemoryHook
        hook = AutoGenMemoryHook(db_path=self.db_path, agent_id="ag_test")
        hook.on_message_received("user", "Tell me about quantum computing.")
        hook.on_reply_generated("Quantum computing uses quantum bits (qubits).")
        text = hook.recall_as_text("quantum")
        self.assertIsInstance(text, str)

    def test_crewai_tool_save_and_search(self):
        from integrations.agent_framework_adapters import CrewAIMemoryTool
        tool = CrewAIMemoryTool(db_path=self.db_path, agent_id="crew_test")
        tools = tool.get_tools()
        self.assertEqual(len(tools), 2)

        save_fn = tools[0]["func"] if isinstance(tools[0], dict) else tools[0].func
        search_fn = tools[1]["func"] if isinstance(tools[1], dict) else tools[1].func

        result = save_fn("CrewAI memory test content")
        self.assertIn("Memory saved", result)

        search_result = search_fn("CrewAI memory")
        self.assertNotEqual(search_result, "No relevant memories found.")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestEnhancedMemoryStorage))
    suite.addTests(loader.loadTestsFromTestCase(TestAgentCollaboration))
    suite.addTests(loader.loadTestsFromTestCase(TestWorkflowOrchestrationEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestFineTuningEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestAgentFrameworkAdapters))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
