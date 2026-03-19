"""
Nova Memory 2.0 — Workflow Orchestration Engine

Manages multi-agent workflows with:
- Dependency-aware task scheduling (tasks only start when all deps complete)
- Pause / resume support
- Per-task and per-workflow callbacks
- Progress tracking and status reporting

FIX: Previous version called _execute_task for ALL pending tasks at once in
start_workflow(), ignoring declared dependencies.  Tasks are now only started
if their dependency list is empty or all dependencies are already completed.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class WorkflowStatus(Enum):
    DRAFT     = "draft"
    ACTIVE    = "active"
    COMPLETED = "completed"
    FAILED    = "failed"
    PAUSED    = "paused"


class TaskStatus(Enum):
    PENDING     = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED   = "completed"
    FAILED      = "failed"
    SKIPPED     = "skipped"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """A single unit of work within a workflow."""
    task_id:        str = field(default_factory=lambda: str(uuid.uuid4()))
    name:           str = ""
    description:    str = ""
    assigned_agent: str = ""
    status:         TaskStatus = TaskStatus.PENDING
    dependencies:   List[str] = field(default_factory=list)
    start_time:     Optional[str] = None
    end_time:       Optional[str] = None
    result:         Optional[Dict[str, Any]] = None
    error:          Optional[str] = None


@dataclass
class Workflow:
    """A directed acyclic graph of tasks executed by agents."""
    workflow_id:  str = field(default_factory=lambda: str(uuid.uuid4()))
    name:         str = ""
    description:  str = ""
    status:       WorkflowStatus = WorkflowStatus.DRAFT
    tasks:        Dict[str, Task] = field(default_factory=dict)
    created_at:   str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at:   Optional[str] = None
    completed_at: Optional[str] = None
    metadata:     Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class WorkflowOrchestrationEngine:
    """
    Orchestrates multi-agent workflows with dependency-aware scheduling.

    Usage::

        engine = WorkflowOrchestrationEngine()
        engine.register_task_callback("my_agent", my_callback_fn)
        wf_id = engine.create_workflow(name="...", description="...", tasks=[...])
        engine.start_workflow(wf_id, input_data={...})
    """

    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.task_callbacks: Dict[str, Callable] = {}
        self.workflow_callbacks: Dict[str, Callable] = {}

    # ------------------------------------------------------------------
    # Workflow lifecycle
    # ------------------------------------------------------------------

    def create_workflow(
        self,
        name: str,
        description: str,
        tasks: List[Dict[str, Any]],
        metadata: Optional[Dict] = None,
    ) -> str:
        """
        Register a new workflow.

        Each task dict should contain:
            - ``name`` (str, required)
            - ``assigned_agent`` (str, required)
            - ``task_id`` (str, optional — auto-generated if absent)
            - ``description`` (str, optional)
            - ``dependencies`` (List[str], optional) — list of task_ids that
              must complete before this task starts

        Returns the workflow ID.
        """
        workflow = Workflow(
            name=name,
            description=description,
            metadata=metadata or {},
        )

        for task_def in tasks:
            task = Task(
                task_id=task_def.get("task_id", str(uuid.uuid4())),
                name=task_def.get("name", "Unnamed Task"),
                description=task_def.get("description", ""),
                assigned_agent=task_def.get("assigned_agent", ""),
                dependencies=task_def.get("dependencies", []),
            )
            workflow.tasks[task.task_id] = task

        self.workflows[workflow.workflow_id] = workflow
        print(f"[OK] Workflow created  id={workflow.workflow_id}  name={name}  "
              f"tasks={len(workflow.tasks)}")
        return workflow.workflow_id

    def start_workflow(
        self,
        workflow_id: str,
        input_data: Optional[Dict] = None,
    ) -> bool:
        """
        Transition a DRAFT workflow to ACTIVE and execute ready tasks.

        FIX: Only tasks with no dependencies (or whose dependencies are all
        already COMPLETED) are started immediately.  Dependent tasks are
        triggered lazily as their prerequisites finish.
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            print(f"[ERROR] Workflow not found: {workflow_id}")
            return False

        if workflow.status != WorkflowStatus.DRAFT:
            print(f"[ERROR] Workflow {workflow_id} is not in DRAFT status "
                  f"(current: {workflow.status.value})")
            return False

        workflow.status = WorkflowStatus.ACTIVE
        workflow.started_at = datetime.now(timezone.utc).isoformat()
        workflow.metadata["input_data"] = input_data or {}

        print(f"[OK] Workflow started  id={workflow_id}  name={workflow.name}")

        # Start only tasks whose dependencies are already satisfied
        for task in list(workflow.tasks.values()):
            if task.status == TaskStatus.PENDING and self._deps_satisfied(workflow, task):
                self._execute_task(workflow_id, task.task_id)

        return True

    def pause_workflow(self, workflow_id: str) -> bool:
        """Pause an active workflow (in-flight tasks are not interrupted)."""
        workflow = self.workflows.get(workflow_id)
        if workflow and workflow.status == WorkflowStatus.ACTIVE:
            workflow.status = WorkflowStatus.PAUSED
            print(f"[OK] Workflow paused: {workflow_id}")
            return True
        return False

    def resume_workflow(self, workflow_id: str) -> bool:
        """Resume a paused workflow by re-scheduling ready tasks."""
        workflow = self.workflows.get(workflow_id)
        if not workflow or workflow.status != WorkflowStatus.PAUSED:
            return False

        workflow.status = WorkflowStatus.ACTIVE
        for task in list(workflow.tasks.values()):
            if task.status == TaskStatus.PENDING and self._deps_satisfied(workflow, task):
                self._execute_task(workflow_id, task.task_id)

        print(f"[OK] Workflow resumed: {workflow_id}")
        return True

    # ------------------------------------------------------------------
    # Task execution
    # ------------------------------------------------------------------

    def _deps_satisfied(self, workflow: Workflow, task: Task) -> bool:
        """Return True if all of task's dependencies are COMPLETED."""
        for dep_id in task.dependencies:
            dep_task = workflow.tasks.get(dep_id)
            if dep_task is None or dep_task.status != TaskStatus.COMPLETED:
                return False
        return True

    def _execute_task(self, workflow_id: str, task_id: str):
        """
        Execute a single task synchronously.

        After completion, any tasks that were waiting on this one are
        checked and started if their dependencies are now satisfied.
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return

        task = workflow.tasks.get(task_id)
        if not task or task.status != TaskStatus.PENDING:
            return

        # Guard: skip if paused
        if workflow.status == WorkflowStatus.PAUSED:
            return

        task.status = TaskStatus.IN_PROGRESS
        task.start_time = datetime.now(timezone.utc).isoformat()

        try:
            callback = self.task_callbacks.get(task.assigned_agent)
            if callback:
                task.result = callback(task, workflow_id, workflow)
            else:
                task.result = {
                    "status": "completed",
                    "message": f"Task '{task.name}' completed (no callback registered)",
                }

            task.status = TaskStatus.COMPLETED
            task.end_time = datetime.now(timezone.utc).isoformat()
            print(f"[OK] Task completed  id={task_id}  name={task.name}")

            # Trigger downstream tasks
            for downstream in workflow.tasks.values():
                if (
                    downstream.status == TaskStatus.PENDING
                    and self._deps_satisfied(workflow, downstream)
                ):
                    self._execute_task(workflow_id, downstream.task_id)

            self._check_workflow_completion(workflow_id)

        except Exception as exc:
            task.status = TaskStatus.FAILED
            task.error = str(exc)
            task.end_time = datetime.now(timezone.utc).isoformat()
            workflow.status = WorkflowStatus.FAILED
            workflow.completed_at = datetime.now(timezone.utc).isoformat()

            cb = self.workflow_callbacks.get(workflow_id)
            if cb:
                cb(workflow)

            logger.exception("Task %s failed: %s", task_id, exc)
            print(f"[ERROR] Task failed  id={task_id}  error={exc}")

    def _check_workflow_completion(self, workflow_id: str):
        """Mark workflow as COMPLETED when all tasks are done."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return

        terminal = {TaskStatus.COMPLETED, TaskStatus.SKIPPED}
        if all(t.status in terminal for t in workflow.tasks.values()):
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.now(timezone.utc).isoformat()
            print(f"[OK] Workflow completed  id={workflow_id}  name={workflow.name}")

            cb = self.workflow_callbacks.get(workflow_id)
            if cb:
                cb(workflow)

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def register_task_callback(self, agent_id: str, callback: Callable):
        """Register a function to be called when a task is assigned to ``agent_id``."""
        self.task_callbacks[agent_id] = callback
        print(f"[OK] Task callback registered for agent: {agent_id}")

    def register_workflow_callback(self, workflow_id: str, callback: Callable):
        """Register a function to be called when a workflow completes or fails."""
        self.workflow_callbacks[workflow_id] = callback
        print(f"[OK] Workflow callback registered: {workflow_id}")

    # ------------------------------------------------------------------
    # Status & progress
    # ------------------------------------------------------------------

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Return a full status snapshot of the workflow."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None

        return {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "description": workflow.description,
            "status": workflow.status.value,
            "tasks": {
                tid: {
                    "name": t.name,
                    "status": t.status.value,
                    "assigned_agent": t.assigned_agent,
                    "dependencies": t.dependencies,
                    "start_time": t.start_time,
                    "end_time": t.end_time,
                    "result": t.result,
                    "error": t.error,
                }
                for tid, t in workflow.tasks.items()
            },
            "created_at": workflow.created_at,
            "started_at": workflow.started_at,
            "completed_at": workflow.completed_at,
            "metadata": workflow.metadata,
        }

    def get_workflow_progress(self, workflow_id: str) -> Dict[str, Any]:
        """Return completion percentage and task counts."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return {"workflow_id": workflow_id, "progress": 0.0}

        total = len(workflow.tasks)
        if total == 0:
            return {"workflow_id": workflow_id, "progress": 100.0, "total_tasks": 0}

        completed = sum(
            1 for t in workflow.tasks.values()
            if t.status == TaskStatus.COMPLETED
        )
        failed = sum(
            1 for t in workflow.tasks.values()
            if t.status == TaskStatus.FAILED
        )

        return {
            "workflow_id": workflow_id,
            "total_tasks": total,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "pending_tasks": total - completed - failed,
            "progress": round((completed / total) * 100, 1),
        }

    def get_all_workflows(self) -> List[Dict[str, Any]]:
        """Return status snapshots for all registered workflows."""
        return [
            self.get_workflow_status(wid) for wid in self.workflows
        ]


# ---------------------------------------------------------------------------
# Quick smoke-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import time

    print("Nova Memory 2.0 — Workflow Orchestration Engine")
    print("=" * 60)

    engine = WorkflowOrchestrationEngine()

    def agent_callback(task, workflow_id, workflow):
        print(f"   [{task.assigned_agent}] Executing: {task.name}")
        return {"status": "completed", "task": task.name}

    for agent in ["healthcare_agent", "data_analyzer", "communication_coordinator"]:
        engine.register_task_callback(agent, agent_callback)

    wf_id = engine.create_workflow(
        name="Healthcare Patient Care",
        description="End-to-end patient care workflow",
        tasks=[
            {
                "task_id": "t1",
                "name": "Retrieve Patient Data",
                "assigned_agent": "healthcare_agent",
                "dependencies": [],
            },
            {
                "task_id": "t2",
                "name": "Analyse Treatment Needs",
                "assigned_agent": "data_analyzer",
                "dependencies": ["t1"],  # must wait for t1
            },
            {
                "task_id": "t3",
                "name": "Coordinate Care Plan",
                "assigned_agent": "communication_coordinator",
                "dependencies": ["t2"],  # must wait for t2
            },
            {
                "task_id": "t4",
                "name": "Generate Report",
                "assigned_agent": "healthcare_agent",
                "dependencies": ["t3"],  # must wait for t3
            },
        ],
    )

    engine.start_workflow(wf_id, {"patient_id": "patient_123"})

    status = engine.get_workflow_status(wf_id)
    progress = engine.get_workflow_progress(wf_id)

    print(f"\nFinal status:   {status['status']}")
    print(f"Progress:       {progress['progress']:.0f}%")
    print("\nTask breakdown:")
    for tid, t in status["tasks"].items():
        print(f"  {t['name']}: {t['status']}")

    print("\n[OK] Workflow orchestration smoke test complete")
