"""
Nova Memory 2.0 - Workflow Orchestration Engine

This module provides visual workflow building, task assignment, progress monitoring,
and success/failure handling for multi-agent workflows.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, field

class WorkflowStatus(Enum):
    """Workflow status states"""
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

class TaskStatus(Enum):
    """Task status states"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class Task:
    """Represents a task in a workflow"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    assigned_agent: str
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = field(default_factory=list)
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@dataclass
class Workflow:
    """Represents a complete workflow"""
    workflow_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    status: WorkflowStatus = WorkflowStatus.DRAFT
    tasks: Dict[str, Task] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class WorkflowOrchestrationEngine:
    """
    Workflow orchestration engine for managing multi-agent workflows
    """

    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.task_callbacks: Dict[str, Callable] = {}
        self.workflow_callbacks: Dict[str, Callable] = {}

    def create_workflow(self, name: str, description: str,
                       tasks: List[Dict[str, Any]],
                       metadata: Optional[Dict] = None) -> str:
        """
        Create a new workflow

        Args:
            name: Workflow name
            description: Workflow description
            tasks: List of task definitions
            metadata: Optional metadata

        Returns:
            Workflow ID
        """
        workflow = Workflow(
            name=name,
            description=description,
            tasks={},
            metadata=metadata or {}
        )

        # Create tasks
        for task_def in tasks:
            task = Task(
                name=task_def["name"],
                description=task_def.get("description", ""),
                assigned_agent=task_def["assigned_agent"],
                dependencies=task_def.get("dependencies", []),
                task_id=task_def.get("task_id", str(uuid.uuid4()))
            )
            workflow.tasks[task.task_id] = task

        workflow_id = workflow.workflow_id
        self.workflows[workflow_id] = workflow

        print(f"[OK] Workflow created: {name} ({workflow_id})")
        return workflow_id

    def start_workflow(self, workflow_id: str, input_data: Optional[Dict] = None) -> bool:
        """
        Start a workflow execution

        Args:
            workflow_id: Workflow ID
            input_data: Input data for the workflow

        Returns:
            Success status
        """
        workflow = self.workflows.get(workflow_id)

        if not workflow:
            print(f"[ERROR] Workflow {workflow_id} not found")
            return False

        if workflow.status != WorkflowStatus.DRAFT:
            print(f"[ERROR] Workflow {workflow_id} is not in DRAFT status")
            return False

        # Update workflow status
        workflow.status = WorkflowStatus.ACTIVE
        workflow.started_at = datetime.now().isoformat()
        workflow.metadata["input_data"] = input_data or {}

        # Start all pending tasks
        for task in workflow.tasks.values():
            if task.status == TaskStatus.PENDING:
                self._execute_task(workflow_id, task.task_id)

        print(f"[OK] Workflow started: {workflow.name}")
        return True

    def _execute_task(self, workflow_id: str, task_id: str):
        """
        Execute a single task

        Args:
            workflow_id: Workflow ID
            task_id: Task ID
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return

        task = workflow.tasks.get(task_id)
        if not task:
            return

        # Check dependencies
        if task.dependencies:
            all_dependencies_completed = all(
                workflow.tasks.get(dep).status == TaskStatus.COMPLETED
                for dep in task.dependencies
            )

            if not all_dependencies_completed:
                return

        # Update task status
        task.status = TaskStatus.IN_PROGRESS
        task.start_time = datetime.now().isoformat()

        # Execute task
        try:
            # Call registered callback
            callback = self.task_callbacks.get(task.assigned_agent)
            if callback:
                result = callback(task, workflow_id, workflow)
                task.result = result
            else:
                # Simulate task execution
                task.result = {"status": "completed", "message": "Task completed successfully"}

            task.status = TaskStatus.COMPLETED
            task.end_time = datetime.now().isoformat()

            # Check if workflow is complete
            self._check_workflow_completion(workflow_id)

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.end_time = datetime.now().isoformat()

            # Mark workflow as failed
            workflow.status = WorkflowStatus.FAILED
            workflow.completed_at = datetime.now().isoformat()

            # Call workflow callback
            if self.workflow_callbacks.get(workflow_id):
                self.workflow_callbacks[workflow_id](workflow)

            print(f"[ERROR] Task {task_id} failed: {e}")

    def _check_workflow_completion(self, workflow_id: str):
        """Check if workflow is complete"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return

        # Check if all tasks are completed
        all_completed = all(
            task.status in [TaskStatus.COMPLETED, TaskStatus.SKIPPED]
            for task in workflow.tasks.values()
        )

        if all_completed:
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.now().isoformat()

            print(f"[OK] Workflow completed: {workflow.name}")

            # Call workflow callback
            if self.workflow_callbacks.get(workflow_id):
                self.workflow_callbacks[workflow_id](workflow)

    def register_task_callback(self, agent_id: str, callback: Callable):
        """
        Register a callback for task execution

        Args:
            agent_id: Agent ID
            callback: Callback function
        """
        self.task_callbacks[agent_id] = callback
        print(f"[OK] Registered task callback for agent: {agent_id}")

    def register_workflow_callback(self, workflow_id: str, callback: Callable):
        """
        Register a callback for workflow completion

        Args:
            workflow_id: Workflow ID
            callback: Callback function
        """
        self.workflow_callbacks[workflow_id] = callback
        print(f"[OK] Registered workflow callback for: {workflow_id}")

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a workflow"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None

        return {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "description": workflow.description,
            "status": workflow.status.value,
            "tasks": {
                task_id: {
                    "name": task.name,
                    "status": task.status.value,
                    "assigned_agent": task.assigned_agent,
                    "start_time": task.start_time,
                    "end_time": task.end_time,
                    "result": task.result
                }
                for task_id, task in workflow.tasks.items()
            },
            "created_at": workflow.created_at,
            "started_at": workflow.started_at,
            "completed_at": workflow.completed_at,
            "metadata": workflow.metadata
        }

    def get_all_workflows(self) -> List[Dict[str, Any]]:
        """Get status of all workflows"""
        return [
            self.get_workflow_status(workflow_id)
            for workflow_id in self.workflows.keys()
        ]

    def pause_workflow(self, workflow_id: str) -> bool:
        """Pause a workflow"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return False

        if workflow.status == WorkflowStatus.ACTIVE:
            workflow.status = WorkflowStatus.PAUSED
            return True

        return False

    def resume_workflow(self, workflow_id: str) -> bool:
        """Resume a paused workflow"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return False

        if workflow.status == WorkflowStatus.PAUSED:
            workflow.status = WorkflowStatus.ACTIVE
            # Resume pending tasks
            for task in workflow.tasks.values():
                if task.status == TaskStatus.PENDING:
                    self._execute_task(workflow_id, task.task_id)
            return True

        return False

    def get_workflow_progress(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow progress percentage"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return {"workflow_id": workflow_id, "progress": 0}

        total_tasks = len(workflow.tasks)
        if total_tasks == 0:
            return {"workflow_id": workflow_id, "progress": 0}

        completed_tasks = sum(
            1 for task in workflow.tasks.values()
            if task.status == TaskStatus.COMPLETED
        )

        progress = (completed_tasks / total_tasks) * 100

        return {
            "workflow_id": workflow_id,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "pending_tasks": total_tasks - completed_tasks,
            "progress": progress
        }

# Demo and Testing
if __name__ == "__main__":
    print("Nova Memory 2.0 - Workflow Orchestration Engine")
    print("=" * 60)

    # Initialize engine
    engine = WorkflowOrchestrationEngine()

    # Register callbacks
    def healthcare_agent_callback(task, workflow_id, workflow):
        """Callback for healthcare agent tasks"""
        print(f"   [Healthcare Agent] Executing: {task.name}")
        time.sleep(1)  # Simulate work
        return {
            "status": "completed",
            "patient_data": {"id": "patient_123", "diagnosis": "diabetes_type_2"}
        }

    def data_analyzer_callback(task, workflow_id, workflow):
        """Callback for data analyzer agent tasks"""
        print(f"   [Data Analyzer] Executing: {task.name}")
        time.sleep(1)  # Simulate work
        return {
            "status": "completed",
            "analysis": {"trend": "stable", "recommendation": "continue_current_treatment"}
        }

    def communication_coordinator_callback(task, workflow_id, workflow):
        """Callback for communication coordinator agent tasks"""
        print(f"   [Communication Coordinator] Executing: {task.name}")
        time.sleep(1)  # Simulate work
        return {
            "status": "completed",
            "notification": "care_plan_shared_with_patient"
        }

    engine.register_task_callback("healthcare_agent", healthcare_agent_callback)
    engine.register_task_callback("data_analyzer", data_analyzer_callback)
    engine.register_task_callback("communication_coordinator", communication_coordinator_callback)

    # Create workflow
    print("\n1. Creating workflow...")

    workflow_id = engine.create_workflow(
        name="Healthcare Patient Care",
        description="Complete patient care workflow",
        tasks=[
            {
                "name": "Retrieve Patient Data",
                "description": "Fetch patient medical history",
                "assigned_agent": "healthcare_agent",
                "dependencies": []
            },
            {
                "name": "Analyze Treatment Needs",
                "description": "Analyze current treatment requirements",
                "assigned_agent": "data_analyzer",
                "dependencies": ["Retrieve Patient Data"]
            },
            {
                "name": "Coordinate Care Plan",
                "description": "Create and coordinate care plan",
                "assigned_agent": "communication_coordinator",
                "dependencies": ["Analyze Treatment Needs"]
            },
            {
                "name": "Generate Report",
                "description": "Generate comprehensive report",
                "assigned_agent": "healthcare_agent",
                "dependencies": ["Coordinate Care Plan"]
            }
        ],
        metadata={"priority": "high", "workflow_type": "healthcare"}
    )

    # Start workflow
    print("\n2. Starting workflow...")

    engine.start_workflow(workflow_id, {"patient_id": "patient_123"})

    # Simulate workflow execution (would normally be automatic)
    print("\n3. Simulating workflow execution...")
    time.sleep(2)

    # Get workflow status
    print("\n4. Workflow status:")

    status = engine.get_workflow_status(workflow_id)
    print(f"   Name: {status['name']}")
    print(f"   Status: {status['status']}")
    print(f"   Progress: {engine.get_workflow_progress(workflow_id)['progress']:.1f}%")

    print("\n   Tasks:")
    for task_id, task in status['tasks'].items():
        print(f"   - {task['name']}: {task['status']}")

    # Get all workflows
    print("\n5. All workflows:")

    all_workflows = engine.get_all_workflows()
    for wf in all_workflows:
        print(f"   - {wf['name']}: {wf['status']} ({engine.get_workflow_progress(wf['workflow_id'])['progress']:.1f}%)")

    print("\n✅ Workflow orchestration engine demo complete!")
    print("   This engine provides visual workflow building, task assignment,")
    print("   progress monitoring, and success/failure handling.")
