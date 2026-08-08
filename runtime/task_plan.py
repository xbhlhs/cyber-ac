"""
L2 决策层输出: Task Plan + Checklist

L2的职责:
  - 接收L1的ActivityContext
  - 生成Task Plan (任务列表 + 依赖关系)
  - 生成Checklist (检查项 + DO-178C目标映射 + 退出条件)
  - 识别人工闸门节点
  - 选择开发路径 (模型/LLM/融合)

L3的职责: 仅封装和派发L2的输出给DA, 不生成任务内容。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class TaskItem:
    """L2生成的单个任务"""
    id: str
    da_name: str                           # 调用的DA (PLA L2决策)
    description: str                       # 任务描述
    activity_type: str
    name: str = ""                         # 任务名称 (如 "需求分析", 用于评审/证据提取)
    depends_on: list[str] = field(default_factory=list)
    inputs: dict = field(default_factory=dict)
    expected_outputs: list[str] = field(default_factory=list)


@dataclass
class CheckItem:
    """L2生成的单个检查项"""
    id: str
    description: str
    category: str = "general"              # general|do178c|human|artifact
    do178c_ref: str = ""                   # 对应DO-178C条款 (如 "A3-1", "6.3.1.a")
    applicable_dal: list[str] = field(default_factory=list)
    check_method: str = "auto"             # auto|manual|hybrid
    exit_condition: str = ""               # 通过此检查项的条件


@dataclass
class HumanGate:
    """L2识别的人工闸门"""
    gate_type: str                         # initial_plan|da_path_selection|verification_confirm|change_impact|evidence_archive
    task_id: str                           # 关联任务
    trigger_condition: str
    authorization: str                     # 授权角色
    timing: str = "after"                  # before|after


@dataclass
class TaskPlan:
    """
    L2决策层的完整输出。

    包含:
      - tasks: 任务列表
      - checklist: 检查清单 (DO-178C目标映射)
      - human_gates: 人工闸门列表
      - constraints: DAL级别约束
      - development_path: 开发路径选择
    """
    activity_id: str
    activity_type: str
    dal_level: str = "D"

    # L2生成的任务列表
    tasks: list[TaskItem] = field(default_factory=list)

    # L2生成的检查清单
    checklist: list[CheckItem] = field(default_factory=list)

    # L2识别的人工闸门
    human_gates: list[HumanGate] = field(default_factory=list)

    # DAL级别约束
    constraints: dict = field(default_factory=dict)

    # 开发路径
    development_path: str = "fusion"

    created_at: str = ""
    version: int = 1

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """转为字典供L3派发"""
        return {
            "activity_id": self.activity_id,
            "activity_type": self.activity_type,
            "dal_level": self.dal_level,
            "development_path": self.development_path,
            "version": self.version,
            "created_at": self.created_at,
            "task_count": len(self.tasks),
            "checklist_count": len(self.checklist),
            "human_gate_count": len(self.human_gates),
            "tasks": [
                {
                    "id": t.id, "name": t.name, "da_name": t.da_name,
                    "description": t.description,
                    "depends_on": t.depends_on,
                    "inputs": t.inputs,
                    "expected_outputs": t.expected_outputs,
                }
                for t in self.tasks
            ],
            "checklist": [
                {
                    "id": c.id, "description": c.description,
                    "category": c.category, "do178c_ref": c.do178c_ref,
                    "check_method": c.check_method,
                }
                for c in self.checklist
            ],
            "human_gates": [
                {
                    "gate_type": h.gate_type, "task_id": h.task_id,
                    "trigger_condition": h.trigger_condition,
                    "authorization": h.authorization, "timing": h.timing,
                }
                for h in self.human_gates
            ],
            "constraints": self.constraints,
        }
