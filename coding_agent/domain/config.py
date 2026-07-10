from __future__ import annotations
from pathlib import Path
import yaml
from coding_agent.domain.models import ConfigData


class Config(ConfigData):
    """声明式配置，从 YAML 和 Markdown 规则文件加载"""

    project_rules: str = ""

    @classmethod
    def load(cls, project_dir: str | Path) -> "Config":
        project_dir = Path(project_dir).resolve()
        config = cls()

        yaml_path = project_dir / "config.yaml"
        if yaml_path.exists():
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            for key, value in data.items():
                if hasattr(config, key):
                    setattr(config, key, value)

        claude_path = project_dir / "CLAUDE.md"
        if claude_path.exists():
            with open(claude_path, "r", encoding="utf-8") as f:
                config.project_rules = f.read()

        agents_path = project_dir / "AGENTS.md"
        if agents_path.exists():
            with open(agents_path, "r", encoding="utf-8") as f:
                config.project_rules += "\n" + f.read()

        return config