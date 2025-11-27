#!/usr/bin/env python3
"""
Resource Monitor for Parallel Agent Execution
Monitors system resources to prevent overwhelming the laptop
"""

import psutil
from typing import Dict, Literal
from dataclasses import dataclass
from datetime import datetime

# Resource thresholds
CPU_THRESHOLD_SAFE = 0.6    # 60%
RAM_THRESHOLD_SAFE = 0.7    # 70%
CPU_THRESHOLD_DANGER = 0.8  # 80%
RAM_THRESHOLD_DANGER = 0.85 # 85%
MAX_AGENTS_PER_SESSION = 5

ResourceZone = Literal["safe", "warning", "danger"]

@dataclass
class ResourceStatus:
    """Current system resource status"""
    cpu_percent: float
    ram_percent: float
    zone: ResourceZone
    can_spawn: bool
    max_agents: int
    current_agents: int
    reason: str
    timestamp: str

def get_resource_status(current_agent_count: int = 0) -> ResourceStatus:
    """
    Get current system resource status

    Args:
        current_agent_count: Number of currently running agents

    Returns:
        ResourceStatus with current metrics and spawn decision
    """
    # Get CPU and RAM usage
    cpu_percent = psutil.cpu_percent(interval=0.5) / 100.0  # 0-1 scale
    ram_percent = psutil.virtual_memory().percent / 100.0   # 0-1 scale

    # Determine resource zone
    if cpu_percent >= CPU_THRESHOLD_DANGER or ram_percent >= RAM_THRESHOLD_DANGER:
        zone = "danger"
        max_agents = 1  # Minimal parallelization
        can_spawn = current_agent_count < max_agents
        reason = f"High resource usage: CPU {cpu_percent*100:.1f}%, RAM {ram_percent*100:.1f}%"
    elif cpu_percent >= CPU_THRESHOLD_SAFE or ram_percent >= RAM_THRESHOLD_SAFE:
        zone = "warning"
        max_agents = 3  # Conservative parallelization
        can_spawn = current_agent_count < max_agents
        reason = f"Moderate resource usage: CPU {cpu_percent*100:.1f}%, RAM {ram_percent*100:.1f}%"
    else:
        zone = "safe"
        max_agents = MAX_AGENTS_PER_SESSION  # Full parallelization
        can_spawn = current_agent_count < max_agents
        reason = f"Low resource usage: CPU {cpu_percent*100:.1f}%, RAM {ram_percent*100:.1f}%"

    return ResourceStatus(
        cpu_percent=cpu_percent,
        ram_percent=ram_percent,
        zone=zone,
        can_spawn=can_spawn,
        max_agents=max_agents,
        current_agents=current_agent_count,
        reason=reason,
        timestamp=datetime.now().isoformat()
    )

def get_recommended_parallelism(task_count: int, current_agent_count: int = 0) -> Dict:
    """
    Get recommended parallelism strategy based on resources and task count

    Args:
        task_count: Number of tasks to execute
        current_agent_count: Number of currently running agents

    Returns:
        Dict with strategy recommendation
    """
    status = get_resource_status(current_agent_count)

    # Calculate how many tasks can run in parallel
    available_slots = max(0, status.max_agents - status.current_agents)
    parallel_tasks = min(task_count, available_slots)
    queued_tasks = max(0, task_count - parallel_tasks)

    # Determine strategy
    if status.zone == "safe":
        strategy = "parallel"
        description = "Resources available for full parallelization"
    elif status.zone == "warning":
        strategy = "mixed"
        description = "Limited parallelization with queuing"
    else:  # danger
        strategy = "sequential"
        description = "High resource usage - sequential execution recommended"

    return {
        "strategy": strategy,
        "parallel_tasks": parallel_tasks,
        "queued_tasks": queued_tasks,
        "resource_status": {
            "cpu_percent": f"{status.cpu_percent*100:.1f}%",
            "ram_percent": f"{status.ram_percent*100:.1f}%",
            "zone": status.zone,
            "max_agents": status.max_agents,
            "current_agents": status.current_agents
        },
        "description": description,
        "reason": status.reason
    }

def check_agent_limit(current_agent_count: int) -> tuple[bool, str]:
    """
    Check if we can spawn another agent

    Args:
        current_agent_count: Number of currently running agents

    Returns:
        Tuple of (can_spawn: bool, reason: str)
    """
    status = get_resource_status(current_agent_count)

    if not status.can_spawn:
        return False, f"Cannot spawn agent: {status.reason}"

    return True, f"Can spawn agent: {status.max_agents - status.current_agents} slots available"

def get_system_info() -> Dict:
    """Get detailed system information"""
    cpu_count = psutil.cpu_count(logical=True)
    ram_total = psutil.virtual_memory().total / (1024**3)  # GB

    return {
        "cpu": {
            "count": cpu_count,
            "percent": psutil.cpu_percent(interval=0.5),
            "per_cpu": psutil.cpu_percent(interval=0.5, percpu=True)
        },
        "ram": {
            "total_gb": round(ram_total, 2),
            "available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
            "percent": psutil.virtual_memory().percent
        },
        "thresholds": {
            "cpu_safe": f"{CPU_THRESHOLD_SAFE*100}%",
            "cpu_danger": f"{CPU_THRESHOLD_DANGER*100}%",
            "ram_safe": f"{RAM_THRESHOLD_SAFE*100}%",
            "ram_danger": f"{RAM_THRESHOLD_DANGER*100}%",
            "max_agents": MAX_AGENTS_PER_SESSION
        }
    }

# Example usage
if __name__ == "__main__":
    import json

    print("🖥️  Resource Monitor Test\n")

    # Get system info
    info = get_system_info()
    print("System Info:")
    print(json.dumps(info, indent=2))
    print()

    # Check resource status
    status = get_resource_status(current_agent_count=0)
    print(f"Resource Status: {status.zone.upper()}")
    print(f"CPU: {status.cpu_percent*100:.1f}%")
    print(f"RAM: {status.ram_percent*100:.1f}%")
    print(f"Can spawn: {status.can_spawn}")
    print(f"Max agents: {status.max_agents}")
    print(f"Reason: {status.reason}")
    print()

    # Get recommendation for 5 tasks
    recommendation = get_recommended_parallelism(task_count=5, current_agent_count=0)
    print("Recommendation for 5 tasks:")
    print(json.dumps(recommendation, indent=2))
