"""
SysML 建模工具包装器

封装 SysML 模型构建和 PlantUML 渲染调用。
"""

import os
import subprocess
from typing import Optional


class SysML:
    """SysML 建模工具包装器"""

    def __init__(self, models_dir: str = "sr1/models"):
        self.models_dir = models_dir
        os.makedirs(models_dir, exist_ok=True)

    def render_plantuml(self, puml_path: str, output_format: str = "png") -> Optional[str]:
        """
        渲染 PlantUML 文件为图像。

        Args:
            puml_path: .puml 文件路径
            output_format: 输出格式 (png/svg)

        Returns:
            输出文件路径，失败返回 None
        """
        plantuml_jar = self._find_plantuml()
        if not plantuml_jar:
            # 尝试使用 plantuml CLI
            try:
                proc = subprocess.run(
                    ["plantuml", f"-t{output_format}", puml_path],
                    capture_output=True, text=True, timeout=60,
                )
                if proc.returncode == 0:
                    base = os.path.splitext(puml_path)[0]
                    return f"{base}.{output_format}"
            except FileNotFoundError:
                pass
            return None

        try:
            subprocess.run(
                ["java", "-jar", plantuml_jar, f"-t{output_format}", puml_path],
                capture_output=True, text=True, timeout=60,
            )
            base = os.path.splitext(puml_path)[0]
            return f"{base}.{output_format}"
        except Exception:
            return None

    def write_puml(self, name: str, content: str) -> str:
        """写入 PlantUML 文件"""
        path = os.path.join(self.models_dir, f"{name}.puml")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def render_all(self) -> list[str]:
        """渲染所有 .puml 文件"""
        outputs = []
        if os.path.isdir(self.models_dir):
            for f in sorted(os.listdir(self.models_dir)):
                if f.endswith(".puml"):
                    puml_path = os.path.join(self.models_dir, f)
                    result = self.render_plantuml(puml_path)
                    if result:
                        outputs.append(result)
        return outputs

    @staticmethod
    def _find_plantuml() -> Optional[str]:
        """查找 plantuml.jar"""
        candidates = [
            "/usr/share/plantuml/plantuml.jar",
            "/usr/local/share/plantuml/plantuml.jar",
            os.path.expanduser("~/.local/share/plantuml/plantuml.jar"),
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        return None
