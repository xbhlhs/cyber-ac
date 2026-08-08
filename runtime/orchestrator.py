"""
PLA-DA 编排器 — 纯通信层

职责:
  - dispatch: 封装L2的TaskItem→TaskContext→写队列+生成delegate_goal
  - collect: 从队列收集DA结果 (含格式验证)
  - archive: L5证据归档

不含任何智能逻辑。PLA的L1/L2/L4智能在 agents/pla/ 中。
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from runtime.protocol import TaskContext, ExecutionResult
from runtime.channel import MessageChannel
from runtime.result_validator import ResultValidator
from runtime.task_plan import TaskPlan, TaskItem
from agents.pla.baseline import BaselineManager
from tools.registry import get_da_tools


class Orchestrator:
    """PLA-DA纯通信编排器"""

    def __init__(self, workspace: str = ".", project_id: str = None, dal_level: str = "D"):
        self.workspace = Path(workspace).resolve()
        self.project_id = project_id
        self.dal_level = dal_level
        self.project_dir = self.workspace / "projects" / project_id if project_id else self.workspace
        self.evidence_dir = self.project_dir / "evidence"
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.channel = MessageChannel(str(self.project_dir / ".pla/queue"))
        self.validator = ResultValidator()
        self._log_entries: list[dict] = []
        self.da_agents = {
            "req-analysis":"agents/da-01/AGENT.md","req-decomp":"agents/da-02/AGENT.md",
            "model-build":"agents/da-03/AGENT.md","model-check":"agents/da-04/AGENT.md",
            "code-gen":"agents/da-05/AGENT.md","code-check":"agents/da-06/AGENT.md",
            "test-scenario":"agents/da-07/AGENT.md","test-case-gen":"agents/da-08/AGENT.md",
            "test-proc-gen":"agents/da-09/AGENT.md","test-exec":"agents/da-10/AGENT.md",
            "verify-analysis":"agents/da-11/AGENT.md","trace-maint":"agents/da-12/AGENT.md",
            "review-materials":"agents/da-13/AGENT.md","airworth-evidence":"agents/da-14/AGENT.md",
        }

    # ---- L3 dispatch ----

    def dispatch(self, task_item: TaskItem, plan: TaskPlan = None, objectives: list = None) -> dict:
        """L3: 封装TaskItem→TaskContext→写队列→delegate_goal"""
        task = TaskContext(
            task_id=task_item.id,
            task_name=task_item.name,
            da_name=task_item.da_name,
            activity_type=task_item.activity_type, description=task_item.description,
            inputs=task_item.inputs, expected_outputs=task_item.expected_outputs,
            constraints={
                "dal_level": plan.dal_level if plan else "D",
                "applicable_objectives": objectives or [],
                "coding_constraints": {"language":"C","standard":"C11","compiler":"GCC","no_dynamic_memory":True},
            },
            dal_level=plan.dal_level if plan else "D",
            created_at=datetime.now().isoformat(),
            dag_version=plan.version if plan else 1,
        )
        queue_path = self.channel.send_task(task)
        goal = self._build_goal(task, objectives or [])
        self._log("L3_dispatch", task.task_id, f"→ {task.da_name} [{len(objectives or [])} obj]")
        return {"task_id":task.task_id,"queue_file":queue_path,"delegate_goal":goal,"da_name":task.da_name,"objectives_injected":len(objectives or [])}

    def _build_goal(self, task: TaskContext, objectives: list) -> str:
        tools = get_da_tools(task.da_name, str(self.project_dir / "config.yaml") if self.project_id else None, self.project_id or "sr1")
        tools_str = ",".join(tools)
        obj_section = ""
        if objectives:
            obj_section = "\n## DO-178C (DAL {})\n\n".format(task.dal_level)
            for o in objectives:
                obj_section += f"  - {o['id']}: {o['desc']}\n"
            obj_section += "\nDeclare compliance in objective_compliance array.\n"
        agent_file = self.da_agents.get(task.da_name,"")
        queue_base = f"projects/{self.project_id}/.pla/queue" if self.project_id else ".pla/queue"
        return f"""You are {task.da_name}. Load {agent_file}.

Available tools: {tools_str}

Read Task Context: {queue_base}/outbox/{task.da_name}/task_{task.task_id}.json
{obj_section}
Result → {queue_base}/inbox/{task.da_name}/result_{task.task_id}.json
Format: {{"task_id":"{task.task_id}","da_name":"{task.da_name}","status":"completed","artifacts":[...],"output":{{}},"process_data":{{"reasoning":"..."}},"unresolved":[...],"objective_compliance":[...],"error":""}}"""

    # ---- L1 collect ----

    def collect(self, da_name: str, task_id: str) -> Optional[ExecutionResult]:
        """从队列收集DA结果, 先验证格式"""
        filepath = self.project_dir / ".pla/queue/inbox" / da_name / f"result_{task_id}.json"
        validation = self.validator.validate_file(str(filepath))
        if not validation["valid"]:
            self._log("L1_format_error", task_id, f"DA {da_name} 结果格式无效: {validation['issues']}")
            return None
        result = self.channel.get_result(da_name, task_id)
        if result:
            self._log("L1_collect", task_id, f"← {da_name}: {result.status}")
        return result

    # ---- L5 archive ----

    def archive(self, activity_id: str) -> str:
        path = self.evidence_dir / f"evidence_{activity_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"activity_id":activity_id,"archived_at":datetime.now().isoformat(),"entries":self._log_entries}, f, ensure_ascii=False, indent=2)
        self._log("L5_archive", activity_id, f"证据归档: {path.name}")
        return str(path)

    # ---- log ----

    def _log(self, event: str, task_id: str, detail: str):
        self._log_entries.append({"timestamp":datetime.now().isoformat(),"event":event,"task_id":task_id,"detail":detail})

    def get_log(self) -> list: return self._log_entries

    def log_human_decision(self, task_id: str, decision: str, reviewer: str = "unknown"):
        self._log("human_decision", task_id, f"{reviewer}: {decision}")
