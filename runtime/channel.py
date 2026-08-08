"""
Agent间消息通道 (File-based Message Channel)

PLA与14个DA Agent之间通过文件系统进行消息传递。

通道结构：
  queue/
  ├── outbox/           # PLA → DA 任务队列
  │   ├── da-01/        #   每个DA一个子目录
  │   ├── da-02/
  │   └── ...
  └── inbox/            # DA → PLA 结果队列
      ├── da-01/
      ├── da-02/
      └── ...
"""

import os
import json
import time
from pathlib import Path
from typing import Optional

from runtime.protocol import TaskContext, ExecutionResult


class MessageChannel:
    """文件消息通道"""

    def __init__(self, queue_dir: str = "queue"):
        self.queue_dir = Path(queue_dir)
        self.outbox_dir = self.queue_dir / "outbox"
        self.inbox_dir = self.queue_dir / "inbox"
        self._ensure_dirs()

    def _ensure_dirs(self):
        """确保所有DA的队列目录存在"""
        for da_id in [f"da-{i:02d}" for i in range(1, 15)]:
            (self.outbox_dir / da_id).mkdir(parents=True, exist_ok=True)
            (self.inbox_dir / da_id).mkdir(parents=True, exist_ok=True)

    # ---- PLA → DA: 发送任务 ----

    def send_task(self, task: TaskContext) -> str:
        """
        PLA向DA发送任务。

        将TaskContext写入 queue/outbox/{da_name}/task_{task_id}.json
        返回文件路径。
        """
        da_dir = self.outbox_dir / task.da_name
        da_dir.mkdir(parents=True, exist_ok=True)
        filepath = da_dir / f"task_{task.task_id}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(task.to_json())
        return str(filepath)

    def get_pending_tasks(self, da_name: str) -> list[str]:
        """获取DA的待处理任务ID列表"""
        da_dir = self.outbox_dir / da_name
        if not da_dir.exists():
            return []
        tasks = sorted(da_dir.glob("task_*.json"))
        return [t.stem.replace("task_", "") for t in tasks]

    # ---- DA → PLA: 接收结果 ----

    def send_result(self, result: ExecutionResult) -> str:
        """
        DA向PLA返回执行结果。

        写入 queue/inbox/{da_name}/result_{task_id}.json
        """
        da_dir = self.inbox_dir / result.da_name
        da_dir.mkdir(parents=True, exist_ok=True)
        filepath = da_dir / f"result_{result.task_id}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(result.to_json())
        return str(filepath)

    def get_result(self, da_name: str, task_id: str) -> Optional[ExecutionResult]:
        """PLA读取DA的执行结果"""
        filepath = self.inbox_dir / da_name / f"result_{task_id}.json"
        if not filepath.exists():
            return None
        with open(filepath, "r", encoding="utf-8") as f:
            return ExecutionResult.from_json(f.read())

    def wait_for_result(self, da_name: str, task_id: str, timeout: float = 60) -> Optional[ExecutionResult]:
        """阻塞等待DA返回结果"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            result = self.get_result(da_name, task_id)
            if result:
                return result
            time.sleep(0.5)
        return None

    def get_all_results(self, da_name: str) -> dict[str, ExecutionResult]:
        """获取某个DA的所有已完成结果"""
        da_dir = self.inbox_dir / da_name
        if not da_dir.exists():
            return {}
        results = {}
        for f in sorted(da_dir.glob("result_*.json")):
            task_id = f.stem.replace("result_", "")
            with open(f, "r", encoding="utf-8") as fp:
                results[task_id] = ExecutionResult.from_json(fp.read())
        return results

    # ---- 清理 ----

    def clear_task(self, da_name: str, task_id: str):
        """清理已完成的任务文件"""
        out = self.outbox_dir / da_name / f"task_{task_id}.json"
        if out.exists():
            out.unlink()

    def clear_all(self):
        """清空所有队列"""
        import shutil
        if self.outbox_dir.exists():
            shutil.rmtree(self.outbox_dir)
        if self.inbox_dir.exists():
            shutil.rmtree(self.inbox_dir)
        self._ensure_dirs()
