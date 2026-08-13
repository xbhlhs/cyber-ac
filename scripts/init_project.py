#!/usr/bin/env python3
"""
项目初始化脚本 — 从 examples/ 模板创建项目, 按 DAL 裁切约束文件。

用法: python3 scripts/init_project.py <project_id> <dal_level> [--model-policy required|optional|text_only]

裁切规则:
  - do178c.yaml: 只保留 applicable_DAL 包含目标 DAL 的目标
  - company.yaml: 全量保留 (公司规范不分 DAL)
  - do331.yaml: 全量保留 (trigger_condition 由代码判断)
  - config.yaml: 从模板复制, 设置 da_models
"""

import sys
import shutil
import yaml
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent


def init_project(project_id: str, dal_level: str):
    proj_dir = WORKSPACE / "projects" / project_id
    env_dir = proj_dir / ".pla" / "environment"
    constraints_dir = env_dir / "constraints"

    # 1. 创建目录
    for d in [
        proj_dir / "requirements",
        proj_dir / "src",
        proj_dir / "models",
        proj_dir / "tests",
        proj_dir / "evidence",
        env_dir,
        constraints_dir,
    ]:
        d.mkdir(parents=True, exist_ok=True)

    # DA 队列目录
    da_names = [
        "req-analysis", "req-decomp", "model-build", "model-check",
        "code-gen", "code-check", "test-scenario", "test-case-gen",
        "test-proc-gen", "test-exec", "verify-analysis", "trace-maint",
        "review-materials", "airworth-evidence",
    ]
    for da in da_names:
        (proj_dir / ".pla/queue/outbox" / da).mkdir(parents=True, exist_ok=True)
        (proj_dir / ".pla/queue/inbox" / da).mkdir(parents=True, exist_ok=True)

    # 2. 复制并裁切约束文件
    # do178c.yaml — DAL 裁切
    do178c = _load_yaml(WORKSPACE / "examples/environment/constraints/do178c.yaml")
    do178c = _filter_do178c(do178c, dal_level)
    _save_yaml(constraints_dir / "do178c.yaml", do178c)

    # company.yaml — 全量保留
    shutil.copy(
        WORKSPACE / "examples/environment/constraints/company.yaml",
        constraints_dir / "company.yaml",
    )

    # do331.yaml — 全量保留
    shutil.copy(
        WORKSPACE / "examples/environment/constraints/do331.yaml",
        constraints_dir / "do331.yaml",
    )

    # 3. 复制环境配置 (保留 da_models)
    shutil.copy(
        WORKSPACE / "examples/environment/config.yaml",
        env_dir / "config.yaml",
    )

    # 4. 项目配置模板
    if not (proj_dir / "config.yaml").exists():
        shutil.copy(
            WORKSPACE / "examples/projects/config.yaml",
            proj_dir / "config.yaml",
        )

    print(f"项目 {project_id} 初始化完成 (DAL {dal_level})")
    print(f"  约束文件已按 DAL {dal_level} 裁切 → {constraints_dir}/")
    print(f"  请编辑 {proj_dir}/config.yaml 设置项目参数")
    _print_summary(do178c, dal_level)


def _filter_do178c(data: dict, dal: str) -> dict:
    """裁切 do178c.yaml: 只保留 applicable_DAL 包含目标 DAL 的目标"""
    filtered = dict(data)  # shallow copy, keep metadata/dal_levels
    for section in ["hlr_verification", "llr_verification", "coding_verification",
                     "testing", "structural_coverage"]:
        if section in data:
            filtered[section] = [
                obj for obj in data[section]
                if dal in obj.get("applicable_DAL", [])
            ]
    return filtered


def _load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f) or {}


def _save_yaml(path: Path, data: dict):
    with open(path, "w") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def _print_summary(do178c: dict, dal: str):
    for section in ["hlr_verification", "llr_verification", "coding_verification",
                     "testing", "structural_coverage"]:
        items = do178c.get(section, [])
        ids = [item["id"] for item in items]
        print(f"  {section}: {len(items)} target(s) → {ids}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python3 scripts/init_project.py <project_id> <dal_level>")
        print("示例: python3 scripts/init_project.py sr2 B")
        sys.exit(1)
    init_project(sys.argv[1], sys.argv[2].upper())
