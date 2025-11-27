# Parallel Agent Execution System

## Architecture

```
Claude Code Session (Branch: "main")
    ↓
Task Coordinator (Jarvis)
    ↓
Resource Monitor → Check CPU/RAM
    ↓
┌─────────────────┬─────────────────┬─────────────────┐
│ Agent 1         │ Agent 2         │ Agent 3         │
│ (Branch: main)  │ (Branch: main)  │ (Branch: main)  │
│ Task: Search    │ Task: Analyze   │ Task: Test      │
└─────────────────┴─────────────────┴─────────────────┘
    ↓                   ↓                   ↓
Hive-Mind Memory (Shared Knowledge Pool)
```

## Components

### 1. Resource Monitor
- **Purpose**: Check system resources before spawning agents
- **Metrics**: CPU usage, RAM usage, agent count
- **Thresholds**:
  - Safe zone: <60% CPU, <70% RAM → Spawn freely
  - Warning zone: 60-80% CPU, 70-85% RAM → Spawn conservatively
  - Danger zone: >80% CPU, >85% RAM → Queue tasks

### 2. Task Coordinator
- **Purpose**: Manage parallel task execution
- **Features**:
  - Branch context propagation (agents inherit parent branch)
  - Task queuing when resources are constrained
  - Priority-based scheduling
  - Learning from execution patterns

### 3. Parallelization Learner
- **Purpose**: Learn which tasks benefit from parallelization
- **Stores in Hive-Mind**:
  - Task type → parallelization benefit score
  - Common bottlenecks
  - Resource usage patterns
  - Success/failure rates

## MCP Tools

### `spawn_parallel_tasks`
**Smart parallel execution with resource awareness**

```json
{
  "tasks": [
    {
      "description": "Search codebase for authentication logic",
      "type": "explore",
      "priority": "high"
    },
    {
      "description": "Analyze security vulnerabilities",
      "type": "analyze",
      "priority": "medium"
    }
  ],
  "branch_id": "security-audit",
  "strategy": "auto"
}
```

**Strategies**:
- `auto` - Let Jarvis decide based on resources
- `parallel` - Force parallel (if resources allow)
- `sequential` - Force sequential
- `adaptive` - Learn from past executions

### `get_task_stats`
**View running/queued tasks**

Returns:
- Currently running agents
- Queued tasks
- Resource usage
- Branch context

### `learn_parallelization`
**Store learnings about parallel execution**

```json
{
  "task_type": "codebase_search",
  "parallel_benefit": 0.85,
  "notes": "Searching multiple directories in parallel saves 60% time",
  "resource_cost": {"cpu": 0.4, "ram": 0.2}
}
```

## Usage Patterns

### Pattern 1: Independent Research Tasks
**Good for parallelization**

```
Task 1: Search for API endpoints
Task 2: Search for database queries
Task 3: Search for authentication code
```

All can run simultaneously, no dependencies.

### Pattern 2: Sequential Dependencies
**Bad for parallelization**

```
Task 1: Fetch data from API
Task 2: Parse the fetched data (depends on Task 1)
Task 3: Store parsed data (depends on Task 2)
```

Must run sequentially.

### Pattern 3: Map-Reduce
**Perfect for parallelization**

```
Task 1-N: Analyze each file in directory (parallel)
Task N+1: Aggregate results (sequential)
```

Parallel analysis, single aggregation.

## Resource Management

### Safe Spawning Limits
```python
MAX_AGENTS_PER_SESSION = 5
CPU_THRESHOLD_SAFE = 0.6    # 60%
RAM_THRESHOLD_SAFE = 0.7    # 70%
CPU_THRESHOLD_DANGER = 0.8  # 80%
RAM_THRESHOLD_DANGER = 0.85 # 85%
```

### Task Priorities
1. **Critical** - User-blocking operations
2. **High** - Important but not blocking
3. **Medium** - Optimization tasks
4. **Low** - Background analysis

## Learning Loop

```
1. User requests parallel tasks
2. Coordinator checks resources
3. Spawn tasks (parallel or queue)
4. Monitor execution time, resource usage
5. Store learnings in hive-mind:
   - Task type → parallel benefit
   - Resource patterns
   - Common bottlenecks
6. Next time: Use learnings to optimize spawning
```

## Safety Features

### Silent Overseer Integration
- Monitor for resource-intensive tasks
- Prevent runaway agents
- Alert on excessive resource usage
- Auto-kill tasks exceeding thresholds

### Graceful Degradation
1. **Ideal**: All tasks parallel
2. **Constrained**: Mix of parallel + queued
3. **Resource-starved**: Sequential execution
4. **Emergency**: Cancel low-priority tasks

## Benefits

1. **Speed**: Independent tasks run simultaneously
2. **Resource-aware**: Never overwhelm the laptop
3. **Learning**: Gets smarter over time
4. **Branch context**: All agents share hive-mind knowledge
5. **Failsafe**: Graceful degradation under load

## Example Scenarios

### Scenario 1: Security Audit
```
User: "Audit the codebase for security issues"

Jarvis spawns 3 parallel agents:
1. Search for SQL injection patterns
2. Search for XSS vulnerabilities
3. Search for authentication issues

All agents inherit branch "security-audit"
All store findings in hive-mind
Parent session aggregates results
```

### Scenario 2: Refactoring Analysis
```
User: "Analyze which functions need refactoring"

Resources: CPU 75%, RAM 80% (Warning zone)

Jarvis decision:
- Spawn 2 agents (not 5)
- Queue remaining tasks
- Process queue as resources free up
```

### Scenario 3: Learning Pattern
```
Jarvis notices:
- "codebase_search" tasks: 90% faster in parallel
- "api_call" tasks: 10% faster in parallel (network bound)

Next time:
- Always parallelize codebase searches
- Run API calls sequentially (not worth the overhead)
```

## Integration with Existing System

### Hive-Mind Memory
- Store parallelization learnings
- Share context across agents
- Aggregate findings from parallel tasks

### Silent Overseer
- Monitor resource usage
- Prevent dangerous parallelization
- Kill runaway agents

### Skilltree
- Add skills for common parallel patterns
- Reuse proven parallelization strategies
- Track which skills benefit from parallel execution

---

**Next**: Implement resource monitor and task coordinator
