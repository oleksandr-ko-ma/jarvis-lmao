#!/usr/bin/env python3
"""
Task Coordinator for Parallel Agent Execution
Manages task spawning, queuing, and branch context propagation
"""

import json
from typing import List, Dict, Literal, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import hashlib

try:
    from .resource_monitor import get_recommended_parallelism, get_resource_status
except ImportError:
    from resource_monitor import get_recommended_parallelism, get_resource_status

class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

class TaskStatus(Enum):
    """Task execution status"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ParallelTask:
    """A task to be executed by an agent"""
    id: str
    description: str
    task_type: str  # explore, analyze, test, search, etc.
    priority: TaskPriority
    branch_id: str
    status: TaskStatus = TaskStatus.QUEUED
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['priority'] = self.priority.name
        data['status'] = self.status.value
        return data

@dataclass
class ExecutionPlan:
    """Plan for executing tasks with resource awareness"""
    strategy: Literal["parallel", "mixed", "sequential"]
    parallel_tasks: List[ParallelTask]
    queued_tasks: List[ParallelTask]
    resource_status: Dict
    total_tasks: int
    estimated_duration: Optional[str] = None
    branch_id: str = "main"

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "strategy": self.strategy,
            "parallel_tasks": [t.to_dict() for t in self.parallel_tasks],
            "queued_tasks": [t.to_dict() for t in self.queued_tasks],
            "resource_status": self.resource_status,
            "total_tasks": self.total_tasks,
            "estimated_duration": self.estimated_duration,
            "branch_id": self.branch_id
        }

class TaskCoordinator:
    """Coordinates parallel task execution with resource awareness"""

    def __init__(self):
        self.tasks: Dict[str, ParallelTask] = {}
        self.execution_history: List[Dict] = []

    def generate_task_id(self, description: str, branch_id: str) -> str:
        """Generate unique task ID"""
        timestamp = datetime.now().isoformat()
        content = f"{description}{branch_id}{timestamp}"
        hash_obj = hashlib.sha256(content.encode())
        return hash_obj.hexdigest()[:16]

    def create_execution_plan(
        self,
        task_descriptions: List[Dict],
        branch_id: str = "main",
        strategy: Literal["auto", "parallel", "sequential", "adaptive"] = "auto"
    ) -> ExecutionPlan:
        """
        Create an execution plan for tasks

        Args:
            task_descriptions: List of dicts with 'description', 'type', 'priority'
            branch_id: Branch context for all tasks
            strategy: Execution strategy

        Returns:
            ExecutionPlan with task allocation
        """
        # Create task objects
        tasks = []
        for desc in task_descriptions:
            task_id = self.generate_task_id(desc['description'], branch_id)
            task = ParallelTask(
                id=task_id,
                description=desc['description'],
                task_type=desc.get('type', 'general'),
                priority=TaskPriority[desc.get('priority', 'MEDIUM').upper()],
                branch_id=branch_id,
                metadata=desc.get('metadata', {})
            )
            tasks.append(task)
            self.tasks[task_id] = task

        # Sort by priority
        tasks.sort(key=lambda t: t.priority.value)

        # Get resource recommendation
        current_running = len([t for t in self.tasks.values() if t.status == TaskStatus.RUNNING])
        recommendation = get_recommended_parallelism(len(tasks), current_running)

        # Allocate tasks based on strategy
        if strategy == "sequential":
            parallel_tasks = tasks[:1]
            queued_tasks = tasks[1:]
            exec_strategy = "sequential"
        elif strategy == "parallel":
            parallel_tasks = tasks[:recommendation['parallel_tasks']]
            queued_tasks = tasks[recommendation['parallel_tasks']:]
            exec_strategy = "parallel"
        else:  # auto or adaptive
            parallel_tasks = tasks[:recommendation['parallel_tasks']]
            queued_tasks = tasks[recommendation['parallel_tasks']:]
            exec_strategy = recommendation['strategy']

        # Mark parallel tasks as running
        for task in parallel_tasks:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now().isoformat()

        return ExecutionPlan(
            strategy=exec_strategy,
            parallel_tasks=parallel_tasks,
            queued_tasks=queued_tasks,
            resource_status=recommendation['resource_status'],
            total_tasks=len(tasks),
            branch_id=branch_id
        )

    def get_task_stats(self) -> Dict:
        """Get statistics about current tasks"""
        running = [t for t in self.tasks.values() if t.status == TaskStatus.RUNNING]
        queued = [t for t in self.tasks.values() if t.status == TaskStatus.QUEUED]
        completed = [t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]
        failed = [t for t in self.tasks.values() if t.status == TaskStatus.FAILED]

        resource_status = get_resource_status(len(running))

        return {
            "total_tasks": len(self.tasks),
            "running": len(running),
            "queued": len(queued),
            "completed": len(completed),
            "failed": len(failed),
            "running_tasks": [t.to_dict() for t in running],
            "queued_tasks": [t.to_dict() for t in queued],
            "resource_status": {
                "cpu_percent": f"{resource_status.cpu_percent*100:.1f}%",
                "ram_percent": f"{resource_status.ram_percent*100:.1f}%",
                "zone": resource_status.zone,
                "can_spawn_more": resource_status.can_spawn
            }
        }

    def complete_task(self, task_id: str, result: str, success: bool = True):
        """Mark a task as completed"""
        if task_id not in self.tasks:
            return

        task = self.tasks[task_id]
        task.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
        task.completed_at = datetime.now().isoformat()
        task.result = result if success else None
        task.error = result if not success else None

        # Record in execution history
        self.execution_history.append({
            "task_id": task_id,
            "description": task.description,
            "task_type": task.task_type,
            "branch_id": task.branch_id,
            "success": success,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
            "duration_seconds": self._calculate_duration(task.started_at, task.completed_at)
        })

    def _calculate_duration(self, start: Optional[str], end: Optional[str]) -> Optional[float]:
        """Calculate duration in seconds"""
        if not start or not end:
            return None
        try:
            start_dt = datetime.fromisoformat(start)
            end_dt = datetime.fromisoformat(end)
            return (end_dt - start_dt).total_seconds()
        except:
            return None

    def get_parallelization_learnings(self) -> Dict:
        """Analyze execution history to learn parallelization patterns"""
        if not self.execution_history:
            return {"message": "No execution history yet"}

        # Group by task type
        by_type = {}
        for execution in self.execution_history:
            task_type = execution['task_type']
            if task_type not in by_type:
                by_type[task_type] = []
            by_type[task_type].append(execution)

        # Calculate statistics per type
        learnings = {}
        for task_type, executions in by_type.items():
            successful = [e for e in executions if e['success']]
            if not successful:
                continue

            avg_duration = sum(e['duration_seconds'] for e in successful if e['duration_seconds']) / len(successful)
            success_rate = len(successful) / len(executions)

            learnings[task_type] = {
                "total_executions": len(executions),
                "success_rate": round(success_rate, 2),
                "avg_duration_seconds": round(avg_duration, 2),
                "parallel_benefit_score": self._estimate_parallel_benefit(task_type, executions),
                "recommendation": self._get_parallelization_recommendation(task_type, avg_duration, success_rate)
            }

        return learnings

    def _estimate_parallel_benefit(self, task_type: str, executions: List[Dict]) -> float:
        """Estimate how much this task type benefits from parallelization (0-1)"""
        # Simple heuristic: tasks that complete quickly and have high success rate benefit more
        successful = [e for e in executions if e['success'] and e['duration_seconds']]
        if not successful:
            return 0.5  # neutral

        avg_duration = sum(e['duration_seconds'] for e in successful) / len(successful)

        # Short tasks (< 30s) benefit more from parallelization
        # Long tasks (> 120s) might be I/O bound or CPU intensive
        if avg_duration < 30:
            return 0.9
        elif avg_duration < 60:
            return 0.7
        elif avg_duration < 120:
            return 0.5
        else:
            return 0.3

    def _get_parallelization_recommendation(self, task_type: str, avg_duration: float, success_rate: float) -> str:
        """Get recommendation for parallelizing this task type"""
        if success_rate < 0.5:
            return "Not recommended - low success rate"
        elif avg_duration < 30:
            return "Highly recommended - quick tasks benefit from parallelization"
        elif avg_duration < 120:
            return "Recommended - moderate duration tasks parallelize well"
        else:
            return "Consider sequential - long-running tasks may be resource-intensive"

# Example usage
if __name__ == "__main__":
    coordinator = TaskCoordinator()

    # Create execution plan
    tasks = [
        {"description": "Search codebase for authentication", "type": "search", "priority": "high"},
        {"description": "Analyze security vulnerabilities", "type": "analyze", "priority": "high"},
        {"description": "Test API endpoints", "type": "test", "priority": "medium"},
        {"description": "Generate documentation", "type": "document", "priority": "low"},
        {"description": "Refactor helper functions", "type": "refactor", "priority": "medium"}
    ]

    print("🤖 Task Coordinator Test\n")
    plan = coordinator.create_execution_plan(tasks, branch_id="security-audit", strategy="auto")
    print("Execution Plan:")
    print(json.dumps(plan.to_dict(), indent=2))
    print()

    # Get task stats
    stats = coordinator.get_task_stats()
    print("Task Statistics:")
    print(json.dumps(stats, indent=2))
