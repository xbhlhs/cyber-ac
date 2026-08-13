"""
PLA L1 感知层 — DA 运行时状态追踪

持续收集DA执行状态 (论文 §2.2 三股信息流):
  - Evidence Flow ↑: DA→L1→L2+L5  (执行产物、过程数据、日志)
  - Deviation Flow ↔: DA→L1→L4→L2 (异常信号、校正请求)

追踪每个DA的完整生命周期:
  PENDING → DISPATCHED → RUNNING → COMPLETED | FAILED | CRASHED | TIMEOUT
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class DAState(Enum):
    PENDING = "pending"          # 尚未派发
    DISPATCHED = "dispatched"    # 已写入队列, 进程已 spawn
    RUNNING = "running"          # 进程运行中
    COMPLETED = "completed"      # 正常完成 (exit_code=0, inbox 存在)
    FAILED = "failed"            # 进程正常退出但未产出 inbox (DA内部错误)
    CRASHED = "crashed"          # 进程异常退出 (exit_code≠0)
    TIMEOUT = "timeout"          # 进程超时未完成


@dataclass
class DARuntimeRecord:
    """单个DA的运行态记录"""
    da_name: str
    task_id: str
    state: DAState = DAState.PENDING
    session_id: str = ""                     # terminal spawn 返回的 session_id
    spawn_command: str = ""                  # 派发命令 (诊断用)
    provider: str = ""
    model: str = ""
    exit_code: int = -1
    log_snippet: str = ""                    # 崩溃时的日志片段
    error_message: str = ""                  # 错误描述

    # 时间戳
    dispatched_at: str = ""
    started_at: str = ""
    completed_at: str = ""

    # 制品
    expected_outputs: list = field(default_factory=list)
    actual_artifacts: list = field(default_factory=list)

    def is_terminal(self) -> bool:
        return self.state in (DAState.COMPLETED, DAState.FAILED,
                              DAState.CRASHED, DAState.TIMEOUT)

    def is_ok(self) -> bool:
        return self.state == DAState.COMPLETED

    def deviation_signal(self) -> Optional[str]:
        """生成 L4 校正层可消费的偏差信号"""
        if self.state == DAState.CRASHED:
            return f"DA {self.da_name} 进程崩溃 (exit_code={self.exit_code})"
        if self.state == DAState.FAILED:
            return f"DA {self.da_name} 进程正常退出但未产出结果文件"
        if self.state == DAState.TIMEOUT:
            return f"DA {self.da_name} 超时未完成"
        return None


class DARuntimeTracker:
    """DA 运行时状态追踪器 — L1 感知层的核心组件

    持续追踪每个DA从派发到完成的全生命周期状态,
    为 L4 校正层提供结构化的偏差信号。
    """

    def __init__(self):
        self._records: dict[str, DARuntimeRecord] = {}  # key = task_id

    # ---- 状态转换 ----

    def track_dispatch(self, da_name: str, task_id: str, session_id: str,
                       spawn_command: str = "", provider: str = "", model: str = "",
                       expected_outputs: list = None) -> DARuntimeRecord:
        """记录 DA 派发"""
        rec = DARuntimeRecord(
            da_name=da_name, task_id=task_id,
            state=DAState.DISPATCHED, session_id=session_id,
            spawn_command=spawn_command, provider=provider, model=model,
            expected_outputs=expected_outputs or [],
            dispatched_at=datetime.now().isoformat(),
        )
        self._records[task_id] = rec
        return rec

    def mark_running(self, task_id: str):
        """标记 DA 开始运行"""
        rec = self._get(task_id)
        if rec:
            rec.state = DAState.RUNNING
            rec.started_at = datetime.now().isoformat()

    def track_completion(self, task_id: str, exit_code: int,
                         log_snippet: str = "", artifacts: list = None,
                         error_message: str = "") -> DARuntimeRecord:
        """记录 DA 完成 (综合进程状态 + inbox 判断)"""
        rec = self._get(task_id)
        if not rec:
            return None
        rec.exit_code = exit_code
        rec.log_snippet = log_snippet
        rec.actual_artifacts = artifacts or []
        rec.error_message = error_message
        rec.completed_at = datetime.now().isoformat()

        if exit_code != 0:
            rec.state = DAState.CRASHED
        elif error_message:
            rec.state = DAState.FAILED
        else:
            rec.state = DAState.COMPLETED
        return rec

    def mark_timeout(self, task_id: str):
        """标记 DA 超时"""
        rec = self._get(task_id)
        if rec:
            rec.state = DAState.TIMEOUT
            rec.completed_at = datetime.now().isoformat()
            rec.error_message = "DA 超时未完成"

    # ---- 查询 ----

    def get_state(self, task_id: str) -> Optional[DAState]:
        rec = self._records.get(task_id)
        return rec.state if rec else None

    def get_record(self, task_id: str) -> Optional[DARuntimeRecord]:
        return self._records.get(task_id)

    def get_active_das(self) -> list[DARuntimeRecord]:
        """当前运行中或已派发但未完成的 DA"""
        return [r for r in self._records.values()
                if r.state in (DAState.DISPATCHED, DAState.RUNNING)]

    def get_completed_das(self) -> list[DARuntimeRecord]:
        return [r for r in self._records.values() if r.state == DAState.COMPLETED]

    def get_failed_das(self) -> list[DARuntimeRecord]:
        return [r for r in self._records.values()
                if r.state in (DAState.FAILED, DAState.CRASHED, DAState.TIMEOUT)]

    def get_deviation_signals(self) -> list[str]:
        """收集所有偏差信号 → 传给 L4 校正层"""
        signals = []
        for r in self._records.values():
            sig = r.deviation_signal()
            if sig:
                signals.append(sig)
        return signals

    def get_summary(self) -> dict:
        """L1 感知摘要"""
        all_recs = list(self._records.values())
        states = {}
        for r in all_recs:
            states[r.state.value] = states.get(r.state.value, 0) + 1
        return {
            "total": len(all_recs),
            "by_state": states,
            "active": len(self.get_active_das()),
            "completed": len(self.get_completed_das()),
            "failed": len(self.get_failed_das()),
            "deviation_signals": self.get_deviation_signals(),
        }

    # ----

    def _get(self, task_id: str) -> Optional[DARuntimeRecord]:
        return self._records.get(task_id)
