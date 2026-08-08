#!/usr/bin/env python3
"""
DA Runner — DA Agent读取队列任务并执行

用法:
  python scripts/run_da.py req-analysis sr_to_hlr-T01 --project sr1

DA Agent加载自己的AGENT.md，读Task Context，执行，写结果。
"""

import sys
import json
from pathlib import Path


def read_task(da_name: str, task_id: str, project_id: str = "sr1") -> dict:
    """读取PLA派发的任务"""
    task_path = Path(f"projects/{project_id}/.pla/queue/outbox/{da_name}/task_{task_id}.json")
    if not task_path.exists():
        print(f"Task not found: {task_path}")
        return None
    with open(task_path) as f:
        return json.load(f)


def write_result(da_name: str, task_id: str, project_id: str = "sr1"):
    """写入执行结果"""
    inbox = Path(f"projects/{project_id}/.pla/queue/inbox/{da_name}")
    inbox.mkdir(parents=True, exist_ok=True)
    result_path = inbox / f"result_{task_id}.json"
    with open(result_path, "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Result written: {result_path}")


def run(da_name: str, task_id: str, project_id: str = "sr1"):
    """DA Agent入口: 读任务→执行→写结果"""
    task = read_task(da_name, task_id, project_id)
    if not task:
        return

    print(f"DA {da_name} received task: {task.get('description','')}")
    print(f"Expected outputs: {task.get('expected_outputs',[])}")
    print(f"Constraints: DAL={task.get('dal_level','?')}, objectives={len(task.get('constraints',{}).get('applicable_objectives',[]))}")

    # Agent定义文件
    da_num = {
        "req-analysis":"01","req-decomp":"02","model-build":"03","model-check":"04",
        "code-gen":"05","code-check":"06","test-scenario":"07","test-case-gen":"08",
        "test-proc-gen":"09","test-exec":"10","verify-analysis":"11","trace-maint":"12",
        "review-materials":"13","airworth-evidence":"14",
    }.get(da_name, "00")

    agent_file = Path(f"agents/da-{da_num}/AGENT.md")
    if agent_file.exists():
        print(f"Agent definition: {agent_file}")

    print("\n=== DA READY ===")
    print(f"Load agent definition, read task context, execute, write result to projects/{project_id}/.pla/queue/inbox/{da_name}/result_{task_id}.json")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/run_da.py <da_name> <task_id> [--project sr1]")
        sys.exit(1)
    project = "sr1"
    if "--project" in sys.argv:
        idx = sys.argv.index("--project")
        project = sys.argv[idx+1]
    run(sys.argv[1], sys.argv[2], project)
