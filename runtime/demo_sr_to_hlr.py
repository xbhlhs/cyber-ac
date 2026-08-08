#!/usr/bin/env python3
"""
SR→HLR 端到端演示

PLA Agent使用Orchestrator编排DA-01(需求分析)→DA-02(需求分解)→DA-12(追溯维护)
验证:
  1. L2 Task DAG生成
  2. L3 任务派发 (写队列 + delegate_task goal)
  3. L1 结果收集
  4. L5 证据归档

运行: python runtime/demo_sr_to_hlr.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runtime import Orchestrator, TaskContext
from pathlib import Path
import json


def main():
    print("=" * 60)
    print("PLA: SR→HLR 融合开发流程演示")
    print("=" * 60)

    orch = Orchestrator()

    # ================================================================
    # Step 1: L1 感知 - 读SR-1输入
    # ================================================================
    print("\n[L1 感知层] 读取SR-1需求...")
    sr_path = Path("sr1/requirements/sr.md")
    if not sr_path.exists():
        print(f"  ✗ SR文件不存在: {sr_path}")
        print("  提示: 请先确保 sr1/requirements/sr.md 存在")
        return
    print(f"  ✓ SR-1: {sr_path} ({sr_path.stat().st_size} bytes)")

    # ================================================================
    # Step 2: L2 决策 - 生成Task DAG
    # ================================================================
    print("\n[L2 决策层] 生成Task DAG (sr_to_hlr)...")
    tasks = orch.plan_activity("sr_to_hlr")
    print(f"  Task DAG: {len(tasks)} 个任务节点")
    for i, t in enumerate(tasks):
        deps = "无依赖" if i == 0 else f"依赖 {tasks[i-1].task_id}"
        print(f"    {t.task_id}: {t.da_name} ({deps})")

    # ================================================================
    # Step 3: L3 执行驱动 - 派发任务
    # ================================================================
    print("\n[L3 执行驱动层] 派发任务给DA Agent...")
    dispatch_info_list = []

    for i, task in enumerate(tasks):
        info = orch.dispatch(task)
        dispatch_info_list.append(info)

        goal_preview = info["delegate_goal"][:120]
        print(f"\n  [{i+1}/{len(tasks)}] {task.task_id} → {task.da_name}")
        print(f"    队列文件: {info['queue_file']}")
        print(f"    期望输出: {task.expected_outputs}")
        print(f"    delegate_goal: {goal_preview}...")
        print(f"\n  ╔══════════════════════════════════════════════════════╗")
        print(f"  ║  PLA现在调用:                                      ║")
        print(f"  ║  delegate_task(goal=info['delegate_goal'])         ║")
        print(f"  ║  DA子Agent会:                                     ║")
        print(f"  ║    1. 加载 agents/da-{task.da_name.split('-')[-1]}/AGENT.md  ║")
        print(f"  ║    2. 读队列文件执行任务                           ║")
        print(f"  ║    3. 写结果到 queue/inbox/                        ║")
        print(f"  ╚══════════════════════════════════════════════════════╝")

    # 保存dispatch信息供后续使用
    disp_file = Path("queue/dispatch_info.json")
    with open(disp_file, "w") as f:
        json.dump(dispatch_info_list, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n  派发信息已保存: {disp_file}")

    # ================================================================
    # Step 4: 显示结果收集方式
    # ================================================================
    print("\n[L1+L4] PLA收集结果的方式:")
    print("  orch.collect('req-analysis', 'sr_to_hlr-T01')")
    print("  orch.collect('req-decomp', 'sr_to_hlr-T02')")
    print("  orch.collect('trace-maint', 'sr_to_hlr-T03')")
    print("  orch.assess_result(task, result)  # L4偏差分析")

    # ================================================================
    # Step 5: L5 证据日志
    # ================================================================
    print("\n[L5 稳态维持层] 当前证据日志:")
    for entry in orch.get_evidence_log():
        print(f"  [{entry['event']}] {entry['task_id']}: {entry['detail']}")

    print("\n" + "=" * 60)
    print("PLA编排完成。等待DA Agent执行并返回结果。")
    print("=" * 60)


if __name__ == "__main__":
    main()
