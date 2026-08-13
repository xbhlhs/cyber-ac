"""
工程资源工具注册表 (Tool Registry)

五类工程资源接入方式:

  CLI       — 命令行工具: GCC、PlantUML、Git、Make，以及任何提供CLI接口的桌面端工具
              （如仿真器命令行接口、调试器命令行接口等）

  API       — 服务化资源:
              · LLM推理接口 — 大语言模型调用
              · 存量系统API — 需求管理工具(REST API)、ReqIF文件导入/导出、
                docx文档解析、基线同步接口等
              · 平台API — 将制品同步到外部管理平台

  Container — 容器化资源 (Docker/Podman)，用于隔离的工具执行环境

  AI        — 智能模型服务: 本地LLM、云端LLM、多模态模型

  Human     — 人工工程资源: 专家评审、人工确认、质量审核

每个DA的AGENT.md声明"工具需求"（需要什么能力），
项目config.yaml指定"工具分配"（用什么具体工具）。
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, Optional
import yaml


class ResourceType(Enum):
    CLI = "cli"
    API = "api"
    CONTAINER = "container"
    AI = "ai"
    HUMAN = "human"


@dataclass
class ToolDef:
    """工具定义"""
    name: str
    resource_type: ResourceType
    description: str
    config: dict = field(default_factory=dict)  # 配置: command, endpoint, model, etc.
    handler: Optional[Callable] = None          # 实际调用函数


# ============================================================
# 工具注册表 — 系统可用的所有工具
# ============================================================

TOOL_REGISTRY: dict[str, ToolDef] = {
    # ---- CLI 工具 (含桌面端CLI接口的工具) ----
    "gcc": ToolDef(
        name="gcc",
        resource_type=ResourceType.CLI,
        description="GCC C compiler — compile C source files (host or cross-compiler)",
        config={"command": "gcc", "default_flags": ["-Wall", "-Wextra", "-std=c11", "-pedantic"]},
    ),
    "git": ToolDef(
        name="git",
        resource_type=ResourceType.CLI,
        description="Git — version control, commit, log, status",
        config={"command": "git"},
    ),
    "make": ToolDef(
        name="make",
        resource_type=ResourceType.CLI,
        description="GNU Make — build automation",
        config={"command": "make"},
    ),

    # ---- API 工具 ----
    # LLM推理
    "llm_api": ToolDef(
        name="llm_api",
        resource_type=ResourceType.API,
        description="LLM API — call large language model for reasoning/generation",
        config={
            "endpoint": "http://localhost:11434/v1",
            "provider": "ollama",
            "model": "deepseek-v4",
        },
    ),

    # 存量系统集成 — 需求导入
    "req_import": ToolDef(
        name="req_import",
        resource_type=ResourceType.API,
        description="Requirements Import — fetch structured requirements from external tools (ReqIF, docx, REST API)",
        config={
            "supported_formats": ["reqif", "docx", "json", "csv"],
            "source_type": "api_or_file",
        },
    ),

    # 存量系统集成 — 基线同步
    "baseline_sync": ToolDef(
        name="baseline_sync",
        resource_type=ResourceType.API,
        description="Baseline Sync — push baselined artifacts to external platform/management system",
        config={
            "push_target": "external_platform_api",
            "sync_items": ["requirements", "models", "code", "tests", "evidence"],
        },
    ),

    # ---- Human 工具 ----
    "human_review": ToolDef(
        name="human_review",
        resource_type=ResourceType.HUMAN,
        description="Human Review Gate — submit materials for human review and wait for decision",
        config={
            "roles": ["项目技术负责人", "质量保证人员", "适航联络人员", "变更控制委员会"],
            "decisions": ["approved", "rejected", "revise"],
        },
    ),
}


# ============================================================
# DA 工具分配 — 从项目配置加载
#
# 加载顺序:
#   1. 读取 environment/config.yaml 中的 da_tools.base + da_tools.da (全局默认)
#   2. 读取 projects/{project_id}/config.yaml 中的 da_tools (项目覆盖)
#   3. 合并: base(全局) + da(全局) → 项目覆盖 da 条目 → 去重
#
# 项目只需声明需要覆盖的DA，未覆盖的沿用全局默认。
# ============================================================

def _load_yaml(path: str) -> dict:
    p = Path(path)
    if p.exists():
        with open(p) as f:
            return yaml.safe_load(f) or {}
    return {}


def get_da_tools(da_name: str, project_config_path: str = None, project_id: str = "sr1") -> list[str]:
    """
    获取指定DA在当前项目中的可用工具列表。

    从 projects/{project_id}/.pla/environment/config.yaml 加载全局默认，
    如果提供了 project_config_path，则从项目配置中加载覆盖。
    """
    env_config = _load_yaml(f"projects/{project_id}/.pla/environment/config.yaml")
    da_tools_cfg = env_config.get("da_tools", {})
    base_tools = da_tools_cfg.get("base", ["read_file", "write_file", "terminal", "search_files"])
    global_da = da_tools_cfg.get("da", {})

    # 合并项目覆盖
    if project_config_path:
        proj_config = _load_yaml(project_config_path)
        proj_da = proj_config.get("da_tools", {}) or {}
        merged_da = {**global_da, **proj_da}  # 项目覆盖全局
    else:
        merged_da = global_da

    specific = merged_da.get(da_name, [])
    return list(set(base_tools + specific))


def get_da_model(da_name: str, project_id: str = "sr1") -> dict | None:
    """
    获取指定DA在当前项目中的LLM model/provider配置。

    配置位置: projects/{project_id}/.pla/environment/config.yaml → da_models 段
    解析顺序: da_models.overrides[da_name] → da_models.default

    返回:
        {"provider": "deepseek", "model": "deepseek-v4-pro"}  — DA需要LLM
        None                                                    — DA不需要LLM (如test-exec)
    """
    env_config = _load_yaml(f"projects/{project_id}/.pla/environment/config.yaml")
    da_models_cfg = env_config.get("da_models", {})
    if not da_models_cfg:
        return None

    # 检查 per-DA override
    overrides = da_models_cfg.get("overrides", {}) or {}
    if da_name in overrides:
        override = overrides[da_name]
        if override is None:
            return None  # 显式标记为不需要LLM
        if isinstance(override, dict):
            return {
                "provider": override.get("provider", ""),
                "model": override.get("model", ""),
                "context_length": override.get("context_length"),  # 可选
            }

    # 回退到默认
    default = da_models_cfg.get("default", {}) or {}
    if not default:
        return None
    return {
        "provider": default.get("provider", ""),
        "model": default.get("model", ""),
        "context_length": default.get("context_length"),  # 可选
    }


# 基础工具（所有DA都可用）
BASE_TOOLS = ["read_file", "write_file", "terminal", "search_files"]
