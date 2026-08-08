"""
L5 制品基线管理 — 制品状态演化: 草稿→审查中→冻结→基线化
"""

import json
from pathlib import Path
from datetime import datetime


class BaselineManager:
    """制品基线管理"""

    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)
        self.pla_dir = self.project_dir / ".pla"
        self.pla_dir.mkdir(parents=True, exist_ok=True)
        self.baseline_file = self.pla_dir / ".baseline.json"
        self._baselines = self._load()

    def _load(self) -> dict:
        if self.baseline_file.exists():
            with open(self.baseline_file) as f:
                return json.load(f)
        return {"artifacts": {}, "history": []}

    def _save(self):
        with open(self.baseline_file, "w") as f:
            json.dump(self._baselines, f, ensure_ascii=False, indent=2)

    def artifact_state(self, artifact_path: str) -> str:
        """查询制品当前状态: draft | frozen | baselined | not_found"""
        return self._baselines["artifacts"].get(artifact_path, {}).get("state", "not_found")

    def freeze(self, artifact_path: str, dal_level: str, reviewer: str = "PLA") -> dict:
        """
        冻结制品。冻结后才能进入下一研发阶段。

        返回: {frozen: bool, version: str, message: str}
        """
        now = datetime.now().isoformat()
        current = self._baselines["artifacts"].get(artifact_path, {"version": 0})

        new_version = current.get("version", 0) + 1
        self._baselines["artifacts"][artifact_path] = {
            "state": "frozen",
            "version": new_version,
            "frozen_at": now,
            "frozen_by": reviewer,
            "dal_level": dal_level,
        }
        self._baselines["history"].append({
            "action": "freeze", "artifact": artifact_path,
            "version": new_version, "at": now, "by": reviewer,
        })
        self._save()
        return {"frozen": True, "version": f"v{new_version}", "message": f"{artifact_path} 冻结为 v{new_version}"}

    def baseline(self, artifact_path: str, reviewer: str = "PLA") -> dict:
        """
        将冻结制品提升为基线。基线化后才能作为后续活动的正式输入。

        只有 frozen 状态的制品才能 baseline。
        """
        current = self._baselines["artifacts"].get(artifact_path)
        if not current or current.get("state") != "frozen":
            return {"baselined": False, "message": f"{artifact_path} 未冻结,不能基线化"}

        now = datetime.now().isoformat()
        self._baselines["artifacts"][artifact_path]["state"] = "baselined"
        self._baselines["artifacts"][artifact_path]["baselined_at"] = now
        self._baselines["artifacts"][artifact_path]["baselined_by"] = reviewer
        self._baselines["history"].append({
            "action": "baseline", "artifact": artifact_path,
            "version": current["version"], "at": now, "by": reviewer,
        })
        self._save()
        return {"baselined": True, "version": f"v{current['version']}", "message": f"{artifact_path} 基线化为 v{current['version']}"}

    def is_baselined(self, artifact_path: str) -> bool:
        return self.artifact_state(artifact_path) == "baselined"

    def get_frozen(self) -> list:
        return [k for k, v in self._baselines["artifacts"].items() if v.get("state") == "frozen"]

    def get_baselined(self) -> list:
        return [k for k, v in self._baselines["artifacts"].items() if v.get("state") == "baselined"]
