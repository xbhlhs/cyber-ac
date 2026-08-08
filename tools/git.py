"""
Git 版本管理包装器

封装 Git 操作，供 PLA 进行版本管理和追溯。
"""

import os
import subprocess
from typing import Optional


class Git:
    """Git 版本管理包装器"""

    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path

    def is_repo(self) -> bool:
        """检查是否为 Git 仓库"""
        try:
            subprocess.run(
                ["git", "-C", self.repo_path, "rev-parse", "--git-dir"],
                capture_output=True, check=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def init(self) -> bool:
        """初始化 Git 仓库"""
        try:
            subprocess.run(
                ["git", "init", self.repo_path],
                capture_output=True, check=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def status(self) -> str:
        """获取仓库状态"""
        try:
            proc = subprocess.run(
                ["git", "-C", self.repo_path, "status", "--short"],
                capture_output=True, text=True,
            )
            return proc.stdout
        except subprocess.CalledProcessError:
            return ""

    def commit(self, message: str, files: Optional[list[str]] = None) -> dict:
        """
        提交更改。

        Returns:
            {"success": bool, "commit_hash": str, "error": str}
        """
        try:
            if files:
                subprocess.run(
                    ["git", "-C", self.repo_path, "add"] + files,
                    capture_output=True, check=True,
                )
            else:
                subprocess.run(
                    ["git", "-C", self.repo_path, "add", "-A"],
                    capture_output=True, check=True,
                )

            proc = subprocess.run(
                ["git", "-C", self.repo_path, "commit", "-m", message],
                capture_output=True, text=True,
            )
            if proc.returncode == 0:
                hash_proc = subprocess.run(
                    ["git", "-C", self.repo_path, "rev-parse", "HEAD"],
                    capture_output=True, text=True,
                )
                return {"success": True, "commit_hash": hash_proc.stdout.strip(), "error": ""}
            else:
                return {"success": False, "commit_hash": "", "error": proc.stderr}
        except Exception as e:
            return {"success": False, "commit_hash": "", "error": str(e)}

    def log(self, count: int = 10) -> str:
        """获取最近提交日志"""
        try:
            proc = subprocess.run(
                ["git", "-C", self.repo_path, "log", f"-{count}", "--oneline"],
                capture_output=True, text=True,
            )
            return proc.stdout
        except subprocess.CalledProcessError:
            return ""
