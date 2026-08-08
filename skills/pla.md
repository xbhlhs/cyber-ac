# PLA Skill — Process Lifecycle Agent

Load `agents/pla/AGENT.md` for your full role (5-layer closed-loop controller).

## Architecture

```
agents/pla/
  perception.py  → L1: 读SR+约束→ActivityContext
  planner.py     → L2: plan() + replan() + assess()
runtime/
  orchestrator.py → L3: dispatch(写队列+goal) + collect(格式验证)
  channel.py      → 文件消息通道
  protocol.py     → TaskContext / ExecutionResult
```

## Your Tools

### Python modules
```python
from agents.pla.perception import Perception
from agents.pla.planner import Planner
from runtime import Orchestrator

# L1
p = Perception('projects/sr1', 'D')
ctx = p.perceive()

# L2
planner = Planner('D')
plan = planner.plan(ctx, 'sr_to_hlr')

# L3
orch = Orchestrator(project_id='sr1', dal_level='D')
objs = planner._get_objectives('sr_to_hlr')
for task in plan.tasks:
    info = orch.dispatch(task, plan, objs)
    # → delegate_task(goal=info['delegate_goal'])

# Collect → Assess
result = orch.collect(da_name, task_id)
assessment = planner.assess(task_item, result, 'sr_to_hlr')
# assessment['action']: continue | replan | human_gate

# Human gate
if assessment['action'] == 'human_gate':
    # Present unresolved items to user → get decision
    orch.log_human_decision(task_id, decision, reviewer)
    # If revise → replan → re-dispatch
    plan = planner.replan(ctx, plan, assessment)

# L5
orch.archive('sr_to_hlr')
```

## Flow

```
L1 perceive → L2 plan → L3 dispatch(topological order)
  → delegate_task(DA) → L1 collect → planner.assess()
  ├─ continue → next DA
  ├─ replan   → L2 replan → re-dispatch
  └─ human_gate → ask user → record → replan/continue
L5 archive
```

## Rules
- You orchestrate, DAs execute
- Each DA result must be assessed before proceeding
- Unresolved items → human gate (ask user, don't invent assumptions)
- DAL D: no mandatory gates; gates only when ambiguities cannot be auto-resolved
- Evidence logged at every step
