"""
DA结果格式验证器 (L1评估的一部分)

验证DA返回的ExecutionResult是否满足统一输出表示的格式要求。
不验证内容正确性——那属于DO-178C合规检查的范畴。
"""

import json
from pathlib import Path
from typing import Optional

# 必须字段及其类型
REQUIRED_FIELDS = {
    "task_id": str,
    "status": str,
    "artifacts": list,
}

# 可选但期望的字段
EXPECTED_FIELDS = {
    "objective_compliance": list,
    "process_data": dict,
    "output": dict,
    "duration_ms": (int, float),
    "error": str,
}

# 有效的status值
VALID_STATUSES = {"completed", "failed", "blocked", "waiting_human"}


class ResultValidator:
    """DA结果格式验证器"""

    def validate_file(self, filepath: str) -> dict:
        """
        验证DA写入的结果JSON文件。

        返回:
          {valid: bool, issues: [str], data: dict|None}
        """
        path = Path(filepath)
        issues = []

        # 1. 文件存在
        if not path.exists():
            return {"valid": False, "issues": ["结果文件不存在"], "data": None}

        # 2. JSON语法正确
        try:
            with open(path) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return {"valid": False, "issues": [f"JSON语法错误: {e}"], "data": None}

        # 3. 必须字段
        for field, expected_type in REQUIRED_FIELDS.items():
            if field not in data:
                issues.append(f"缺少必须字段: {field}")
            elif not isinstance(data[field], expected_type):
                issues.append(f"字段类型错误: {field} (期望{expected_type.__name__}, 实际{type(data[field]).__name__})")

        # 4. status值有效性
        if "status" in data and data["status"] not in VALID_STATUSES:
            issues.append(f"无效status值: {data['status']} (允许: {VALID_STATUSES})")

        # 5. artifacts格式
        if "artifacts" in data:
            for i, artifact in enumerate(data["artifacts"]):
                if not isinstance(artifact, str):
                    issues.append(f"artifacts[{i}]应为字符串路径")
                    break

        # 6. objective_compliance格式 (如果有)
        if "objective_compliance" in data and isinstance(data["objective_compliance"], list):
            for i, obj in enumerate(data["objective_compliance"]):
                if not isinstance(obj, dict):
                    issues.append(f"objective_compliance[{i}]应为对象")
                elif "objective_id" not in obj:
                    issues.append(f"objective_compliance[{i}]缺少objective_id")
                elif "status" not in obj:
                    issues.append(f"objective_compliance[{i}]缺少status")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "data": data if len(issues) == 0 else None,
        }

    def validate_result(self, result: any) -> dict:
        """
        验证已解析的ExecutionResult对象。

        返回: {valid: bool, issues: [str]}
        """
        issues = []

        if not hasattr(result, 'task_id') or not result.task_id:
            issues.append("缺少task_id")
        if not hasattr(result, 'status') or result.status not in VALID_STATUSES:
            issues.append(f"无效status: {getattr(result, 'status', None)}")

        return {"valid": len(issues) == 0, "issues": issues}
