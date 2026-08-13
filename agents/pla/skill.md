# PLA Skill — Process Lifecycle Agent

Load `agents/pla/AGENT.md` for your full role (5-layer closed-loop controller).

## Architecture

```
agents/pla/
  perception.py  → L1: 读SR+约束→ActivityContext
  planner.py     → L2: plan() + replan() + assess()
runtime/
  orchestrator.py → L3: dispatch(写队列+spawn_cmd)
                    L1: collect_after_spawn(进程状态+inbox综合判断)
                    L5: archive
  channel.py      → 文件消息通道
  protocol.py     → TaskContext / ExecutionResult
```

## Your Tools

PLA 需要同时使用 Python 模块 (orchestrator) 和 Hermes Agent 工具 (terminal/process):

### Python modules
```python
from agents.pla.perception import Perception
from agents.pla.planner import Planner
from runtime import Orchestrator
```

### Agent tools (Hermes built-in)
- `terminal(command, background=True, notify_on_complete=True)` — spawn DA 进程
- `process(action='wait', session_id, timeout)` — 阻塞等待进程退出
- `process(action='log', session_id)` — 获取进程输出/日志

### 派发-监控-收集 完整循环 (推荐流程)

```
for task in plan.tasks:
    # Step 1: 写 TaskContext 到队列, 生成 spawn 命令
    info = orch.dispatch(task, plan, objs)
    # L1 tracker 已记录: state=PENDING→DISPATCHED

    # Step 2: spawn DA 进程 (带完成通知回调)
    spawn = terminal(command=info['spawn_command'],
                     background=True,
                     notify_on_complete=True,
                     timeout=600)
    orch.tracker.mark_running(info['task_id'])  # L1: DISPATCHED→RUNNING

    # Step 3: 阻塞等待进程退出 (监控进程状态, 不是轮询文件!)
    proc = process(action='wait',
                   session_id=spawn['session_id'],
                   timeout=600)

    # Step 4: 综合判断进程状态 + inbox 结果
    # orch.collect_after_spawn() 内部更新 tracker: RUNNING→COMPLETED/CRASHED/FAILED
    result, error = orch.collect_after_spawn(
        info['da_name'], info['task_id'],
        exit_code=proc['exit_code'],
        log_snippet=proc.get('output', ''))

    if error:
        # 进程崩溃 or 正常退出但未写 inbox
        if proc['exit_code'] != 0:
            full_log = process(action='log', session_id=spawn['session_id'])
        assessment = {'status': 'failed', 'issues': [error],
                      'unresolved': [], 'action': 'replan'}
    else:
        # Step 5: L4 评估
        assessment = planner.assess(task, result, 'sr_to_hlr')

    # L1 感知摘要: 偏差信号 → L4 校正
    deviation_signals = orch.tracker.get_deviation_signals()
    if deviation_signals:
        # 将偏差信号传给 L4 校正层
        pass

# L1 感知: 查看所有 DA 运行状态
summary = orch.tracker.get_summary()
# {"total": N, "by_state": {"completed": N, "crashed": 0, ...},
#  "deviation_signals": [...]}
```

# Human gate
if assessment['action'] == 'human_gate':
    orch.log_human_decision(task_id, decision, reviewer)
    plan = planner.replan(ctx, plan, assessment)

# L5
orch.archive('sr_to_hlr')
```

### 备用: 文件轮询 (fallback)

当进程管理不可用时, 用 `wait_for_da()` 轮询 inbox 文件:

```python
info = orch.dispatch(task, plan, objs)
terminal(command=info['spawn_command'], background=True, timeout=600)
result = orch.wait_for_da(info['da_name'], info['task_id'], timeout=600)
```

## Flow

```
L1 perceive (制品扫描 + DA状态追踪)
  → L2 plan (路径选择 + TaskPlan生成)
  → L3 dispatch (写队列 + tracker.track_dispatch)
  → terminal(spawn, background, notify_on_complete)
  → tracker.mark_running                        # L1: DISPATCHED→RUNNING
  → process(wait)                                # 阻塞等进程退出
  → orch.collect_after_spawn(exit_code, log)     # L1: RUNNING→COMPLETED/CRASHED/FAILED
  → tracker.get_deviation_signals() → L4         # 偏差信号→校正层
  → planner.assess()                             # L4 评估
  ├─ continue → next DA
  ├─ replan   → L2 replan → re-dispatch
  └─ human_gate → ask user → record → replan/continue
L5 archive (含 tracker 状态快照)
```

### 监控能力对比

| | 文件轮询 (wait_for_da) | 进程监控 (推荐) |
|---|---|---|
| 感知手段 | 轮询 inbox 文件 | process(action='wait') 阻塞进程 |
| 崩溃检测 | ❌ 只能靠超时 | ✅ exit_code ≠ 0 |
| 内部错误检测 | ❌ 无法区分 | ✅ 进程正常退出但无 inbox |
| 日志获取 | ❌ 无法获取 | ✅ process(action='log') |
| 回调通知 | ❌ | ✅ notify_on_complete=True |

## Rules
- You orchestrate, DAs execute
- Each DA result must be assessed before proceeding
- Unresolved items → human gate (ask user, don't invent assumptions)
- DAL D: no mandatory gates; gates only when ambiguities cannot be auto-resolved
- Evidence logged at every step
