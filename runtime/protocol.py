"""
Agent间通信协议 (Task Context / Execution Result)

定义PLA与DA之间消息传递的标准化格式。
通信方式: 文件消息传递 (file-based message passing)
  PLA → DA: queue/outbox/{da-name}/task_{task_id}.json
  DA → PLA: queue/inbox/{da-name}/result_{task_id}.json
"""

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


# ============================================================
# Task Context — PLA → DA
# ============================================================

@dataclass
class TaskContext:
    """PLA向DA下发的任务上下文"""
    task_id: str                              # 唯一任务标识 (如 sr_to_hlr-T01)
    da_name: str                              # 目标DA名称 (PLA L2决策)
    activity_type: str                        # 研发活动类型
    description: str                          # 任务描述
    task_name: str = ""                       # 任务名称 (人可读, 用于评审/证据提取)

    # 输入输出
    inputs: dict = field(default_factory=dict)           # 输入制品: {name: path}
    expected_outputs: list[str] = field(default_factory=list)  # 期望输出路径

    # 约束注入（DAL自适应）
    constraints: dict = field(default_factory=dict)
    dal_level: str = "C"
    development_path: str = "fusion"           # model_driven | llm_driven | fusion

    # 人工闸门
    human_gate_before: bool = False            # 执行前是否需要人工审批
    human_gate_after: bool = False             # 执行后是否需要人工确认
    human_gate_type: str = ""                  # initial_plan|da_path_selection|verification_confirm|change_impact|evidence_archive

    # 元信息
    created_at: str = ""
    dag_version: int = 1

    def to_json(self) -> str:
        data = asdict(self)
        return json.dumps(data, ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "TaskContext":
        data = json.loads(json_str)
        return cls(**data)


# ============================================================
# Execution Result — DA → PLA
# ============================================================

@dataclass
class ExecutionResult:
    """DA向PLA返回的统一执行结果"""
    task_id: str
    da_name: str = ""
    status: str = "completed"                              # completed | failed | blocked | waiting_human

    # 工程制品 (Artifact)
    artifacts: list[str] = field(default_factory=list)  # 实际产出的文件路径

    # 执行状态 (Status)
    exit_code: int = 0
    error: str = ""

    # 执行日志 (Log)
    log: str = ""

    # 度量指标 (Metrics)
    metrics: dict = field(default_factory=dict)
    duration_ms: float = 0

    # 审计证据 (Evidence)
    process_data: dict = field(default_factory=dict)  # 推理过程、决策依据、偏差数据

    # DO-178C合规声明
    objective_compliance: list = field(default_factory=list)

    # 未收敛项 (ambiguities, open questions — DA标记)
    unresolved: list = field(default_factory=list)

    # 输出制品内容
    output: dict = field(default_factory=dict)

    # 是否需要人工评审
    requires_human_review: bool = False
    review_materials: list[str] = field(default_factory=list)

    completed_at: str = ""

    def to_json(self) -> str:
        data = asdict(self)
        return json.dumps(data, ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "ExecutionResult":
        data = json.loads(json_str)
        return cls(**data)


# ============================================================
# Task DAG Node — L2内部使用
# ============================================================

@dataclass
class TaskNode:
    """L2决策层生成的单个任务节点"""
    id: str
    da_name: str
    description: str
    activity_type: str
    name: str = ""
    depends_on: list[str] = field(default_factory=list)
    inputs: dict = field(default_factory=dict)
    expected_outputs: list[str] = field(default_factory=list)
    constraints: dict = field(default_factory=dict)
    human_gate_before: bool = False
    human_gate_after: bool = False
    human_gate_type: str = ""

    def to_task_context(self, dal_level: str = "C", dev_path: str = "fusion") -> TaskContext:
        return TaskContext(
            task_id=self.id,
            task_name=self.name,
            da_name=self.da_name,
            activity_type=self.activity_type,
            description=self.description,
            inputs=self.inputs,
            expected_outputs=self.expected_outputs,
            constraints=self.constraints,
            dal_level=dal_level,
            development_path=dev_path,
            human_gate_before=self.human_gate_before,
            human_gate_after=self.human_gate_after,
            human_gate_type=self.human_gate_type,
            created_at=datetime.now().isoformat(),
        )
