import tempfile
from pathlib import Path
from coding_agent.domain.config import Config


def test_config_defaults():
    config = Config()
    assert config.max_steps == 50
    assert config.max_context_tokens == 8000
    assert config.max_retries == 3
    assert config.allowed_dirs == ["."]
    assert config.model_name == "gpt-4o"


def test_load_from_yaml():
    yaml_content = """
max_steps: 20
model_name: "gpt-3.5-turbo"
allowed_dirs:
  - "./src"
  - "./tests"
"""
    with tempfile.TemporaryDirectory() as td:
        config_path = Path(td) / "config.yaml"
        config_path.write_text(yaml_content)
        config = Config.load(td)
        assert config.max_steps == 20
        assert config.model_name == "gpt-3.5-turbo"
        assert config.allowed_dirs == ["./src", "./tests"]
        assert config.max_context_tokens == 8000  # default preserved


def test_load_without_config_file():
    with tempfile.TemporaryDirectory() as td:
        config = Config.load(td)
        assert config.max_steps == 50


def test_load_claude_md():
    claude_md = """# CLAUDE.md
本项目使用 pytest 进行测试，代码风格遵循 PEP 8。
"""
    with tempfile.TemporaryDirectory() as td:
        claude_path = Path(td) / "CLAUDE.md"
        claude_path.write_text(claude_md, encoding="utf-8")
        config = Config.load(td)
        assert "pytest" in config.project_rules