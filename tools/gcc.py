"""
GCC 编译器包装器

封装 GCC 调用，统一接口供 Code Agent 和 Test Agent 使用。
"""

import subprocess
import shutil
from typing import Optional


class GCC:
    """GCC 编译器包装器"""

    def __init__(self, compiler: str = "gcc"):
        self.compiler = shutil.which(compiler) or compiler

    def version(self) -> str:
        """获取 GCC 版本"""
        try:
            proc = subprocess.run(
                [self.compiler, "--version"],
                capture_output=True, text=True, timeout=10,
            )
            return proc.stdout.split("\n")[0] if proc.returncode == 0 else "unknown"
        except Exception:
            return "unknown"

    def compile(
        self,
        sources: list[str],
        output: str,
        flags: Optional[list[str]] = None,
        includes: Optional[list[str]] = None,
        link_flags: Optional[list[str]] = None,
    ) -> dict:
        """
        编译 C 源文件。

        Args:
            sources: 源文件路径列表
            output: 输出文件路径
            flags: 编译选项
            includes: include 路径
            link_flags: 链接选项

        Returns:
            {"exit_code": int, "stdout": str, "stderr": str, "command": str}
        """
        cmd = [self.compiler]
        if flags:
            cmd.extend(flags)
        if includes:
            for inc in includes:
                cmd.extend(["-I", inc])
        cmd.extend(sources)
        cmd.extend(["-o", output])
        if link_flags:
            cmd.extend(link_flags)

        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        return {
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "command": " ".join(cmd),
        }

    def compile_and_run(
        self,
        sources: list[str],
        flags: Optional[list[str]] = None,
        stdin: Optional[str] = None,
    ) -> dict:
        """
        编译并执行。

        Returns:
            {"compile": {...}, "run": {"exit_code": int, "stdout": str, "stderr": str}}
        """
        import tempfile, os

        with tempfile.NamedTemporaryFile(suffix=".out", delete=False) as tmp:
            binary = tmp.name

        try:
            compile_result = self.compile(sources, binary, flags)
            if compile_result["exit_code"] != 0:
                return {"compile": compile_result, "run": None}

            run_proc = subprocess.run(
                [binary],
                input=stdin,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return {
                "compile": compile_result,
                "run": {
                    "exit_code": run_proc.returncode,
                    "stdout": run_proc.stdout,
                    "stderr": run_proc.stderr,
                },
            }
        finally:
            if os.path.exists(binary):
                os.unlink(binary)
