#!/usr/bin/env python3
"""
PLA Runner — 驱动PLA完成一次研发活动

用法:
  python scripts/run_pla.py sr_to_hlr --project sr1 --dal D
"""

import sys
import json
from pathlib import Path

# add workspace to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.pla.perception import Perception
from agents.pla.planner import Planner
from runtime import Orchestrator


def run(project_id: str, activity_type: str, dal_level: str = "D"):
    project_dir = f"projects/{project_id}"

    # L1
    p = Perception(project_dir, dal_level)
    ctx = p.perceive()
    print(f"L1: {ctx.project_name} | DAL {ctx.dal_level} | stage={ctx.lifecycle_stage}")

    # L2
    planner = Planner(dal_level)
    plan = planner.plan(ctx, activity_type)
    print(f"L2: {len(plan.tasks)} tasks, {len(plan.checklist)} checks, {len(plan.human_gates)} gates")
    for t in plan.tasks:
        deps = f" ← {t.depends_on[0]}" if t.depends_on else ""
        print(f"  {t.id}: {t.da_name}{deps}")

    # L3 dispatch
    orch = Orchestrator(project_id=project_id, dal_level=dal_level)
    objs = planner._get_objectives(activity_type)

    dispatch_infos = []
    for task in plan.tasks:
        info = orch.dispatch(task, plan, objs)
        dispatch_infos.append(info)
        print(f"L3: {task.id} → {task.da_name} [{info['objectives_injected']} obj]")

    # Save dispatch info for PLA session
    with open("queue/dispatch.json", "w") as f:
        json.dump([{
            "task_id": d["task_id"], "da_name": d["da_name"],
            "depends_on": plan.tasks[i].depends_on,
            "delegate_goal": d["delegate_goal"],
        } for i, d in enumerate(dispatch_infos)], f, ensure_ascii=False, indent=2)

    print(f"\nDispatched {len(dispatch_infos)} tasks. Dispatch info: queue/dispatch.json")
    print("PLA session: load skills/pla.md and use delegate_task for each task in order.")
    print("After each DA completes: orch.collect() → planner.assess() → continue/replan/human_gate")

    return plan, orch, planner


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("activity", help="Activity type (e.g. sr_to_hlr)")
    ap.add_argument("--project", default="sr1")
    ap.add_argument("--dal", default="D")
    args = ap.parse_args()
    run(args.project, args.activity, args.dal)
