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
from agents.pla.da_tracker import DARuntimeTracker
from tools.registry import get_da_tools, get_da_model


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
        self.tracker = DARuntimeTracker()  # L1 运行时状态追踪
        self.da_agents = {
            "req-analysis":"agents/da-01/AGENT.md","req-decomp":"agents/da-02/AGENT.md",
            "model-build":"agents/da-03/AGENT.md","model-check":"agents/da-04/AGENT.md",
            "code-gen":"agents/da-05/AGENT.md","code-check":"agents/da-06/AGENT.md",
            "test-scenario":"agents/da-07/AGENT.md","test-case-gen":"agents/da-08/AGENT.md",
            "test-proc-gen":"agents/da-09/AGENT.md","test-exec":"agents/da-10/AGENT.md",
            "verify-analysis":"agents/da-11/AGENT.md","trace-maint":"agents/da-12/AGENT.md",
            "review-materials":"agents/da-13/AGENT.md","airworth-evidence":"agents/da-14/AGENT.md",
            "da-15":"agents/da-15/AGENT.md","da-16":"agents/da-16/AGENT.md",
        }

    # ---- L3 dispatch ----

    def dispatch(self, task_item: TaskItem, plan: TaskPlan = None, objectives: list = None) -> dict:
        """L3: 封装TaskItem→TaskContext→写队列→生成spawn_command

        返回 dict:
          - task_id, queue_file, da_name, objectives_injected
          - spawn_command: 完整的 hermes chat 命令 (terminal spawn 用)
          - needs_llm: True=需要LLM Agent, False=纯工具执行
        """
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
        spawn_info = self._get_spawn_command(task.da_name, task.task_id, goal)

        # L1 追踪: 记录 DA 运行时状态
        model_cfg = get_da_model(task.da_name, self.project_id or "sr1") or {}
        self.tracker.track_dispatch(
            da_name=task.da_name, task_id=task.task_id,
            session_id="",  # PLA在agent层调用terminal()后通过 set_session_id() 回填
            spawn_command=spawn_info.get("command", ""),
            provider=model_cfg.get("provider", ""),
            model=model_cfg.get("model", ""),
            expected_outputs=list(task.expected_outputs),
        )

        self._log("L3_dispatch", task.task_id, f"→ {task.da_name} [{len(objectives or [])} obj] {spawn_info.get('label','')}")
        return {
            "task_id": task.task_id,
            "queue_file": queue_path,
            "da_name": task.da_name,
            "objectives_injected": len(objectives or []),
            "spawn_command": spawn_info.get("command"),
            "needs_llm": spawn_info.get("needs_llm", True),
            "spawn_label": spawn_info.get("label", ""),
        }

    def _get_spawn_command(self, da_name: str, task_id: str, goal: str) -> dict:
        """为DA生成 hermes terminal spawn 命令。

        从项目配置读取 da_models，生成带 --provider/--model 的 hermes chat 管道命令。
        goal 文本通过管道传入 stdin，避免 shell 引号崩溃 (B003)。
        DAs that don't need LLM (model config = null) return needs_llm=False.
        """
        model_cfg = get_da_model(da_name, self.project_id or "sr1")

        if model_cfg is None:
            return {
                "command": None,
                "needs_llm": False,
                "label": "[no-LLM]",
            }

        provider = model_cfg["provider"]
        model = model_cfg["model"]
        ctx_len = model_cfg.get("context_length")

        # 将 goal 写入临时文件, 通过管道传入 hermes — 避免 shell 引号问题
        goal_file = f"/tmp/da_goal_{task_id}.txt"
        with open(goal_file, "w", encoding="utf-8") as f:
            f.write(goal)

        agent_dir = f"projects/{self.project_id}/.pla/agents/{da_name}"
        cmd = f"cd {agent_dir} && hermes chat -q \\\"$(cat {goal_file})\\\" --provider {provider} --model {model} -s fusion-development"

        label = f"[{provider}/{model}]"
        if ctx_len:
            label += f" (context_length={ctx_len} 需在Hermes config中配置)"

        return {
            "command": cmd,
            "needs_llm": True,
            "label": label,
        }

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

    # ---- L1 collect + wait ----

    def collect(self, da_name: str, task_id: str) -> Optional[ExecutionResult]:
        """从队列收集DA结果, 先验证格式 (非阻塞 — 文件必须已存在)"""
        filepath = self.project_dir / ".pla/queue/inbox" / da_name / f"result_{task_id}.json"
        validation = self.validator.validate_file(str(filepath))
        if not validation["valid"]:
            self._log("L1_format_error", task_id, f"DA {da_name} 结果格式无效: {validation['issues']}")
            return None
        result = self.channel.get_result(da_name, task_id)
        if result:
            self._log("L1_collect", task_id, f"← {da_name}: {result.status}")
        return result

    def wait_for_da(self, da_name: str, task_id: str, timeout: float = 600) -> Optional[ExecutionResult]:
        """阻塞等待DA完成并返回结果 (terminal spawn 后的收集入口)。

        与 collect() 的区别: collect() 假设结果文件已存在;
        wait_for_da() 会轮询 inbox 队列, 等待 DA 写入结果文件。

        timeout 秒后仍未收到结果返回 None, 记录超时日志。
        """
        self._log("L1_wait", task_id, f"等待 {da_name} 完成 (超时: {timeout}s)...")
        result = self.channel.wait_for_result(da_name, task_id, timeout)
        if result:
            self._log("L1_collect", task_id, f"← {da_name}: {result.status}")
        else:
            self._log("L1_timeout", task_id, f"← {da_name}: 超时 ({timeout}s)")
        return result

    def collect_after_spawn(self, da_name: str, task_id: str, exit_code: int,
                            log_snippet: str = "") -> tuple[Optional[ExecutionResult], Optional[str]]:
        """进程级收集: 在 process(action='wait') 之后调用。

        综合判断进程状态 + inbox 结果:
          - exit_code != 0 → 进程崩溃, 记录日志片段
          - exit_code == 0 但无 inbox → DA 内部错误
          - exit_code == 0 且有 inbox → 正常收集

        返回: (result, error_message)
          - result 非 None 且 error 为 None → 正常
          - result 为 None 且 error 非 None → 失败
        """
        if exit_code != 0:
            snippet = log_snippet[:300] if log_snippet else "(无日志)"
            self._log("L1_crash", task_id,
                      f"DA {da_name} 进程异常退出 (exit_code={exit_code}): {snippet}")
            self.tracker.track_completion(task_id, exit_code, log_snippet,
                                          error_message=f"进程异常退出 (exit_code={exit_code})")
            return None, f"进程异常退出 (exit_code={exit_code})"

        result = self.collect(da_name, task_id)
        if result is None:
            self._log("L1_no_inbox", task_id,
                      f"DA {da_name} 进程正常退出但未写入 inbox 结果文件")
            self.tracker.track_completion(task_id, exit_code, log_snippet,
                                          error_message="DA 进程正常退出但未产出结果文件")
            return None, "DA 进程正常退出但未产出结果文件"

        # L1 追踪: 记录成功完成
        self.tracker.track_completion(task_id, exit_code, log_snippet,
                                      artifacts=getattr(result, 'artifacts', []) or [])
        return result, None

    # ---- L5 archive ----

    def archive(self, activity_id: str, version_label: str = "") -> str:
        """L5 证据归档 — 每次归档保留独立版本，不覆盖历史记录。"""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = f"_{version_label}" if version_label else ""
        filename = f"evidence_{activity_id}_{ts}{suffix}.json"
        path = self.evidence_dir / filename
        record = {
            "activity_id": activity_id,
            "version": version_label or ts,
            "archived_at": datetime.now().isoformat(),
            "entries": self._log_entries,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        self._update_archive_index(activity_id, filename, record)
        self._log("L5_archive", activity_id, f"证据归档: {filename}")
        return str(path)

    def _update_archive_index(self, activity_id: str, filename: str, record: dict):
        """维护归档索引 — 追加不覆盖"""
        index_path = self.evidence_dir / f"evidence_{activity_id}_index.json"
        if index_path.exists():
            with open(index_path, "r", encoding="utf-8") as f:
                index = json.load(f)
        else:
            index = {"activity_id": activity_id, "versions": []}
        index["versions"].append({
            "file": filename,
            "archived_at": record["archived_at"],
            "version": record["version"],
            "entry_count": len(record["entries"]),
        })
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

    # ---- log ----

    def _log(self, event: str, task_id: str, detail: str):
        self._log_entries.append({"timestamp":datetime.now().isoformat(),"event":event,"task_id":task_id,"detail":detail})

    def get_log(self) -> list: return self._log_entries

    def log_human_decision(self, task_id: str, decision: str, reviewer: str = "unknown"):
        self._log("human_decision", task_id, f"{reviewer}: {decision}")
