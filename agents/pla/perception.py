"""
PLA L1 感知层 — 研发输入感知

读取SR、项目配置、DO-178C约束，结构化后交给L2。
"""

from dataclasses import dataclass, field
from pathlib import Path
import yaml


@dataclass
class ActivityContext:
    project_id: str
    project_name: str
    dal_level: str
    input_artifacts: dict = field(default_factory=dict)
    constraints: dict = field(default_factory=dict)
    lifecycle_stage: str = "requirements"
    summary: str = ""


class Perception:
    def __init__(self, project_dir: str, dal_level: str = "D"):
        self.project_dir = Path(project_dir)
        self.dal_level = dal_level

    def perceive(self) -> ActivityContext:
        config_path = self.project_dir / "config.yaml"
        project_config = {}
        if config_path.exists():
            with open(config_path) as f:
                project_config = yaml.safe_load(f).get("project", {})

        artifacts = self._scan_artifacts()
        constraints = self._load_constraints(project_config)

        return ActivityContext(
            project_id=project_config.get("id", self.project_dir.name),
            project_name=project_config.get("name", ""),
            dal_level=self.dal_level,  # 参数优先, 不受配置文件覆盖
            input_artifacts=artifacts,
            lifecycle_stage=self._determine_stage(artifacts),
            summary=f"项目{project_config.get('name','')}: 已有制品 [{', '.join(k for k,v in artifacts.items() if v.get('exists'))}]",
        )

    def _scan_artifacts(self) -> dict:
        artifacts = {}
        for name, rel in {
            "sr":"requirements/sr.md","hlr":"requirements/hlr.md",
            "llr":"requirements/llr.md","source":"src/","tests":"tests/","evidence":"evidence/"
        }.items():
            p = self.project_dir / rel
            artifacts[name] = {"path":str(p), "exists":p.exists(), "size":p.stat().st_size if p.exists() and p.is_file() else 0}
        return artifacts

    def _load_constraints(self, project_config: dict = None) -> dict:
        constraints = {}

        # DO-178C
        cp = Path("environment/constraints/do178c.yaml")
        if cp.exists():
            with open(cp) as f:
                do178c = yaml.safe_load(f)
            constraints["dal_info"] = do178c.get("dal_levels",{}).get(self.dal_level,{})
            constraints["do178c_ref"] = str(cp)

        # 公司规范
        company_path = Path("environment/constraints/company.yaml")
        if company_path.exists():
            with open(company_path) as f:
                constraints["company"] = yaml.safe_load(f).get("company_standards", {})

        # 项目路径约束
        if project_config:
            constraints["project_path"] = project_config.get("project_path_constraints", {})

        return constraints

    def _determine_stage(self, artifacts: dict) -> str:
        if artifacts.get("sr",{}).get("exists"):
            if not artifacts.get("hlr",{}).get("exists"): return "sr_to_hlr"
            if not artifacts.get("llr",{}).get("exists"): return "hlr_to_llr"
            if artifacts.get("source",{}).get("exists"): return "implementation"
        return "requirements"
