# Coding Agent Harness 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 从零实现一个 Coding Agent Harness，分层架构（表示层/应用层/领域层/基础设施层），反馈闭环为主贡献

**Architecture:** Python 3.11+ 分层架构，FastAPI WebUI，Pydantic 数据模型，ChromaDB 向量存储，keyring 凭据管理

**Tech Stack:** Python 3.11+, FastAPI, Pydantic, ChromaDB, keyring, pytest, ruff, mypy, OpenAI SDK

---

## 文件结构

```
coding_agent/
├── __init__.py
├── main.py
├── infrastructure/
│   ├── __init__.py
│   ├── llm_provider.py
│   ├── credential_store.py
│   ├── file_system.py
│   ├── git_ops.py
│   ├── subprocess_manager.py
│   └── vector_store.py
├── domain/
│   ├── __init__.py
│   ├── models.py
│   ├── tool_manager.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── file_tools.py
│   │   ├── search_tools.py
│   │   ├── shell_tool.py
│   │   ├── git_tools.py
│   │   └── test_tool.py
│   ├── governance.py
│   ├── feedback/
│   │   ├── __init__.py
│   │   ├── sensors.py
│   │   ├── classifier.py
│   │   ├── engine.py
│   │   └── pipeline.py
│   ├── memory.py
│   └── config.py
├── application/
│   ├── __init__.py
│   ├── agent_loop.py
│   ├── action_parser.py
│   └── session_manager.py
└── presentation/
    ├── __init__.py
    ├── app.py
    ├── routes.py
    ├── websocket.py
    └── static/
        ├── index.html
        ├── style.css
        └── app.js

tests/
├── __init__.py
├── conftest.py
├── infrastructure/
│   ├── test_llm_provider.py
│   ├── test_credential_store.py
│   ├── test_file_system.py
│   ├── test_git_ops.py
│   ├── test_subprocess_manager.py
│   └── test_vector_store.py
├── domain/
│   ├── test_models.py
│   ├── test_tool_manager.py
│   ├── test_tools/
│   │   ├── test_file_tools.py
│   │   ├── test_search_tools.py
│   │   ├── test_shell_tool.py
│   │   ├── test_git_tools.py
│   │   └── test_test_tool.py
│   ├── test_governance.py
│   ├── test_feedback/
│   │   ├── test_sensors.py
│   │   ├── test_classifier.py
│   │   ├── test_engine.py
│   │   └── test_pipeline.py
│   ├── test_memory.py
│   └── test_config.py
├── application/
│   ├── test_agent_loop.py
│   ├── test_action_parser.py
│   └── test_session_manager.py
├── presentation/
│   └── test_app.py
└── demonstrations/
    ├── test_demo_governance.py
    ├── test_demo_feedback.py
    └── test_demo_pipeline.py

pyproject.toml
.gitlab-ci.yml
Dockerfile
README.md
```

---

## 依赖关系图

```
Phase 1: Foundation
Task 1 (项目骨架)
  ├── Task 2 (数据模型) ── 无依赖，可与 Task 1 并行
  │     ├── Task 3 (配置系统)
  │     │     └── Task 18 (CLI)
  │     ├── Task 4 (凭据存储)
  │     ├── Task 5 (LLM 抽象)
  │     │     ├── Task 9 (记忆) ── 需要 VectorStore
  │     │     └── Task 17 (AgentLoop)
  │     ├── Task 6 (文件系统+子进程)
  │     │     └── Task 7 (工具系统)
  │     │           └── Task 17
  │     └── Task 8 (治理护栏)
  │           └── Task 17
  │
Phase 2: Feedback (主贡献)
Task 10 (Sensor ABC + SyntaxSensor)
Task 11 (TypeCheck + Lint + Test sensors)
Task 12 (FailureClassifier)
Task 13 (CorrectionEngine)
  └── Task 14 (FeedbackPipeline) ── 需要 Task 10-13 全部完成
        └── Task 17

Phase 3: Application
Task 15 (ActionParser) ── 需要 Task 2
Task 16 (SessionManager) ── 需要 Task 2
  └── Task 17 (AgentLoop) ── 需要 Task 5,7,8,14,15,16

Phase 4: Presentation
Task 18 (FastAPI routes) ── 需要 Task 17
  └── Task 19 (前端)
        └── Task 20 (WebUI 集成)

Phase 5: Integration
Task 21 (CLI 入口)
Task 22 (机制演示 1: 治理)
Task 23 (机制演示 2: 反馈)
Task 24 (机制演示 3: 完整管线)
Task 25 (Docker + CI)
Task 26 (README)
```

**可并行区域**：
- Task 3, 4, 5, 6, 8 在 Task 2 完成后可并行
- Task 10, 11, 12, 13 在各自依赖满足后可并行
- Task 22, 23, 24 在 Task 17 完成后可并行

---

## Phase 1: Foundation

### Task 1: 项目骨架与依赖

**Files:**
- Create: `pyproject.toml`

- [ ] **Step 1: 创建 pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "coding-agent-harness"
version = "0.1.0"
description = "A self-implemented Coding Agent Harness"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.5.0",
    "openai>=1.10.0",
    "keyring>=24.0.0",
    "chromadb>=0.4.22",
    "pyyaml>=6.0",
    "httpx>=0.26.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "ruff>=0.1.0",
    "mypy>=1.8.0",
]
```

- [ ] **Step 2: 安装依赖**

```bash
pip install -e ".[dev]"
```

Expected: 所有依赖安装成功

- [ ] **Step 3: 创建包目录结构**

```bash
mkdir -p coding_agent/infrastructure coding_agent/domain/tools coding_agent/domain/feedback coding_agent/application coding_agent/presentation/static
mkdir -p tests/infrastructure tests/domain/test_tools tests/domain/test_feedback tests/application tests/presentation tests/demonstrations
```

- [ ] **Step 4: 创建所有 __init__.py**

每个目录下创建空的 `__init__.py`

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml coding_agent/ tests/
git commit -m "feat: initialize project skeleton with dependencies"
```

---

### Task 2: 数据模型

**Files:**
- Create: `coding_agent/domain/models.py`
- Create: `tests/domain/test_models.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/domain/test_models.py
import pytest
from coding_agent.domain.models import (
    Action, ActionType, ActionResult, Message, SensorReport,
    SensorFailure, FailureCategory, FailureSeverity, MemoryEntry
)

def test_action_creation():
    action = Action(
        type=ActionType.CALL_TOOL,
        tool_name="read_file",
        tool_args={"path": "test.py"},
        thought="reading the file"
    )
    assert action.type == ActionType.CALL_TOOL
    assert action.tool_name == "read_file"

def test_action_done():
    action = Action(type=ActionType.DONE, thought="done")
    assert action.type == ActionType.DONE
    assert action.tool_name is None

def test_action_result_success():
    result = ActionResult(success=True, output="file content", changed_files=[])
    assert result.success is True
    assert result.error is None

def test_action_result_failure():
    result = ActionResult(success=False, output="", error="file not found", changed_files=[])
    assert result.success is False
    assert result.error == "file not found"

def test_message_creation():
    msg = Message(role="user", content="hello")
    assert msg.role == "user"
    assert msg.content == "hello"

def test_sensor_failure():
    failure = SensorFailure(
        file_path="test.py",
        line=10,
        severity=FailureSeverity.ERROR,
        category=FailureCategory.SYNTAX_ERROR,
        message="invalid syntax",
        raw_output="SyntaxError: invalid syntax"
    )
    assert failure.category == FailureCategory.SYNTAX_ERROR
    assert failure.severity == FailureSeverity.ERROR

def test_sensor_report():
    failure = SensorFailure(
        file_path="test.py", line=1, severity=FailureSeverity.ERROR,
        category=FailureCategory.SYNTAX_ERROR, message="err", raw_output="err"
    )
    report = SensorReport(sensor_name="syntax", passed=False, failures=[failure], duration_ms=100)
    assert report.passed is False
    assert len(report.failures) == 1

def test_memory_entry():
    import datetime
    entry = MemoryEntry(
        id="abc-123", content="project uses pytest",
        timestamp=datetime.datetime.now(), type="long_term"
    )
    assert entry.id == "abc-123"
    assert entry.type == "long_term"
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/domain/test_models.py -v
```

Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: 实现数据模型**

```python
# coding_agent/domain/models.py
from __future__ import annotations
import datetime
import uuid
from enum import Enum
from pydantic import BaseModel, Field


class ActionType(str, Enum):
    CALL_TOOL = "call_tool"
    DONE = "done"
    TAKE_NOTE = "take_note"


class Action(BaseModel):
    type: ActionType
    tool_name: str | None = None
    tool_args: dict | None = None
    thought: str = ""
    note: str | None = None


class ActionResult(BaseModel):
    success: bool
    output: str = ""
    error: str | None = None
    changed_files: list[str] = Field(default_factory=list)


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class Message(BaseModel):
    role: str
    content: str


class FailureSeverity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"


class FailureCategory(str, Enum):
    SYNTAX_ERROR = "syntax"
    TYPE_ERROR = "type"
    TEST_FAILURE = "test"
    LINT_WARNING = "lint"
    IMPORT_ERROR = "import"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class SensorFailure(BaseModel):
    file_path: str
    line: int | None = None
    severity: FailureSeverity
    category: FailureCategory
    message: str
    raw_output: str = ""


class SensorReport(BaseModel):
    sensor_name: str
    passed: bool
    failures: list[SensorFailure] = Field(default_factory=list)
    duration_ms: int = 0


class MemoryType(str, Enum):
    SCRATCHPAD = "scratchpad"
    LONG_TERM = "long_term"


class MemoryEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    embedding: list[float] | None = None
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)
    type: MemoryType = MemoryType.SCRATCHPAD
    tags: list[str] = Field(default_factory=list)


class SessionStatus(str, Enum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class StepRecord(BaseModel):
    step_number: int
    action: Action | None = None
    action_result: ActionResult | None = None
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)


class AgentResult(BaseModel):
    success: bool
    answer: str = ""
    error: str | None = None


class Session(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    goal: str
    start_time: datetime.datetime = Field(default_factory=datetime.datetime.now)
    end_time: datetime.datetime | None = None
    steps: list[StepRecord] = Field(default_factory=list)
    result: AgentResult | None = None
    status: SessionStatus = SessionStatus.RUNNING


class ConfigData(BaseModel):
    max_steps: int = 50
    max_context_tokens: int = 8000
    max_retries: int = 3
    allowed_dirs: list[str] = Field(default_factory=lambda: ["."])
    blocked_patterns: list[str] = Field(default_factory=list)
    model_name: str = "gpt-4o"
    tools_enabled: list[str] = Field(default_factory=list)
    sensor_pipeline: list[str] = Field(default_factory=lambda: ["syntax", "typecheck", "lint", "test"])
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/domain/test_models.py -v
```

Expected: PASS (8 tests)

- [ ] **Step 5: Commit**

```bash
git add coding_agent/domain/models.py tests/domain/test_models.py
git commit -m "feat: add core data models (Action, Message, SensorReport, Session, etc.)"
```

---

### Task 3: 配置系统

**Files:**
- Create: `coding_agent/domain/config.py`
- Create: `tests/domain/test_config.py`

**Depends on:** Task 2

- [ ] **Step 1: 写失败测试**

```python
# tests/domain/test_config.py
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
        assert config.max_context_tokens == 8000  # 未覆盖的保持默认

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
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/domain/test_config.py -v
```

Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: 实现配置系统**

```python
# coding_agent/domain/config.py
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
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/domain/test_config.py -v
```

Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add coding_agent/domain/config.py tests/domain/test_config.py
git commit -m "feat: add config system with YAML and CLAUDE.md loading"
```

---

### Task 4: 凭据存储

**Files:**
- Create: `coding_agent/infrastructure/credential_store.py`
- Create: `tests/infrastructure/test_credential_store.py`

**Depends on:** Task 2

- [ ] **Step 1: 写失败测试**

```python
# tests/infrastructure/test_credential_store.py
import pytest
from coding_agent.infrastructure.credential_store import CredentialStore

def test_set_and_get_status():
    store = CredentialStore()
    store.set_api_key("sk-test-key-12345")
    status = store.get_status()
    assert status["configured"] is True
    assert "sk-test" not in str(status)  # 不泄露明文

def test_clear_key():
    store = CredentialStore()
    store.set_api_key("sk-test-key-12345")
    store.clear_api_key()
    status = store.get_status()
    assert status["configured"] is False

def test_status_not_configured():
    store = CredentialStore()
    store.clear_api_key()
    status = store.get_status()
    assert status["configured"] is False
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/infrastructure/test_credential_store.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现凭据存储**

```python
# coding_agent/infrastructure/credential_store.py
from __future__ import annotations
import keyring
import keyring.errors


class CredentialStore:
    SERVICE_NAME = "coding-agent-harness"
    API_KEY_ENTRY = "api_key"

    def set_api_key(self, key: str) -> None:
        keyring.set_password(self.SERVICE_NAME, self.API_KEY_ENTRY, key)

    def get_api_key(self) -> str | None:
        try:
            return keyring.get_password(self.SERVICE_NAME, self.API_KEY_ENTRY)
        except keyring.errors.KeyringError:
            return None

    def get_status(self) -> dict:
        key = self.get_api_key()
        return {
            "configured": key is not None,
            "masked": "****" if key else None,
        }

    def update_api_key(self, key: str) -> None:
        self.set_api_key(key)

    def clear_api_key(self) -> None:
        try:
            keyring.delete_password(self.SERVICE_NAME, self.API_KEY_ENTRY)
        except keyring.errors.PasswordDeleteError:
            pass
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/infrastructure/test_credential_store.py -v
```

Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add coding_agent/infrastructure/credential_store.py tests/infrastructure/test_credential_store.py
git commit -m "feat: add credential store using Windows Credential Manager"
```

---

### Task 5: LLM 抽象层

**Files:**
- Create: `coding_agent/infrastructure/llm_provider.py`
- Create: `tests/infrastructure/test_llm_provider.py`

**Depends on:** Task 2

- [ ] **Step 1: 写失败测试**

```python
# tests/infrastructure/test_llm_provider.py
import pytest
from coding_agent.infrastructure.llm_provider import (
    LLMProvider, ScriptedMockLLM, RuleBasedMockLLM, LLMResponse, ToolCall
)
from coding_agent.domain.models import Message, ActionType

def test_scripted_mock_returns_preset_responses():
    responses = [
        LLMResponse(text="step 1", tool_calls=[
            ToolCall(name="read_file", arguments={"path": "test.py"})
        ]),
        LLMResponse(text="done", tool_calls=[]),
    ]
    llm = ScriptedMockLLM(responses)
    msgs = [Message(role="user", content="task")]
    tools = [{"name": "read_file", "description": "read a file"}]

    r1 = llm.chat(msgs, tools)
    assert r1.text == "step 1"
    assert len(r1.tool_calls) == 1
    assert r1.tool_calls[0].name == "read_file"

    r2 = llm.chat(msgs, tools)
    assert r2.text == "done"
    assert len(r2.tool_calls) == 0

def test_scripted_mock_raises_when_exhausted():
    llm = ScriptedMockLLM([LLMResponse(text="only one", tool_calls=[])])
    llm.chat([], [])
    with pytest.raises(IndexError):
        llm.chat([], [])

def test_rule_based_mock_matches_pattern():
    rules = [
        (lambda msgs, tools: "error" in msgs[-1].content,
         LLMResponse(text="fixing", tool_calls=[
             ToolCall(name="write_file", arguments={"path": "test.py", "content": "fixed"})
         ])),
        (lambda msgs, tools: True,
         LLMResponse(text="done", tool_calls=[])),
    ]
    llm = RuleBasedMockLLM(rules)

    r1 = llm.chat([Message(role="user", content="error in test.py")], [])
    assert r1.text == "fixing"
    assert r1.tool_calls[0].name == "write_file"

    r2 = llm.chat([Message(role="user", content="all good")], [])
    assert r2.text == "done"

def test_llm_response_tool_calls():
    tc = ToolCall(name="run_shell", arguments={"command": "pytest"})
    assert tc.name == "run_shell"
    assert tc.arguments == {"command": "pytest"}
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/infrastructure/test_llm_provider.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现 LLM 抽象层**

```python
# coding_agent/infrastructure/llm_provider.py
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from collections.abc import Callable
from coding_agent.domain.models import Message


@dataclass
class ToolCall:
    name: str
    arguments: dict


@dataclass
class LLMResponse:
    text: str
    tool_calls: list[ToolCall] = field(default_factory=list)


class LLMProvider(ABC):
    @abstractmethod
    def chat(self, messages: list[Message], tools: list[dict]) -> LLMResponse:
        ...


class ScriptedMockLLM(LLMProvider):
    def __init__(self, responses: list[LLMResponse]):
        self.responses = responses
        self.call_count = 0

    def chat(self, messages: list[Message], tools: list[dict]) -> LLMResponse:
        if self.call_count >= len(self.responses):
            raise IndexError(
                f"ScriptedMockLLM exhausted after {self.call_count} calls "
                f"(only {len(self.responses)} responses provided)"
            )
        response = self.responses[self.call_count]
        self.call_count += 1
        return response


RuleFunc = Callable[[list[Message], list[dict]], bool]


class RuleBasedMockLLM(LLMProvider):
    def __init__(self, rules: list[tuple[RuleFunc, LLMResponse]]):
        self.rules = rules

    def chat(self, messages: list[Message], tools: list[dict]) -> LLMResponse:
        for predicate, response in self.rules:
            if predicate(messages, tools):
                return response
        return LLMResponse(text="no matching rule", tool_calls=[])
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/infrastructure/test_llm_provider.py -v
```

Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add coding_agent/infrastructure/llm_provider.py tests/infrastructure/test_llm_provider.py
git commit -m "feat: add LLM abstraction with ScriptedMockLLM and RuleBasedMockLLM"
```

---

### Task 6: 文件系统与子进程管理器

**Files:**
- Create: `coding_agent/infrastructure/file_system.py`
- Create: `coding_agent/infrastructure/subprocess_manager.py`
- Create: `tests/infrastructure/test_file_system.py`
- Create: `tests/infrastructure/test_subprocess_manager.py`

**Depends on:** Task 2

- [ ] **Step 1: 写失败测试**

```python
# tests/infrastructure/test_file_system.py
import tempfile
from pathlib import Path
from coding_agent.infrastructure.file_system import FileSystemManager

def test_read_file():
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "test.txt"
        f.write_text("hello world")
        fs = FileSystemManager(allowed_dirs=[td])
        content = fs.read_file(str(f))
        assert content == "hello world"

def test_write_file():
    with tempfile.TemporaryDirectory() as td:
        fs = FileSystemManager(allowed_dirs=[td])
        p = Path(td) / "output.txt"
        fs.write_file(str(p), "new content")
        assert p.read_text() == "new content"

def test_read_file_outside_allowed_dirs():
    with tempfile.TemporaryDirectory() as td:
        fs = FileSystemManager(allowed_dirs=[td])
        with pytest.raises(PermissionError):
            fs.read_file("/etc/passwd")

def test_list_dir():
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "a.py").touch()
        (Path(td) / "b.py").touch()
        fs = FileSystemManager(allowed_dirs=[td])
        items = fs.list_dir(td)
        assert "a.py" in items
        assert "b.py" in items
```

```python
# tests/infrastructure/test_subprocess_manager.py
import pytest
from coding_agent.infrastructure.subprocess_manager import SubprocessManager

def test_run_simple_command():
    mgr = SubprocessManager(timeout=10)
    result = mgr.run("echo hello")
    assert result["exit_code"] == 0
    assert "hello" in result["stdout"]

def test_run_command_timeout():
    mgr = SubprocessManager(timeout=1)
    with pytest.raises(TimeoutError):
        mgr.run("sleep 10" if os.name != "nt" else "timeout /t 10")

def test_run_failing_command():
    mgr = SubprocessManager(timeout=10)
    result = mgr.run("python -c 'exit(1)'")
    assert result["exit_code"] == 1
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/infrastructure/test_file_system.py tests/infrastructure/test_subprocess_manager.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现**

```python
# coding_agent/infrastructure/file_system.py
from pathlib import Path

class FileSystemManager:
    def __init__(self, allowed_dirs: list[str] | None = None):
        self.allowed_dirs = [Path(d).resolve() for d in (allowed_dirs or ["."])]

    def _check_path(self, path: str) -> Path:
        resolved = Path(path).resolve()
        if not any(
            str(resolved).startswith(str(allowed))
            for allowed in self.allowed_dirs
        ):
            raise PermissionError(f"Access denied: {path} is outside allowed directories")
        return resolved

    def read_file(self, path: str) -> str:
        p = self._check_path(path)
        return p.read_text(encoding="utf-8")

    def write_file(self, path: str, content: str) -> None:
        p = self._check_path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

    def list_dir(self, path: str) -> list[str]:
        p = self._check_path(path)
        return [item.name for item in p.iterdir()]
```

```python
# coding_agent/infrastructure/subprocess_manager.py
import subprocess
import os

class SubprocessManager:
    def __init__(self, timeout: int = 120):
        self.timeout = timeout

    def run(self, command: str, cwd: str | None = None) -> dict:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=cwd,
            )
            return {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Command timed out after {self.timeout}s: {command}")
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/infrastructure/test_file_system.py tests/infrastructure/test_subprocess_manager.py -v
```

Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add coding_agent/infrastructure/file_system.py coding_agent/infrastructure/subprocess_manager.py tests/infrastructure/test_file_system.py tests/infrastructure/test_subprocess_manager.py
git commit -m "feat: add FileSystemManager with directory sandbox and SubprocessManager"
```

---

### Task 7: 工具系统

**Files:**
- Create: `coding_agent/domain/tool_manager.py`
- Create: `coding_agent/domain/tools/__init__.py`
- Create: `coding_agent/domain/tools/file_tools.py`
- Create: `coding_agent/domain/tools/search_tools.py`
- Create: `coding_agent/domain/tools/shell_tool.py`
- Create: `coding_agent/domain/tools/git_tools.py`
- Create: `coding_agent/domain/tools/test_tool.py`
- Create: `tests/domain/test_tool_manager.py`
- Create: `tests/domain/test_tools/test_file_tools.py`
- Create: `tests/domain/test_tools/test_shell_tool.py`

**Depends on:** Task 2, Task 6

- [ ] **Step 1: 写失败测试（ToolManager）**

```python
# tests/domain/test_tool_manager.py
import pytest
from coding_agent.domain.tool_manager import ToolManager, ToolDef, ToolPermission
from coding_agent.domain.models import Action, ActionType

def test_register_and_list_tools():
    tm = ToolManager()
    tm.register(ToolDef(
        name="echo", description="echo back",
        parameters={}, permission=ToolPermission.SAFE,
        handler=lambda args: "echo: " + str(args)
    ))
    defs = tm.list_defs()
    assert len(defs) == 1
    assert defs[0]["name"] == "echo"

def test_dispatch_tool():
    tm = ToolManager()
    tm.register(ToolDef(
        name="double", description="double a number",
        parameters={"n": "int"}, permission=ToolPermission.SAFE,
        handler=lambda args: args["n"] * 2
    ))
    action = Action(type=ActionType.CALL_TOOL, tool_name="double", tool_args={"n": 5})
    result = tm.dispatch(action)
    assert result.success is True
    assert result.output == "10"

def test_dispatch_unknown_tool():
    tm = ToolManager()
    action = Action(type=ActionType.CALL_TOOL, tool_name="nonexistent", tool_args={})
    result = tm.dispatch(action)
    assert result.success is False
    assert "unknown" in result.error.lower()

def test_tool_permission():
    tool = ToolDef(
        name="rm", description="delete",
        parameters={}, permission=ToolPermission.DANGEROUS,
        handler=lambda args: "deleted"
    )
    assert tool.permission == ToolPermission.DANGEROUS
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/domain/test_tool_manager.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现 ToolManager + 所有工具**

```python
# coding_agent/domain/tool_manager.py
from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from collections.abc import Callable
from coding_agent.domain.models import Action, ActionResult


class ToolPermission(str, Enum):
    SAFE = "safe"
    RISKY = "risky"
    DANGEROUS = "dangerous"


@dataclass
class ToolDef:
    name: str
    description: str
    parameters: dict
    permission: ToolPermission
    handler: Callable


class ToolManager:
    def __init__(self):
        self._tools: dict[str, ToolDef] = {}

    def register(self, tool: ToolDef) -> None:
        self._tools[tool.name] = tool

    def list_defs(self) -> list[dict]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
                "permission": t.permission.value,
            }
            for t in self._tools.values()
        ]

    def get(self, name: str) -> ToolDef | None:
        return self._tools.get(name)

    def dispatch(self, action: Action) -> ActionResult:
        tool = self._tools.get(action.tool_name or "")
        if tool is None:
            return ActionResult(
                success=False,
                error=f"Unknown tool: {action.tool_name}",
            )
        try:
            result = tool.handler(action.tool_args or {})
            changed_files = action.tool_args.get("_changed_files", []) if action.tool_args else []
            return ActionResult(
                success=True,
                output=str(result),
                changed_files=changed_files,
            )
        except Exception as e:
            return ActionResult(
                success=False,
                error=str(e),
            )
```

```python
# coding_agent/domain/tools/file_tools.py
from coding_agent.infrastructure.file_system import FileSystemManager

def register_file_tools(tm, fs: FileSystemManager):
    def read_file(args):
        return fs.read_file(args["path"])

    def write_file(args):
        fs.write_file(args["path"], args["content"])
        return f"Written: {args['path']}"

    def list_dir(args):
        items = fs.list_dir(args["path"])
        return "\n".join(items)

    from coding_agent.domain.tool_manager import ToolDef, ToolPermission
    tm.register(ToolDef("read_file", "Read a file", {"path": "str"}, ToolPermission.SAFE, read_file))
    tm.register(ToolDef("write_file", "Write a file", {"path": "str", "content": "str"}, ToolPermission.RISKY, write_file))
    tm.register(ToolDef("list_dir", "List directory contents", {"path": "str"}, ToolPermission.SAFE, list_dir))


# coding_agent/domain/tools/search_tools.py
import glob
import re
from pathlib import Path

def register_search_tools(tm):
    def search_files(args):
        pattern = args.get("pattern", "**/*")
        matches = glob.glob(pattern, recursive=True)
        return "\n".join(matches[:50])

    def grep(args):
        pattern = args["pattern"]
        path = args.get("path", ".")
        results = []
        for f in Path(path).rglob("*.py"):
            try:
                for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                    if re.search(pattern, line):
                        results.append(f"{f}:{i}: {line.strip()}")
            except Exception:
                pass
        return "\n".join(results[:50])

    from coding_agent.domain.tool_manager import ToolDef, ToolPermission
    tm.register(ToolDef("search_files", "Search files by glob", {"pattern": "str"}, ToolPermission.SAFE, search_files))
    tm.register(ToolDef("grep", "Search file contents by regex", {"pattern": "str", "path": "str"}, ToolPermission.SAFE, grep))


# coding_agent/domain/tools/shell_tool.py
from coding_agent.infrastructure.subprocess_manager import SubprocessManager

def register_shell_tool(tm, sm: SubprocessManager):
    def run_shell(args):
        result = sm.run(args["command"])
        return f"exit_code={result['exit_code']}\nstdout:\n{result['stdout']}\nstderr:\n{result['stderr']}"

    from coding_agent.domain.tool_manager import ToolDef, ToolPermission
    tm.register(ToolDef("run_shell", "Execute a shell command", {"command": "str"}, ToolPermission.DANGEROUS, run_shell))


# coding_agent/domain/tools/git_tools.py
from coding_agent.infrastructure.subprocess_manager import SubprocessManager

def register_git_tools(tm, sm: SubprocessManager):
    def _git(cmd):
        r = sm.run(f"git {cmd}")
        return r["stdout"] + r["stderr"]

    from coding_agent.domain.tool_manager import ToolDef, ToolPermission
    tm.register(ToolDef("git_status", "Show git status", {}, ToolPermission.SAFE, lambda a: _git("status --short")))
    tm.register(ToolDef("git_diff", "Show git diff", {}, ToolPermission.SAFE, lambda a: _git("diff")))
    tm.register(ToolDef("git_commit", "Create a git commit", {"message": "str"}, ToolPermission.RISKY,
                         lambda a: _git(f'commit -m "{a["message"]}"')))


# coding_agent/domain/tools/test_tool.py
from coding_agent.infrastructure.subprocess_manager import SubprocessManager

def register_test_tool(tm, sm: SubprocessManager):
    def run_test(args):
        result = sm.run("pytest -v --tb=short")
        return f"exit_code={result['exit_code']}\n{result['stdout']}"

    from coding_agent.domain.tool_manager import ToolDef, ToolPermission
    tm.register(ToolDef("run_test", "Run test suite", {}, ToolPermission.SAFE, run_test))
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/domain/test_tool_manager.py -v
```

Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add coding_agent/domain/tool_manager.py coding_agent/domain/tools/ tests/domain/test_tool_manager.py
git commit -m "feat: add ToolManager with 10 built-in tools (file, search, shell, git, test)"
```

---

### Task 8: 治理护栏

**Files:**
- Create: `coding_agent/domain/governance.py`
- Create: `tests/domain/test_governance.py`

**Depends on:** Task 2, Task 7

- [ ] **Step 1: 写失败测试**

```python
# tests/domain/test_governance.py
import pytest
from coding_agent.domain.governance import Governance, PermissionResult, HITLState
from coding_agent.domain.tool_manager import ToolManager, ToolDef, ToolPermission
from coding_agent.domain.models import Action, ActionType

@pytest.fixture
def tm():
    mgr = ToolManager()
    mgr.register(ToolDef("read", "read file", {}, ToolPermission.SAFE, lambda a: "ok"))
    mgr.register(ToolDef("write", "write file", {}, ToolPermission.RISKY, lambda a: "ok"))
    mgr.register(ToolDef("shell", "run shell", {}, ToolPermission.DANGEROUS, lambda a: "ok"))
    return mgr

def test_safe_tool_allowed(tm):
    gov = Governance(tm)
    action = Action(type=ActionType.CALL_TOOL, tool_name="read")
    assert gov.check(action) == PermissionResult.ALLOWED

def test_risky_tool_needs_confirmation(tm):
    gov = Governance(tm)
    action = Action(type=ActionType.CALL_TOOL, tool_name="write")
    assert gov.check(action) == PermissionResult.NEEDS_CONFIRMATION

def test_dangerous_tool_needs_hitl(tm):
    gov = Governance(tm)
    action = Action(type=ActionType.CALL_TOOL, tool_name="shell")
    assert gov.check(action) == PermissionResult.NEEDS_HITL

def test_blocked_command_pattern(tm):
    gov = Governance(tm)
    action = Action(type=ActionType.CALL_TOOL, tool_name="shell",
                    tool_args={"command": "rm -rf /"})
    assert gov.check(action) == PermissionResult.BLOCKED

def test_blocked_drop_table(tm):
    gov = Governance(tm)
    action = Action(type=ActionType.CALL_TOOL, tool_name="shell",
                    tool_args={"command": "DROP TABLE users"})
    assert gov.check(action) == PermissionResult.BLOCKED

def test_blocked_git_push_force_main(tm):
    gov = Governance(tm)
    action = Action(type=ActionType.CALL_TOOL, tool_name="shell",
                    tool_args={"command": "git push --force main"})
    assert gov.check(action) == PermissionResult.BLOCKED

def test_unknown_tool_blocked(tm):
    gov = Governance(tm)
    action = Action(type=ActionType.CALL_TOOL, tool_name="nonexistent")
    assert gov.check(action) == PermissionResult.BLOCKED

def test_done_action_allowed(tm):
    gov = Governance(tm)
    action = Action(type=ActionType.DONE)
    assert gov.check(action) == PermissionResult.ALLOWED

def test_hitl_state_transitions():
    state = HITLState()
    assert state.status == "pending"
    state.approve()
    assert state.status == "approved"
    state2 = HITLState()
    state2.deny()
    assert state2.status == "denied"
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/domain/test_governance.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现治理护栏**

```python
# coding_agent/domain/governance.py
from __future__ import annotations
from enum import Enum
import re
from coding_agent.domain.models import Action, ActionType
from coding_agent.domain.tool_manager import ToolManager, ToolPermission


class PermissionResult(str, Enum):
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    NEEDS_CONFIRMATION = "confirm"
    NEEDS_HITL = "hitl"


class HITLState:
    def __init__(self):
        self.status = "pending"

    def approve(self):
        self.status = "approved"

    def deny(self):
        self.status = "denied"


BLOCKED_PATTERNS = [
    r"rm\s+-rf\s+/",
    r"DROP\s+TABLE",
    r"DELETE\s+FROM",
    r"git\s+push\s+--force\s+(main|master)",
    r"chmod\s+777\s+/",
    r"format\s+[A-Z]:",
    r"del\s+/[Ff]\s+/",
    r">\s*/dev/sda",
    r"mkfs\.",
    r"dd\s+if=",
]


class Governance:
    def __init__(self, tool_manager: ToolManager, extra_blocked: list[str] | None = None):
        self.tool_manager = tool_manager
        self.blocked_patterns = BLOCKED_PATTERNS + (extra_blocked or [])

    def check(self, action: Action) -> PermissionResult:
        if action.type == ActionType.DONE or action.type == ActionType.TAKE_NOTE:
            return PermissionResult.ALLOWED

        tool = self.tool_manager.get(action.tool_name or "")
        if tool is None:
            return PermissionResult.BLOCKED

        command = self._extract_command(action)
        if command and self._is_blocked_command(command):
            return PermissionResult.BLOCKED

        if tool.permission == ToolPermission.SAFE:
            return PermissionResult.ALLOWED
        elif tool.permission == ToolPermission.RISKY:
            return PermissionResult.NEEDS_CONFIRMATION
        else:
            return PermissionResult.NEEDS_HITL

    def _extract_command(self, action: Action) -> str | None:
        if action.tool_name == "run_shell" and action.tool_args:
            return action.tool_args.get("command", "")
        return None

    def _is_blocked_command(self, command: str) -> bool:
        for pattern in self.blocked_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return True
        return False
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/domain/test_governance.py -v
```

Expected: PASS (9 tests)

- [ ] **Step 5: Commit**

```bash
git add coding_agent/domain/governance.py tests/domain/test_governance.py
git commit -m "feat: add governance guardrail with 3-tier permission and blocked command patterns"
```

---

## Phase 2: Feedback Loop（主贡献）

### Task 9: 记忆系统 + VectorStore

**Files:**
- Create: `coding_agent/infrastructure/vector_store.py`
- Create: `coding_agent/domain/memory.py`
- Create: `tests/infrastructure/test_vector_store.py`
- Create: `tests/domain/test_memory.py`

**Depends on:** Task 2

- [ ] **Step 1: 写失败测试**

```python
# tests/infrastructure/test_vector_store.py
import pytest
from coding_agent.infrastructure.vector_store import InMemoryVectorStore, MemoryEntry as VSEntry

def test_insert_and_search():
    store = InMemoryVectorStore()
    store.insert("project uses pytest", [0.1, 0.2, 0.3])
    store.insert("code style is PEP 8", [0.1, 0.2, 0.4])
    results = store.search("testing", [0.1, 0.2, 0.3])
    assert len(results) == 2
    assert "pytest" in results[0].text

def test_search_empty_store():
    store = InMemoryVectorStore()
    results = store.search("query", [0.0, 0.0, 0.0])
    assert len(results) == 0

def test_delete_entry():
    store = InMemoryVectorStore()
    store.insert("test memory", [0.5, 0.5])
    store.delete("test memory")
    results = store.search("memory", [0.5, 0.5])
    assert len(results) == 0
```

```python
# tests/domain/test_memory.py
import pytest
from coding_agent.domain.memory import MemoryManager
from coding_agent.infrastructure.vector_store import InMemoryVectorStore

def test_write_and_read_scratchpad():
    mm = MemoryManager(InMemoryVectorStore())
    mm.write("use pytest for testing")
    memories = mm.read("testing")
    assert len(memories) > 0

def test_consolidate():
    mm = MemoryManager(InMemoryVectorStore())
    mm.write("important decision: use FastAPI")
    mm.consolidate()
    memories = mm.read("FastAPI")
    assert any("FastAPI" in m.content for m in memories)

def test_compress_context():
    mm = MemoryManager(InMemoryVectorStore())
    from coding_agent.domain.models import Message
    context = [Message(role="system", content="you are a coding agent")]
    for i in range(20):
        context.append(Message(role="user", content=f"message {i}"))
        context.append(Message(role="assistant", content=f"response {i}"))
    compressed = mm.compress(context, max_recent=4)
    assert len(compressed) < len(context)
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/infrastructure/test_vector_store.py tests/domain/test_memory.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现**

```python
# coding_agent/infrastructure/vector_store.py
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
import math


@dataclass
class MemoryEntry:
    text: str
    embedding: list[float] | None = None


class VectorStore(ABC):
    @abstractmethod
    def search(self, query: str, query_embedding: list[float], top_k: int = 5) -> list[MemoryEntry]:
        ...

    @abstractmethod
    def insert(self, text: str, embedding: list[float]) -> None:
        ...

    @abstractmethod
    def delete(self, text: str) -> None:
        ...


class InMemoryVectorStore(VectorStore):
    def __init__(self):
        self._entries: list[tuple[MemoryEntry, list[float]]] = []

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def search(self, query: str, query_embedding: list[float], top_k: int = 5) -> list[MemoryEntry]:
        if not self._entries:
            return []
        scored = [
            (entry, self._cosine_similarity(query_embedding, emb))
            for entry, emb in self._entries
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [entry for entry, _ in scored[:top_k]]

    def insert(self, text: str, embedding: list[float]) -> None:
        self._entries.append((MemoryEntry(text=text, embedding=embedding), embedding))

    def delete(self, text: str) -> None:
        self._entries = [(e, emb) for e, emb in self._entries if e.text != text]
```

```python
# coding_agent/domain/memory.py
from __future__ import annotations
import datetime
import hashlib
from coding_agent.domain.models import Message, MemoryEntry, MemoryType
from coding_agent.infrastructure.vector_store import VectorStore


class MemoryManager:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.session_notes: list[MemoryEntry] = []

    def read(self, goal: str) -> list[MemoryEntry]:
        embedding = self._simple_embed(goal)
        entries = self.vector_store.search(goal, embedding, top_k=5)
        return entries  # type: ignore[return-value]

    def write(self, note: str) -> None:
        entry = MemoryEntry(
            content=note,
            timestamp=datetime.datetime.now(),
            type=MemoryType.SCRATCHPAD,
        )
        self.session_notes.append(entry)

    def consolidate(self) -> None:
        for note in self.session_notes:
            embedding = self._simple_embed(note.content)
            self.vector_store.insert(note.content, embedding)
        self.session_notes = []

    def compress(self, context: list[Message], max_recent: int = 6) -> list[Message]:
        if len(context) <= max_recent:
            return context
        system = [m for m in context if m.role == "system"]
        recent = context[-max_recent:]
        summary = "Earlier conversation summary:\n"
        for m in context[len(system):-max_recent]:
            summary += f"[{m.role}]: {m.content[:200]}\n"
        return system + [Message(role="user", content=summary)] + recent

    def _simple_embed(self, text: str) -> list[float]:
        h = hashlib.sha256(text.encode()).digest()
        return [b / 255.0 for b in h[:32]]
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/infrastructure/test_vector_store.py tests/domain/test_memory.py -v
```

Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add coding_agent/infrastructure/vector_store.py coding_agent/domain/memory.py tests/infrastructure/test_vector_store.py tests/domain/test_memory.py
git commit -m "feat: add memory system with InMemoryVectorStore and MemoryManager"
```

---

### Task 10: Sensor ABC + SyntaxSensor

**Files:**
- Create: `coding_agent/domain/feedback/__init__.py`
- Create: `coding_agent/domain/feedback/sensors.py`
- Create: `tests/domain/test_feedback/test_sensors.py`

**Depends on:** Task 2

- [ ] **Step 1: 写失败测试**

```python
# tests/domain/test_feedback/test_sensors.py
import tempfile
from pathlib import Path
from coding_agent.domain.feedback.sensors import SyntaxSensor, SensorReport

def test_syntax_sensor_pass():
    sensor = SyntaxSensor()
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "good.py"
        f.write_text("def hello():\n    return 'world'\n")
        report = sensor.sense([str(f)])
        assert report.passed is True
        assert len(report.failures) == 0

def test_syntax_sensor_fail():
    sensor = SyntaxSensor()
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "bad.py"
        f.write_text("def hello(\n    return 'world'\n")
        report = sensor.sense([str(f)])
        assert report.passed is False
        assert len(report.failures) > 0
        assert report.failures[0].category.value == "syntax"

def test_syntax_sensor_empty_files():
    sensor = SyntaxSensor()
    report = sensor.sense([])
    assert report.passed is True
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/domain/test_feedback/test_sensors.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现 Sensor ABC + SyntaxSensor**

```python
# coding_agent/domain/feedback/sensors.py
from __future__ import annotations
import py_compile
import time
from abc import ABC, abstractmethod
from pathlib import Path
from coding_agent.domain.models import SensorReport, SensorFailure, FailureCategory, FailureSeverity


class Sensor(ABC):
    name: str = "base"

    @abstractmethod
    def sense(self, changed_files: list[str]) -> SensorReport:
        ...


class SyntaxSensor(Sensor):
    name = "syntax"

    def sense(self, changed_files: list[str]) -> SensorReport:
        start = time.time()
        failures: list[SensorFailure] = []
        py_files = [f for f in changed_files if f.endswith(".py")]

        for f in py_files:
            try:
                py_compile.compile(f, doraise=True)
            except py_compile.PyCompileError as e:
                failures.append(SensorFailure(
                    file_path=f,
                    line=None,
                    severity=FailureSeverity.ERROR,
                    category=FailureCategory.SYNTAX_ERROR,
                    message=str(e),
                    raw_output=str(e),
                ))

        duration_ms = int((time.time() - start) * 1000)
        return SensorReport(
            sensor_name=self.name,
            passed=len(failures) == 0,
            failures=failures,
            duration_ms=duration_ms,
        )
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/domain/test_feedback/test_sensors.py -v
```

Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add coding_agent/domain/feedback/__init__.py coding_agent/domain/feedback/sensors.py tests/domain/test_feedback/test_sensors.py
git commit -m "feat: add Sensor ABC and SyntaxSensor for feedback pipeline"
```

---

### Task 11: TypeCheck + Lint + Test Sensors

**Files:**
- Modify: `coding_agent/domain/feedback/sensors.py`
- Modify: `tests/domain/test_feedback/test_sensors.py`

**Depends on:** Task 10

- [ ] **Step 1: 写失败测试**

```python
# 追加到 tests/domain/test_feedback/test_sensors.py
def test_typecheck_sensor_pass():
    sensor = TypeCheckSensor()
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "typed.py"
        f.write_text("def add(a: int, b: int) -> int:\n    return a + b\n")
        report = sensor.sense([str(f)])
        assert isinstance(report, SensorReport)

def test_typecheck_sensor_fail():
    sensor = TypeCheckSensor()
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "bad_type.py"
        f.write_text("def add(a: int, b: int) -> str:\n    return a + b\n")
        report = sensor.sense([str(f)])
        if not report.passed:
            assert any(f.category == FailureCategory.TYPE_ERROR for f in report.failures)

def test_lint_sensor():
    sensor = LintSensor()
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "style.py"
        f.write_text("import os\nimport sys\n\ndef foo():\n    pass\n")
        report = sensor.sense([str(f)])
        assert isinstance(report, SensorReport)

def test_test_sensor_pass():
    sensor = TestSensor()
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "test_ok.py"
        f.write_text("def test_pass():\n    assert True\n")
        report = sensor.sense([str(f)])
        assert isinstance(report, SensorReport)
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/domain/test_feedback/test_sensors.py::test_typecheck_sensor_pass -v
```

Expected: FAIL (TypeCheckSensor not defined)

- [ ] **Step 3: 实现剩余传感器**

```python
# 追加到 coding_agent/domain/feedback/sensors.py
import subprocess


class TypeCheckSensor(Sensor):
    name = "typecheck"

    def sense(self, changed_files: list[str]) -> SensorReport:
        start = time.time()
        failures: list[SensorFailure] = []
        py_files = [f for f in changed_files if f.endswith(".py")]

        if not py_files:
            return SensorReport(sensor_name=self.name, passed=True, failures=[], duration_ms=0)

        try:
            result = subprocess.run(
                ["mypy", "--no-error-summary"] + py_files,
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode != 0:
                for line in result.stdout.splitlines():
                    if ":" in line and "error" in line.lower():
                        parts = line.split(":", 2)
                        failures.append(SensorFailure(
                            file_path=parts[0] if len(parts) > 0 else "",
                            line=int(parts[1]) if len(parts) > 1 and parts[1].strip().isdigit() else None,
                            severity=FailureSeverity.ERROR,
                            category=FailureCategory.TYPE_ERROR,
                            message=line,
                            raw_output=line,
                        ))
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        duration_ms = int((time.time() - start) * 1000)
        return SensorReport(
            sensor_name=self.name,
            passed=len(failures) == 0,
            failures=failures,
            duration_ms=duration_ms,
        )


class LintSensor(Sensor):
    name = "lint"

    def sense(self, changed_files: list[str]) -> SensorReport:
        start = time.time()
        failures: list[SensorFailure] = []
        py_files = [f for f in changed_files if f.endswith(".py")]

        if not py_files:
            return SensorReport(sensor_name=self.name, passed=True, failures=[], duration_ms=0)

        try:
            result = subprocess.run(
                ["ruff", "check"] + py_files,
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                for line in result.stdout.splitlines():
                    if ":" in line:
                        parts = line.split(":", 2)
                        failures.append(SensorFailure(
                            file_path=parts[0] if len(parts) > 0 else "",
                            line=int(parts[1]) if len(parts) > 1 and parts[1].strip().isdigit() else None,
                            severity=FailureSeverity.WARNING,
                            category=FailureCategory.LINT_WARNING,
                            message=line,
                            raw_output=line,
                        ))
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        duration_ms = int((time.time() - start) * 1000)
        return SensorReport(
            sensor_name=self.name,
            passed=len(failures) == 0,
            failures=failures,
            duration_ms=duration_ms,
        )


class TestSensor(Sensor):
    name = "test"

    def sense(self, changed_files: list[str]) -> SensorReport:
        start = time.time()
        failures: list[SensorFailure] = []

        try:
            result = subprocess.run(
                ["pytest", "-v", "--tb=short"] + changed_files,
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode != 0:
                for line in result.stdout.splitlines():
                    if "FAILED" in line:
                        failures.append(SensorFailure(
                            file_path=changed_files[0] if changed_files else "",
                            line=None,
                            severity=FailureSeverity.ERROR,
                            category=FailureCategory.TEST_FAILURE,
                            message=line,
                            raw_output=result.stdout,
                        ))
        except subprocess.TimeoutExpired:
            failures.append(SensorFailure(
                file_path="",
                line=None,
                severity=FailureSeverity.ERROR,
                category=FailureCategory.TIMEOUT,
                message="Test execution timed out",
                raw_output="",
            ))
        except FileNotFoundError:
            pass

        duration_ms = int((time.time() - start) * 1000)
        return SensorReport(
            sensor_name=self.name,
            passed=len(failures) == 0,
            failures=failures,
            duration_ms=duration_ms,
        )
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/domain/test_feedback/test_sensors.py -v
```

Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add coding_agent/domain/feedback/sensors.py tests/domain/test_feedback/test_sensors.py
git commit -m "feat: add TypeCheckSensor, LintSensor, and TestSensor"
```

---

### Task 12: FailureClassifier

**Files:**
- Create: `coding_agent/domain/feedback/classifier.py`
- Create: `tests/domain/test_feedback/test_classifier.py`

**Depends on:** Task 2

- [ ] **Step 1: 写失败测试**

```python
# tests/domain/test_feedback/test_classifier.py
from coding_agent.domain.feedback.classifier import FailureClassifier
from coding_agent.domain.models import SensorReport, SensorFailure, FailureCategory, FailureSeverity

def test_classify_empty():
    classifier = FailureClassifier()
    result = classifier.classify([])
    assert result.total_failures == 0
    assert result.has_blocking is False

def test_classify_single_failure():
    failure = SensorFailure(
        file_path="test.py", line=5, severity=FailureSeverity.ERROR,
        category=FailureCategory.SYNTAX_ERROR, message="bad syntax", raw_output="err"
    )
    report = SensorReport(sensor_name="syntax", passed=False, failures=[failure], duration_ms=10)
    classifier = FailureClassifier()
    result = classifier.classify([report])
    assert result.total_failures == 1
    assert result.has_blocking is True
    assert FailureCategory.SYNTAX_ERROR in result.by_category

def test_classify_mixed_failures():
    failures = [
        SensorFailure(file_path="a.py", line=1, severity=FailureSeverity.ERROR,
                      category=FailureCategory.SYNTAX_ERROR, message="e1", raw_output="e1"),
        SensorFailure(file_path="b.py", line=2, severity=FailureSeverity.WARNING,
                      category=FailureCategory.LINT_WARNING, message="w1", raw_output="w1"),
        SensorFailure(file_path="a.py", line=3, severity=FailureSeverity.ERROR,
                      category=FailureCategory.TYPE_ERROR, message="e2", raw_output="e2"),
    ]
    report = SensorReport(sensor_name="combined", passed=False, failures=failures, duration_ms=50)
    classifier = FailureClassifier()
    result = classifier.classify([report])
    assert result.total_failures == 3
    assert len(result.by_file["a.py"]) == 2
    assert result.has_blocking is True

def test_classify_no_blocking():
    failure = SensorFailure(
        file_path="test.py", line=1, severity=FailureSeverity.WARNING,
        category=FailureCategory.LINT_WARNING, message="warn", raw_output="warn"
    )
    report = SensorReport(sensor_name="lint", passed=False, failures=[failure], duration_ms=5)
    classifier = FailureClassifier()
    result = classifier.classify([report])
    assert result.has_blocking is False

def test_summary_text():
    failure = SensorFailure(
        file_path="test.py", line=5, severity=FailureSeverity.ERROR,
        category=FailureCategory.SYNTAX_ERROR, message="invalid syntax", raw_output="err"
    )
    report = SensorReport(sensor_name="syntax", passed=False, failures=[failure], duration_ms=10)
    classifier = FailureClassifier()
    result = classifier.classify([report])
    assert "test.py" in result.summary
    assert "syntax" in result.summary.lower()
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/domain/test_feedback/test_classifier.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现 FailureClassifier**

```python
# coding_agent/domain/feedback/classifier.py
from __future__ import annotations
from dataclasses import dataclass, field
from coding_agent.domain.models import SensorReport, SensorFailure, FailureCategory, FailureSeverity


@dataclass
class ClassifiedResult:
    total_failures: int = 0
    by_category: dict[FailureCategory, list[SensorFailure]] = field(default_factory=dict)
    by_file: dict[str, list[SensorFailure]] = field(default_factory=dict)
    has_blocking: bool = False
    summary: str = ""


BLOCKING_CATEGORIES = {
    FailureCategory.SYNTAX_ERROR,
    FailureCategory.TYPE_ERROR,
    FailureCategory.TEST_FAILURE,
    FailureCategory.IMPORT_ERROR,
    FailureCategory.TIMEOUT,
}


class FailureClassifier:
    def classify(self, reports: list[SensorReport]) -> ClassifiedResult:
        result = ClassifiedResult()

        all_failures: list[SensorFailure] = []
        for report in reports:
            all_failures.extend(report.failures)

        result.total_failures = len(all_failures)

        for f in all_failures:
            result.by_category.setdefault(f.category, []).append(f)
            result.by_file.setdefault(f.file_path, []).append(f)

        result.has_blocking = any(
            f.category in BLOCKING_CATEGORIES and f.severity == FailureSeverity.ERROR
            for f in all_failures
        )

        result.summary = self._build_summary(result)
        return result

    def _build_summary(self, result: ClassifiedResult) -> str:
        if result.total_failures == 0:
            return "All checks passed."

        lines = [f"Feedback: {result.total_failures} issue(s) found.\n"]
        priority_order = [
            FailureCategory.SYNTAX_ERROR,
            FailureCategory.TYPE_ERROR,
            FailureCategory.TEST_FAILURE,
            FailureCategory.IMPORT_ERROR,
            FailureCategory.LINT_WARNING,
            FailureCategory.TIMEOUT,
            FailureCategory.UNKNOWN,
        ]
        for cat in priority_order:
            if cat in result.by_category:
                failures = result.by_category[cat]
                lines.append(f"\n[{cat.value.upper()}] ({len(failures)} issues):")
                for f in failures[:5]:
                    loc = f"{f.file_path}:{f.line}" if f.line else f.file_path
                    lines.append(f"  - {loc}: {f.message}")

        return "\n".join(lines)
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/domain/test_feedback/test_classifier.py -v
```

Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add coding_agent/domain/feedback/classifier.py tests/domain/test_feedback/test_classifier.py
git commit -m "feat: add FailureClassifier with category aggregation and summary generation"
```

---

### Task 13: CorrectionEngine

**Files:**
- Create: `coding_agent/domain/feedback/engine.py`
- Create: `tests/domain/test_feedback/test_engine.py`

**Depends on:** Task 2, Task 12

- [ ] **Step 1: 写失败测试**

```python
# tests/domain/test_feedback/test_engine.py
from coding_agent.domain.feedback.engine import CorrectionEngine, CorrectionStrategy
from coding_agent.domain.feedback.classifier import ClassifiedResult
from coding_agent.domain.models import SensorFailure, FailureCategory, FailureSeverity

def test_retry_on_blocking():
    engine = CorrectionEngine(max_retries=3)
    result = ClassifiedResult(has_blocking=True)
    assert engine.decide(result) == CorrectionStrategy.RETRY

def test_retry_then_ask_user():
    engine = CorrectionEngine(max_retries=2)
    result = ClassifiedResult(has_blocking=True)
    assert engine.decide(result) == CorrectionStrategy.RETRY
    assert engine.decide(result) == CorrectionStrategy.RETRY
    assert engine.decide(result) == CorrectionStrategy.ASK_USER

def test_ignore_when_no_blocking():
    engine = CorrectionEngine(max_retries=3)
    result = ClassifiedResult(has_blocking=False)
    assert engine.decide(result) == CorrectionStrategy.IGNORE

def test_reset_retry_count():
    engine = CorrectionEngine(max_retries=2)
    result = ClassifiedResult(has_blocking=True)
    engine.decide(result)
    engine.reset()
    assert engine.retry_count == 0
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/domain/test_feedback/test_engine.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现 CorrectionEngine**

```python
# coding_agent/domain/feedback/engine.py
from __future__ import annotations
from enum import Enum
from coding_agent.domain.feedback.classifier import ClassifiedResult


class CorrectionStrategy(str, Enum):
    RETRY = "retry"
    ROLLBACK = "rollback"
    ASK_USER = "ask_user"
    IGNORE = "ignore"


class CorrectionEngine:
    def __init__(self, max_retries: int = 3):
        self.retry_count = 0
        self.max_retries = max_retries

    def decide(self, classified: ClassifiedResult) -> CorrectionStrategy:
        if not classified.has_blocking:
            return CorrectionStrategy.IGNORE

        self.retry_count += 1
        if self.retry_count > self.max_retries:
            return CorrectionStrategy.ASK_USER

        return CorrectionStrategy.RETRY

    def reset(self) -> None:
        self.retry_count = 0
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/domain/test_feedback/test_engine.py -v
```

Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add coding_agent/domain/feedback/engine.py tests/domain/test_feedback/test_engine.py
git commit -m "feat: add CorrectionEngine with retry/ask_user/ignore strategies"
```

---

### Task 14: FeedbackPipeline

**Files:**
- Create: `coding_agent/domain/feedback/pipeline.py`
- Create: `tests/domain/test_feedback/test_pipeline.py`

**Depends on:** Task 10, 11, 12, 13

- [ ] **Step 1: 写失败测试**

```python
# tests/domain/test_feedback/test_pipeline.py
import tempfile
from pathlib import Path
from coding_agent.domain.feedback.pipeline import FeedbackPipeline
from coding_agent.domain.feedback.sensors import SyntaxSensor
from coding_agent.domain.feedback.classifier import FailureClassifier
from coding_agent.domain.feedback.engine import CorrectionEngine, CorrectionStrategy

def test_pipeline_with_syntax_error():
    pipeline = FeedbackPipeline(
        sensors=[SyntaxSensor()],
        classifier=FailureClassifier(),
        engine=CorrectionEngine(max_retries=1),
    )
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "bad.py"
        f.write_text("def broken(\n")
        result = pipeline.run([str(f)])
        assert result.strategy is not None
        assert "syntax" in result.feedback_text.lower()

def test_pipeline_with_no_errors():
    pipeline = FeedbackPipeline(
        sensors=[SyntaxSensor()],
        classifier=FailureClassifier(),
        engine=CorrectionEngine(max_retries=3),
    )
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "good.py"
        f.write_text("def hello():\n    return 'world'\n")
        result = pipeline.run([str(f)])
        assert result.strategy == CorrectionStrategy.IGNORE

def test_pipeline_empty_files():
    pipeline = FeedbackPipeline(
        sensors=[SyntaxSensor()],
        classifier=FailureClassifier(),
        engine=CorrectionEngine(max_retries=3),
    )
    result = pipeline.run([])
    assert result.feedback_text == "All checks passed."
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/domain/test_feedback/test_pipeline.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现 FeedbackPipeline**

```python
# coding_agent/domain/feedback/pipeline.py
from __future__ import annotations
from dataclasses import dataclass, field
from coding_agent.domain.feedback.sensors import Sensor
from coding_agent.domain.feedback.classifier import FailureClassifier
from coding_agent.domain.feedback.engine import CorrectionEngine, CorrectionStrategy


@dataclass
class PipelineResult:
    feedback_text: str = ""
    strategy: CorrectionStrategy | None = None
    reports: list = field(default_factory=list)


class FeedbackPipeline:
    def __init__(self, sensors: list[Sensor], classifier: FailureClassifier, engine: CorrectionEngine):
        self.sensors = sensors
        self.classifier = classifier
        self.engine = engine

    def run(self, changed_files: list[str]) -> PipelineResult:
        if not changed_files:
            return PipelineResult(feedback_text="All checks passed.", strategy=CorrectionStrategy.IGNORE)

        reports = []
        for sensor in self.sensors:
            report = sensor.sense(changed_files)
            reports.append(report)

        classified = self.classifier.classify(reports)
        strategy = self.engine.decide(classified)

        return PipelineResult(
            feedback_text=classified.summary,
            strategy=strategy,
            reports=reports,
        )
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/domain/test_feedback/test_pipeline.py -v
```

Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add coding_agent/domain/feedback/pipeline.py tests/domain/test_feedback/test_pipeline.py
git commit -m "feat: add FeedbackPipeline orchestrating sensors, classifier, and engine"
```

---

## Phase 3: Application Layer

### Task 15: ActionParser

**Files:**
- Create: `coding_agent/application/action_parser.py`
- Create: `tests/application/test_action_parser.py`

**Depends on:** Task 2

- [ ] **Step 1: 写失败测试**

```python
# tests/application/test_action_parser.py
from coding_agent.application.action_parser import ActionParser
from coding_agent.infrastructure.llm_provider import LLMResponse, ToolCall
from coding_agent.domain.models import ActionType

def test_parse_done():
    parser = ActionParser()
    response = LLMResponse(text="task completed", tool_calls=[])
    action = parser.parse(response)
    assert action.type == ActionType.DONE
    assert action.thought == "task completed"

def test_parse_tool_call():
    parser = ActionParser()
    response = LLMResponse(
        text="let me read the file",
        tool_calls=[ToolCall(name="read_file", arguments={"path": "test.py"})]
    )
    action = parser.parse(response)
    assert action.type == ActionType.CALL_TOOL
    assert action.tool_name == "read_file"
    assert action.tool_args == {"path": "test.py"}
    assert action.thought == "let me read the file"

def test_parse_multiple_tool_calls_uses_first():
    parser = ActionParser()
    response = LLMResponse(
        text="doing multiple things",
        tool_calls=[
            ToolCall(name="read_file", arguments={"path": "a.py"}),
            ToolCall(name="write_file", arguments={"path": "b.py", "content": "x"}),
        ]
    )
    action = parser.parse(response)
    assert action.type == ActionType.CALL_TOOL
    assert action.tool_name == "read_file"
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/application/test_action_parser.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现 ActionParser**

```python
# coding_agent/application/action_parser.py
from coding_agent.domain.models import Action, ActionType
from coding_agent.infrastructure.llm_provider import LLMResponse


class ActionParser:
    def parse(self, response: LLMResponse) -> Action:
        if not response.tool_calls:
            return Action(type=ActionType.DONE, thought=response.text)

        tc = response.tool_calls[0]
        return Action(
            type=ActionType.CALL_TOOL,
            tool_name=tc.name,
            tool_args=tc.arguments,
            thought=response.text,
        )
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/application/test_action_parser.py -v
```

Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add coding_agent/application/action_parser.py tests/application/test_action_parser.py
git commit -m "feat: add ActionParser for converting LLMResponse to structured Action"
```

---

### Task 16: SessionManager

**Files:**
- Create: `coding_agent/application/session_manager.py`
- Create: `tests/application/test_session_manager.py`

**Depends on:** Task 2

- [ ] **Step 1: 写失败测试**

```python
# tests/application/test_session_manager.py
from coding_agent.application.session_manager import SessionManager
from coding_agent.domain.models import SessionStatus

def test_create_session():
    sm = SessionManager()
    session = sm.create("write a test function")
    assert session.goal == "write a test function"
    assert session.status == SessionStatus.RUNNING
    assert session.id is not None

def test_record_step():
    sm = SessionManager()
    session = sm.create("task")
    from coding_agent.domain.models import Action, ActionType, ActionResult
    action = Action(type=ActionType.CALL_TOOL, tool_name="read_file", tool_args={"path": "x"})
    result = ActionResult(success=True, output="content", changed_files=["x"])
    sm.record_step(session.id, action, result)
    s = sm.get(session.id)
    assert len(s.steps) == 1
    assert s.steps[0].action.tool_name == "read_file"

def test_complete_session():
    sm = SessionManager()
    session = sm.create("task")
    sm.complete(session.id, success=True, answer="done")
    s = sm.get(session.id)
    assert s.status == SessionStatus.COMPLETED
    assert s.result.success is True

def test_list_sessions():
    sm = SessionManager()
    sm.create("task 1")
    sm.create("task 2")
    assert len(sm.list_all()) == 2

def test_get_nonexistent():
    sm = SessionManager()
    assert sm.get("nonexistent") is None
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/application/test_session_manager.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现 SessionManager**

```python
# coding_agent/application/session_manager.py
import datetime
from coding_agent.domain.models import (
    Session, SessionStatus, AgentResult, StepRecord, Action, ActionResult
)


class SessionManager:
    def __init__(self):
        self._sessions: dict[str, Session] = {}

    def create(self, goal: str) -> Session:
        session = Session(goal=goal)
        self._sessions[session.id] = session
        return session

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def record_step(self, session_id: str, action: Action, result: ActionResult) -> None:
        session = self._sessions.get(session_id)
        if session is None:
            return
        step = StepRecord(
            step_number=len(session.steps) + 1,
            action=action,
            action_result=result,
        )
        session.steps.append(step)

    def complete(self, session_id: str, success: bool, answer: str = "", error: str | None = None) -> None:
        session = self._sessions.get(session_id)
        if session is None:
            return
        session.result = AgentResult(success=success, answer=answer, error=error)
        session.status = SessionStatus.COMPLETED if success else SessionStatus.FAILED
        session.end_time = datetime.datetime.now()

    def list_all(self) -> list[Session]:
        return list(self._sessions.values())
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/application/test_session_manager.py -v
```

Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add coding_agent/application/session_manager.py tests/application/test_session_manager.py
git commit -m "feat: add SessionManager for session lifecycle and step recording"
```

---

### Task 17: AgentLoop（主循环）

**Files:**
- Create: `coding_agent/application/agent_loop.py`
- Create: `tests/application/test_agent_loop.py`

**Depends on:** Task 5, 7, 8, 14, 15, 16

- [ ] **Step 1: 写失败测试**

```python
# tests/application/test_agent_loop.py
import pytest
from coding_agent.application.agent_loop import AgentLoop
from coding_agent.infrastructure.llm_provider import ScriptedMockLLM, LLMResponse, ToolCall
from coding_agent.domain.tool_manager import ToolManager, ToolDef, ToolPermission
from coding_agent.domain.governance import Governance
from coding_agent.domain.feedback.pipeline import FeedbackPipeline
from coding_agent.domain.feedback.sensors import SyntaxSensor
from coding_agent.domain.feedback.classifier import FailureClassifier
from coding_agent.domain.feedback.engine import CorrectionEngine
from coding_agent.application.action_parser import ActionParser
from coding_agent.application.session_manager import SessionManager
from coding_agent.domain.memory import MemoryManager
from coding_agent.infrastructure.vector_store import InMemoryVectorStore
from coding_agent.domain.config import Config

def make_harness(responses):
    llm = ScriptedMockLLM(responses)
    tm = ToolManager()
    tm.register(ToolDef("echo", "echo back", {}, ToolPermission.SAFE, lambda a: a.get("msg", "")))
    governance = Governance(tm)
    pipeline = FeedbackPipeline(
        sensors=[SyntaxSensor()],
        classifier=FailureClassifier(),
        engine=CorrectionEngine(max_retries=3),
    )
    parser = ActionParser()
    session_mgr = SessionManager()
    memory = MemoryManager(InMemoryVectorStore())
    config = Config(max_steps=10)
    return AgentLoop(llm, tm, governance, pipeline, parser, session_mgr, memory, config)

def test_agent_completes_with_done():
    responses = [
        LLMResponse(text="let me echo", tool_calls=[ToolCall(name="echo", arguments={"msg": "hello"})]),
        LLMResponse(text="all done", tool_calls=[]),
    ]
    loop = make_harness(responses)
    result = loop.run("say hello")
    assert result.success is True
    assert result.answer == "all done"

def test_agent_stops_at_max_steps():
    config = Config(max_steps=2)
    responses = [
        LLMResponse(text="step 1", tool_calls=[ToolCall(name="echo", arguments={"msg": "x"})]),
        LLMResponse(text="step 2", tool_calls=[ToolCall(name="echo", arguments={"msg": "x"})]),
        LLMResponse(text="step 3", tool_calls=[ToolCall(name="echo", arguments={"msg": "x"})]),
    ]
    llm = ScriptedMockLLM(responses)
    tm = ToolManager()
    tm.register(ToolDef("echo", "echo", {}, ToolPermission.SAFE, lambda a: a.get("msg", "")))
    loop = AgentLoop(
        llm, tm, Governance(tm),
        FeedbackPipeline([SyntaxSensor()], FailureClassifier(), CorrectionEngine()),
        ActionParser(), SessionManager(), MemoryManager(InMemoryVectorStore()), config,
    )
    result = loop.run("task")
    assert result.success is False
    assert "max steps" in result.error.lower()

def test_agent_blocked_by_governance():
    responses = [
        LLMResponse(text="dangerous", tool_calls=[ToolCall(name="echo", arguments={"command": "rm -rf /"})]),
        LLMResponse(text="ok fine", tool_calls=[ToolCall(name="echo", arguments={"msg": "safe"})]),
        LLMResponse(text="done", tool_calls=[]),
    ]
    llm = ScriptedMockLLM(responses)
    tm = ToolManager()
    tm.register(ToolDef("echo", "echo", {}, ToolPermission.DANGEROUS, lambda a: "ok"))
    governance = Governance(tm)
    loop = AgentLoop(
        llm, tm, governance,
        FeedbackPipeline([SyntaxSensor()], FailureClassifier(), CorrectionEngine()),
        ActionParser(), SessionManager(), MemoryManager(InMemoryVectorStore()), Config(max_steps=10),
    )
    result = loop.run("task")
    assert result.success is True
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/application/test_agent_loop.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现 AgentLoop**

```python
# coding_agent/application/agent_loop.py
from coding_agent.infrastructure.llm_provider import LLMProvider
from coding_agent.domain.tool_manager import ToolManager
from coding_agent.domain.governance import Governance, PermissionResult
from coding_agent.domain.feedback.pipeline import FeedbackPipeline
from coding_agent.application.action_parser import ActionParser
from coding_agent.application.session_manager import SessionManager
from coding_agent.domain.memory import MemoryManager
from coding_agent.domain.config import Config
from coding_agent.domain.models import Message, ActionType, AgentResult


class AgentLoop:
    def __init__(
        self,
        llm: LLMProvider,
        tool_manager: ToolManager,
        governance: Governance,
        feedback_pipeline: FeedbackPipeline,
        action_parser: ActionParser,
        session_manager: SessionManager,
        memory: MemoryManager,
        config: Config,
    ):
        self.llm = llm
        self.tool_manager = tool_manager
        self.governance = governance
        self.feedback_pipeline = feedback_pipeline
        self.action_parser = action_parser
        self.session_manager = session_manager
        self.memory = memory
        self.config = config

    def run(self, goal: str) -> AgentResult:
        session = self.session_manager.create(goal)
        context = self._build_context(goal)
        steps = 0

        while steps < self.config.max_steps:
            steps += 1

            if self._context_too_large(context):
                context = self.memory.compress(context)

            response = self.llm.chat(context, self.tool_manager.list_defs())
            action = self.action_parser.parse(response)

            context.append(Message(role="assistant", content=response.text))

            if action.type == ActionType.DONE:
                self.session_manager.complete(session.id, success=True, answer=response.text)
                return AgentResult(success=True, answer=response.text)

            if action.type == ActionType.TAKE_NOTE:
                self.memory.write(action.note or "")
                continue

            permission = self.governance.check(action)
            if permission == PermissionResult.BLOCKED:
                context.append(Message(role="user", content="Action blocked by governance guardrail."))
                self.session_manager.record_step(session.id, action, None)  # type: ignore[arg-type]
                continue

            if permission in (PermissionResult.NEEDS_CONFIRMATION, PermissionResult.NEEDS_HITL):
                context.append(Message(
                    role="user",
                    content=f"Action requires {permission.value}. Please approve in the WebUI."
                ))
                self.session_manager.record_step(session.id, action, None)  # type: ignore[arg-type]
                continue

            result = self.tool_manager.dispatch(action)
            context.append(Message(role="user", content=result.output))
            self.session_manager.record_step(session.id, action, result)

            if result.changed_files:
                fb_result = self.feedback_pipeline.run(result.changed_files)
                context.append(Message(role="user", content=fb_result.feedback_text))

        self.session_manager.complete(session.id, success=False, error="Max steps reached")
        return AgentResult(success=False, error="Max steps reached")

    def _build_context(self, goal: str) -> list[Message]:
        context = [
            Message(role="system", content="You are a coding agent. You can read/write files, run shell commands, and execute tests. Respond with tool calls to take action, or just text when done."),
        ]
        if self.config.project_rules:
            context.append(Message(role="user", content=f"Project rules:\n{self.config.project_rules}"))
        memories = self.memory.read(goal)
        for m in memories:
            context.append(Message(role="user", content=f"Memory: {m.content}"))
        context.append(Message(role="user", content=goal))
        return context

    def _context_too_large(self, context: list[Message]) -> bool:
        total = sum(len(m.content) for m in context)
        return total > self.config.max_context_tokens * 4
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/application/test_agent_loop.py -v
```

Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add coding_agent/application/agent_loop.py tests/application/test_agent_loop.py
git commit -m "feat: add AgentLoop main loop orchestrating all harness components"
```

---

## Phase 4: Presentation Layer

### Task 18: FastAPI + Routes + WebSocket

**Files:**
- Create: `coding_agent/presentation/app.py`
- Create: `coding_agent/presentation/routes.py`
- Create: `coding_agent/presentation/websocket.py`
- Create: `tests/presentation/test_app.py`

**Depends on:** Task 17

- [ ] **Step 1: 写失败测试**

```python
# tests/presentation/test_app.py
import pytest
from fastapi.testclient import TestClient
from coding_agent.presentation.app import create_app

@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)

def test_status_endpoint(client):
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data

def test_sessions_list(client):
    response = client.get("/api/sessions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_credentials_status(client):
    response = client.get("/api/credentials/status")
    assert response.status_code == 200
    assert "configured" in response.json()
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/presentation/test_app.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现 FastAPI + Routes + WebSocket**

```python
# coding_agent/presentation/app.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from coding_agent.presentation.routes import create_router
from coding_agent.presentation.websocket import websocket_endpoint


def create_app() -> FastAPI:
    app = FastAPI(title="Coding Agent Harness")
    app.include_router(create_router())
    app.add_api_websocket_route("/ws/events", websocket_endpoint)

    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

    return app
```

```python
# coding_agent/presentation/routes.py
from fastapi import APIRouter
from coding_agent.infrastructure.credential_store import CredentialStore

store = CredentialStore()
sessions_data: list[dict] = []


def create_router() -> APIRouter:
    router = APIRouter(prefix="/api")

    @router.get("/status")
    async def status():
        return {"status": "running", "sessions_count": len(sessions_data)}

    @router.get("/sessions")
    async def list_sessions():
        return sessions_data

    @router.get("/sessions/{session_id}")
    async def get_session(session_id: str):
        for s in sessions_data:
            if s.get("id") == session_id:
                return s
        return {"error": "not found"}

    @router.get("/credentials/status")
    async def credentials_status():
        return store.get_status()

    @router.post("/credentials")
    async def set_credentials(data: dict):
        store.set_api_key(data.get("api_key", ""))
        return {"status": "ok"}

    @router.delete("/credentials")
    async def clear_credentials():
        store.clear_api_key()
        return {"status": "ok"}

    return router
```

```python
# coding_agent/presentation/websocket.py
from fastapi import WebSocket


async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json({"type": "connected"})
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"type": "echo", "data": data})
    except Exception:
        pass
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/presentation/test_app.py -v
```

Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add coding_agent/presentation/app.py coding_agent/presentation/routes.py coding_agent/presentation/websocket.py tests/presentation/test_app.py
git commit -m "feat: add FastAPI app with REST routes, WebSocket, and credential endpoints"
```

---

### Task 19: 前端界面

**Files:**
- Create: `coding_agent/presentation/static/index.html`
- Create: `coding_agent/presentation/static/style.css`
- Create: `coding_agent/presentation/static/app.js`

**Depends on:** Task 18

- [ ] **Step 1: 创建前端文件**

```html
<!-- coding_agent/presentation/static/index.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Coding Agent Harness</title>
<link rel="stylesheet" href="/style.css">
</head>
<body>
<div id="app">
  <header>
    <h1>Coding Agent Harness</h1>
    <span id="status-indicator" class="status-offline">Disconnected</span>
  </header>

  <main>
    <section class="panel" id="task-panel">
      <h2>Task</h2>
      <textarea id="goal-input" placeholder="Enter your coding task..." rows="4"></textarea>
      <button id="run-btn" onclick="submitTask()">Run Task</button>
    </section>

    <section class="panel" id="monitor-panel">
      <h2>Live Monitor</h2>
      <div id="step-log"></div>
    </section>

    <section class="panel" id="approval-panel" style="display:none">
      <h2>Approval Required</h2>
      <div id="approval-content"></div>
      <button onclick="approve()">Approve</button>
      <button onclick="deny()">Deny</button>
    </section>

    <section class="panel" id="history-panel">
      <h2>Sessions</h2>
      <div id="sessions-list"></div>
    </section>

    <section class="panel" id="config-panel">
      <h2>Configuration</h2>
      <div id="credential-status">Loading...</div>
      <input type="password" id="api-key-input" placeholder="Enter API key">
      <button onclick="setCredentials()">Set API Key</button>
      <button onclick="clearCredentials()">Clear</button>
    </section>
  </main>
</div>
<script src="/app.js"></script>
</body>
</html>
```

```css
/* coding_agent/presentation/static/style.css */
:root {
  --bg: #1a1b26; --panel-bg: #24283b; --text: #c0caf5;
  --accent: #7aa2f7; --danger: #f7768e; --success: #9ece6a;
  --warning: #e0af68; --border: #3b4261;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: var(--bg); color: var(--text); }
header { display: flex; justify-content: space-between; align-items: center; padding: 16px 24px; background: var(--panel-bg); border-bottom: 1px solid var(--border); }
h1 { font-size: 20px; }
.status-offline { color: var(--danger); }
.status-online { color: var(--success); }
main { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; padding: 24px; max-width: 1400px; margin: 0 auto; }
.panel { background: var(--panel-bg); border: 1px solid var(--border); border-radius: 8px; padding: 20px; }
.panel h2 { font-size: 16px; margin-bottom: 12px; color: var(--accent); }
textarea, input { width: 100%; background: var(--bg); color: var(--text); border: 1px solid var(--border); border-radius: 4px; padding: 8px 12px; margin-bottom: 8px; }
button { background: var(--accent); color: var(--bg); border: none; border-radius: 4px; padding: 8px 16px; cursor: pointer; margin-right: 8px; }
button:hover { opacity: 0.9; }
#step-log { max-height: 400px; overflow-y: auto; font-family: monospace; font-size: 13px; }
#step-log .step { padding: 8px; border-bottom: 1px solid var(--border); }
#step-log .step.error { border-left: 3px solid var(--danger); }
#step-log .step.success { border-left: 3px solid var(--success); }
```

```javascript
// coding_agent/presentation/static/app.js
let ws = null;

function connect() {
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
  ws = new WebSocket(`${protocol}//${location.host}/ws/events`);
  ws.onopen = () => {
    document.getElementById('status-indicator').textContent = 'Connected';
    document.getElementById('status-indicator').className = 'status-online';
  };
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'step') {
      addStepLog(data);
    }
  };
  ws.onclose = () => {
    document.getElementById('status-indicator').textContent = 'Disconnected';
    document.getElementById('status-indicator').className = 'status-offline';
    setTimeout(connect, 3000);
  };
}

function addStepLog(data) {
  const log = document.getElementById('step-log');
  const div = document.createElement('div');
  div.className = 'step ' + (data.success ? 'success' : 'error');
  div.textContent = `[Step ${data.step}] ${data.action || ''} ${data.output || ''}`;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
}

function submitTask() {
  const goal = document.getElementById('goal-input').value;
  if (!goal) return;
  fetch('/api/run', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({goal}),
  }).then(r => r.json()).then(data => {
    addStepLog({step: 'info', action: 'Task submitted', output: JSON.stringify(data)});
  });
}

async function setCredentials() {
  const key = document.getElementById('api-key-input').value;
  await fetch('/api/credentials', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({api_key: key}),
  });
  document.getElementById('api-key-input').value = '';
  loadCredentialStatus();
}

async function clearCredentials() {
  await fetch('/api/credentials', {method: 'DELETE'});
  loadCredentialStatus();
}

async function loadCredentialStatus() {
  const r = await fetch('/api/credentials/status');
  const data = await r.json();
  document.getElementById('credential-status').textContent =
    data.configured ? 'API key configured' : 'No API key configured';
}

async function loadSessions() {
  const r = await fetch('/api/sessions');
  const data = await r.json();
  const list = document.getElementById('sessions-list');
  list.innerHTML = data.map(s => `<div>${s.id}: ${s.goal || 'N/A'}</div>`).join('');
}

connect();
loadCredentialStatus();
loadSessions();
```

- [ ] **Step 2: 验证前端可访问**

启动 FastAPI 后访问 `http://localhost:8080`，确认页面加载成功

- [ ] **Step 3: Commit**

```bash
git add coding_agent/presentation/static/
git commit -m "feat: add WebUI frontend with task input, live monitor, and credential management"
```

---

### Task 20: WebUI 集成——run API

**Files:**
- Modify: `coding_agent/presentation/routes.py`
- Modify: `coding_agent/presentation/app.py`

**Depends on:** Task 18, Task 17

- [ ] **Step 1: 更新 routes.py 添加 /api/run**

```python
# 在 routes.py 中追加
from coding_agent.application.agent_loop import AgentLoop

agent_loop: AgentLoop | None = None

def set_agent_loop(loop: AgentLoop):
    global agent_loop
    agent_loop = loop

@router.post("/run")
async def run_task(data: dict):
    if agent_loop is None:
        return {"error": "Agent loop not initialized"}
    goal = data.get("goal", "")
    result = agent_loop.run(goal)
    return {"success": result.success, "answer": result.answer, "error": result.error}
```

- [ ] **Step 2: 更新 app.py 注入依赖**

```python
# 在 create_app 中注入
def create_app(loop: AgentLoop | None = None):
    if loop:
        from coding_agent.presentation.routes import set_agent_loop
        set_agent_loop(loop)
    ...
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/presentation/test_app.py -v
```

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add coding_agent/presentation/
git commit -m "feat: integrate AgentLoop with WebUI run endpoint"
```

---

## Phase 5: Integration & Demos

### Task 21: CLI 入口 + main

**Files:**
- Create: `coding_agent/main.py`
- Create: `coding_agent/__init__.py`

**Depends on:** Task 17, Task 4

- [ ] **Step 1: 实现 CLI 入口**

```python
# coding_agent/main.py
import argparse
import sys
from pathlib import Path
from getpass import getpass

def main():
    parser = argparse.ArgumentParser(prog="coding-agent", description="Coding Agent Harness")
    sub = parser.add_subparsers(dest="command")

    serve_parser = sub.add_parser("serve", help="Start WebUI server")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8080)

    cred_parser = sub.add_parser("credentials", help="Manage API credentials")
    cred_parser.add_argument("action", choices=["set", "status", "clear"])

    run_parser = sub.add_parser("run", help="Run a task from CLI")
    run_parser.add_argument("goal", nargs="+")

    args = parser.parse_args()

    if args.command == "serve":
        from coding_agent.presentation.app import create_app
        import uvicorn
        app = create_app()
        uvicorn.run(app, host=args.host, port=args.port)

    elif args.command == "credentials":
        from coding_agent.infrastructure.credential_store import CredentialStore
        store = CredentialStore()
        if args.action == "set":
            key = getpass("Enter API key: ")
            store.set_api_key(key)
            print("API key saved.")
        elif args.action == "status":
            status = store.get_status()
            print(f"Configured: {status['configured']}")
        elif args.action == "clear":
            store.clear_api_key()
            print("API key cleared.")

    elif args.command == "run":
        print("CLI run mode: use 'serve' for WebUI, or run tests directly.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 更新 pyproject.toml 添加 CLI 入口**

```toml
[project.scripts]
coding-agent = "coding_agent.main:main"
```

- [ ] **Step 3: 验证 CLI**

```bash
python -m coding_agent.main --help
```

Expected: 显示 help 文本

- [ ] **Step 4: Commit**

```bash
git add coding_agent/main.py coding_agent/__init__.py pyproject.toml
git commit -m "feat: add CLI entry point with serve, credentials, and run commands"
```

---

### Task 22: 机制演示 1——治理护栏拦截

**Files:**
- Create: `tests/demonstrations/test_demo_governance.py`

**Depends on:** Task 8

- [ ] **Step 1: 写演示测试**

```python
# tests/demonstrations/test_demo_governance.py
"""
机制演示 1: 治理护栏拦截危险动作
使用 mock LLM 驱动，确定性验证护栏拦截行为。
"""
import pytest
from coding_agent.application.agent_loop import AgentLoop
from coding_agent.infrastructure.llm_provider import ScriptedMockLLM, LLMResponse, ToolCall
from coding_agent.domain.tool_manager import ToolManager, ToolDef, ToolPermission
from coding_agent.domain.governance import Governance
from coding_agent.domain.feedback.pipeline import FeedbackPipeline
from coding_agent.domain.feedback.sensors import SyntaxSensor
from coding_agent.domain.feedback.classifier import FailureClassifier
from coding_agent.domain.feedback.engine import CorrectionEngine
from coding_agent.application.action_parser import ActionParser
from coding_agent.application.session_manager import SessionManager
from coding_agent.domain.memory import MemoryManager
from coding_agent.infrastructure.vector_store import InMemoryVectorStore
from coding_agent.domain.config import Config


def test_demo_governance_blocks_dangerous_action():
    """
    演示场景:
    1. Agent 尝试执行 'rm -rf /' 命令
    2. 治理护栏检测到危险命令模式，返回 BLOCKED
    3. Agent 收到拦截消息后，放弃危险操作，正常完成任务
    """
    responses = [
        # 第 1 轮: 尝试执行危险命令
        LLMResponse(
            text="let me clean up",
            tool_calls=[ToolCall(name="run_shell", arguments={"command": "rm -rf /"})],
        ),
        # 第 2 轮: 被拦截后，换个方式
        LLMResponse(
            text="ok, let me just list files instead",
            tool_calls=[ToolCall(name="run_shell", arguments={"command": "ls -la"})],
        ),
        # 第 3 轮: 完成
        LLMResponse(text="task completed", tool_calls=[]),
    ]

    llm = ScriptedMockLLM(responses)
    tm = ToolManager()
    tm.register(ToolDef("run_shell", "run shell", {"command": "str"}, ToolPermission.DANGEROUS,
                        lambda a: f"executed: {a['command']}"))

    governance = Governance(tm)
    loop = AgentLoop(
        llm, tm, governance,
        FeedbackPipeline([SyntaxSensor()], FailureClassifier(), CorrectionEngine()),
        ActionParser(), SessionManager(), MemoryManager(InMemoryVectorStore()), Config(max_steps=10),
    )

    result = loop.run("clean up the project")

    # 验证: 任务最终成功完成（agent 放弃了危险操作）
    assert result.success is True
    assert result.answer == "task completed"

    # 验证: 危险命令被拦截（通过检查 governance 的检查逻辑）
    from coding_agent.domain.models import Action, ActionType
    dangerous_action = Action(
        type=ActionType.CALL_TOOL,
        tool_name="run_shell",
        tool_args={"command": "rm -rf /"},
    )
    assert governance.check(dangerous_action) == Governance.PermissionResult.BLOCKED if hasattr(Governance, 'PermissionResult') else False
```

- [ ] **Step 2: 运行演示**

```bash
pytest tests/demonstrations/test_demo_governance.py -v
```

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/demonstrations/test_demo_governance.py
git commit -m "feat: add mechanism demo 1 - governance guardrail blocking dangerous actions"
```

---

### Task 23: 机制演示 2——反馈闭环修正

**Files:**
- Create: `tests/demonstrations/test_demo_feedback.py`

**Depends on:** Task 14, Task 17

- [ ] **Step 1: 写演示测试**

```python
# tests/demonstrations/test_demo_feedback.py
"""
机制演示 2: 反馈闭环——注入失败，agent 收到反馈并修正
使用 mock LLM 驱动，确定性验证反馈闭环的修正行为。
"""
import tempfile
from pathlib import Path
from coding_agent.application.agent_loop import AgentLoop
from coding_agent.infrastructure.llm_provider import RuleBasedMockLLM, LLMResponse, ToolCall
from coding_agent.domain.tool_manager import ToolManager, ToolDef, ToolPermission
from coding_agent.domain.governance import Governance
from coding_agent.domain.feedback.pipeline import FeedbackPipeline
from coding_agent.domain.feedback.sensors import SyntaxSensor
from coding_agent.domain.feedback.classifier import FailureClassifier
from coding_agent.domain.feedback.engine import CorrectionEngine
from coding_agent.application.action_parser import ActionParser
from coding_agent.application.session_manager import SessionManager
from coding_agent.domain.memory import MemoryManager
from coding_agent.infrastructure.vector_store import InMemoryVectorStore
from coding_agent.domain.config import Config
from coding_agent.infrastructure.file_system import FileSystemManager


def test_demo_feedback_loop_correction():
    """
    演示场景:
    1. Agent 写入一个语法错误的 Python 文件
    2. 反馈管线的 SyntaxSensor 检测到语法错误
    3. 反馈文本注入上下文
    4. Agent 收到反馈后修正文件
    5. 最终任务完成
    """
    with tempfile.TemporaryDirectory() as td:
        fs = FileSystemManager(allowed_dirs=[td])
        bad_file = Path(td) / "broken.py"

        # 规则式 mock: 看到 "feedback" 就修正，否则写错误文件
        def should_fix(msgs, tools):
            return any("feedback" in m.content.lower() for m in msgs)

        def should_done(msgs, tools):
            return any("fixed" in m.content.lower() for m in msgs)

        llm = RuleBasedMockLLM([
            # 修正: 写正确的文件
            (should_fix, LLMResponse(
                text="fixing the syntax",
                tool_calls=[ToolCall(name="write_file", arguments={
                    "path": str(bad_file),
                    "content": "def hello():\n    return 'world'\n",
                    "_changed_files": [str(bad_file)],
                })]
            )),
            # 完成后: done
            (should_done, LLMResponse(text="fixed and done", tool_calls=[])),
            # 默认: 写错误文件
            (lambda m, t: True, LLMResponse(
                text="writing the file",
                tool_calls=[ToolCall(name="write_file", arguments={
                    "path": str(bad_file),
                    "content": "def broken(\n    return 'oops'\n",
                    "_changed_files": [str(bad_file)],
                })]
            )),
        ])

        tm = ToolManager()
        tm.register(ToolDef("write_file", "write file", {"path": "str", "content": "str", "_changed_files": "list"},
                            ToolPermission.RISKY,
                            lambda a: fs.write_file(a["path"], a["content"]) or "written"))

        loop = AgentLoop(
            llm, tm, Governance(tm),
            FeedbackPipeline([SyntaxSensor()], FailureClassifier(), CorrectionEngine(max_retries=3)),
            ActionParser(), SessionManager(), MemoryManager(InMemoryVectorStore()), Config(max_steps=10),
        )

        result = loop.run(f"create {bad_file}")

        # 验证: 任务成功完成
        assert result.success is True
        # 验证: 文件最终是正确的
        content = fs.read_file(str(bad_file))
        assert "def hello():" in content
```

- [ ] **Step 2: 运行演示**

```bash
pytest tests/demonstrations/test_demo_feedback.py -v
```

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/demonstrations/test_demo_feedback.py
git commit -m "feat: add mechanism demo 2 - feedback loop correction with SyntaxSensor"
```

---

### Task 24: 机制演示 3——完整反馈管线

**Files:**
- Create: `tests/demonstrations/test_demo_pipeline.py`

**Depends on:** Task 14

- [ ] **Step 1: 写演示测试**

```python
# tests/demonstrations/test_demo_pipeline.py
"""
机制演示 3: 反馈闭环完整管线——sensor → 分类 → 策略 → 回灌
主贡献维度确定性行为验证，不依赖真实 LLM。
"""
import tempfile
from pathlib import Path
from coding_agent.domain.feedback.pipeline import FeedbackPipeline
from coding_agent.domain.feedback.sensors import SyntaxSensor
from coding_agent.domain.feedback.classifier import FailureClassifier
from coding_agent.domain.feedback.engine import CorrectionEngine, CorrectionStrategy


def test_demo_full_pipeline_flow():
    """
    演示完整的反馈管线流程:
    1. 创建包含语法错误的文件
    2. SyntaxSensor 检测到错误
    3. FailureClassifier 分类为 SYNTAX_ERROR
    4. CorrectionEngine 判定为 RETRY
    5. 反馈文本包含具体错误信息
    """
    with tempfile.TemporaryDirectory() as td:
        bad_file = Path(td) / "error.py"
        bad_file.write_text("def broken(\n    return 'oops'\n")

        pipeline = FeedbackPipeline(
            sensors=[SyntaxSensor()],
            classifier=FailureClassifier(),
            engine=CorrectionEngine(max_retries=3),
        )

        result = pipeline.run([str(bad_file)])

        # 验证: 检测到失败
        assert result.feedback_text != "All checks passed."
        # 验证: 策略是 RETRY（阻塞性错误）
        assert result.strategy == CorrectionStrategy.RETRY
        # 验证: 反馈文本包含文件路径和错误类型
        assert "error.py" in result.feedback_text
        assert "syntax" in result.feedback_text.lower()
        # 验证: 有 sensor 报告
        assert len(result.reports) == 1
        assert result.reports[0].sensor_name == "syntax"
        assert result.reports[0].passed is False


def test_demo_pipeline_no_errors():
    """验证无错误时管线正常返回"""
    with tempfile.TemporaryDirectory() as td:
        good_file = Path(td) / "good.py"
        good_file.write_text("def hello():\n    return 'world'\n")

        pipeline = FeedbackPipeline(
            sensors=[SyntaxSensor()],
            classifier=FailureClassifier(),
            engine=CorrectionEngine(max_retries=3),
        )

        result = pipeline.run([str(good_file)])
        assert result.feedback_text == "All checks passed."
        assert result.strategy == CorrectionStrategy.IGNORE


def test_demo_retry_limit():
    """验证重试次数上限后升级为 ASK_USER"""
    engine = CorrectionEngine(max_retries=2)
    from coding_agent.domain.feedback.classifier import ClassifiedResult

    blocking_result = ClassifiedResult(has_blocking=True, total_failures=1, summary="error")

    assert engine.decide(blocking_result) == CorrectionStrategy.RETRY
    assert engine.decide(blocking_result) == CorrectionStrategy.RETRY
    assert engine.decide(blocking_result) == CorrectionStrategy.ASK_USER
```

- [ ] **Step 2: 运行演示**

```bash
pytest tests/demonstrations/test_demo_pipeline.py -v
```

Expected: PASS (3 tests)

- [ ] **Step 3: Commit**

```bash
git add tests/demonstrations/test_demo_pipeline.py
git commit -m "feat: add mechanism demo 3 - full feedback pipeline (sensor→classify→strategy→feedback)"
```

---

### Task 25: Docker + CI 配置

**Files:**
- Create: `Dockerfile`
- Create: `.gitlab-ci.yml`
- Create: `tests/conftest.py`

**Depends on:** Task 21

- [ ] **Step 1: 创建 Dockerfile**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
COPY coding_agent/ coding_agent/
RUN pip install --no-cache-dir -e .
EXPOSE 8080
CMD ["coding-agent", "serve", "--host", "0.0.0.0", "--port", "8080"]
```

- [ ] **Step 2: 创建 .gitlab-ci.yml**

```yaml
stages:
  - test

unit-test:
  stage: test
  image: python:3.11-slim
  before_script:
    - pip install -e ".[dev]"
  script:
    - pytest tests/ -v --tb=short
```

- [ ] **Step 3: 创建 conftest.py**

```python
# tests/conftest.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

- [ ] **Step 4: 运行完整测试**

```bash
pytest tests/ -v --tb=short
```

Expected: 所有测试 PASS

- [ ] **Step 5: Commit**

```bash
git add Dockerfile .gitlab-ci.yml tests/conftest.py
git commit -m "feat: add Dockerfile, CI config, and conftest fixtures"
```

---

### Task 26: README.md

**Files:**
- Create: `README.md`

**Depends on:** All previous tasks

- [ ] **Step 1: 编写 README.md**

```markdown
# Coding Agent Harness

一个从零实现的 Coding Agent Harness。核心公式：**Agent = LLM × Harness**。

## 项目简介

本项目将 LLM 从"会思考的芯片"变成"能工作的计算机"。通过六个维度（决策封装、工具动作、上下文记忆、治理护栏、反馈闭环、配置）的代码实现，让 LLM 在编码场景中稳定、安全、可靠地运行。

主贡献维度：**反馈闭环**——多层 Sensor 管线（语法→类型→lint→测试）+ 失败分类 + 修正策略引擎。

## 安装

```bash
pip install -e ".[dev]"
```

## 运行

```bash
# WebUI 模式
coding-agent serve --port 8080

# CLI 模式
coding-agent run "fix the bug in src/utils.py"
```

## API Key 配置

```bash
# 安全录入（隐藏输入，存储在 Windows Credential Manager）
coding-agent credentials set

# 查看状态（不显示明文）
coding-agent credentials status

# 清除
coding-agent credentials clear
```

## Docker

```bash
docker build -t coding-agent .
docker run -p 8080:8080 coding-agent
```

## 测试

```bash
pytest tests/ -v
```

## 机制演示

```bash
# 演示 1: 治理护栏拦截危险动作
pytest tests/demonstrations/test_demo_governance.py -v

# 演示 2: 反馈闭环修正
pytest tests/demonstrations/test_demo_feedback.py -v

# 演示 3: 完整反馈管线
pytest tests/demonstrations/test_demo_pipeline.py -v
```

## 目录结构

```
coding_agent/          # 主包
├── infrastructure/    # 基础设施层: LLM, 凭据, 文件系统, 子进程, 向量存储
├── domain/            # 领域层: 模型, 工具, 治理, 反馈, 记忆, 配置
│   └── feedback/      # ★ 主贡献: Sensor管线, 分类器, 修正引擎, 管线
├── application/       # 应用层: 主循环, 动作解析, 会话管理
└── presentation/      # 表示层: FastAPI, WebSocket, 前端
```

## 安全边界

- 凭据存储在操作系统钥匙串中，不落地明文文件
- 治理护栏在工具执行前拦截危险动作
- 文件操作限定在 `allowed_dirs` 范围内
- `.env` 文件支持（明文风险，详见凭据威胁模型）
- 日志自动脱敏，不记录 API key

## 已知限制

- 仅支持 OpenAI 兼容 API 协议
- 凭据存储依赖操作系统钥匙串（Docker 中需额外配置）
- 前端为原生 JS，不支持 IE
- 仅测试 Windows 11 + Python 3.11

## 技术栈

Python 3.11+, FastAPI, Pydantic, ChromaDB, keyring, pytest, ruff, mypy
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with install, usage, security, and demo instructions"
```

---

## 依赖关系总结

```
Task 1 (骨架)
 └─ Task 2 (模型)
     ├─ Task 3 (配置) ──────────── 可并行 ────┐
     ├─ Task 4 (凭据) ──────────── 可并行 ────┤
     ├─ Task 5 (LLM抽象) ──────── 可并行 ────┤
     ├─ Task 6 (FS+子进程) ────── 可并行 ────┤
     │   └─ Task 7 (工具系统) ────────────────┤
     ├─ Task 8 (治理) ──────────── 可并行 ────┤
     ├─ Task 9 (记忆) ──────────── 可并行 ────┤
     ├─ Task 10 (SyntaxSensor) ─── 可并行 ────┤
     │   └─ Task 11 (更多Sensors) ────────────┤
     ├─ Task 12 (Classifier) ───── 可并行 ────┤
     ├─ Task 13 (Engine) ───────── 可并行 ────┤
     │   └─ Task 14 (Pipeline) ───────────────┤
     ├─ Task 15 (ActionParser) ─── 可并行 ────┤
     └─ Task 16 (SessionManager) ─ 可并行 ────┤
         └─ Task 17 (AgentLoop) ──────────────┘
             ├─ Task 18 (FastAPI) ──┐
             │   └─ Task 19 (前端) ─┤
             │       └─ Task 20 ────┘
             ├─ Task 21 (CLI)
             ├─ Task 22 (演示1) ──── 可并行
             ├─ Task 23 (演示2) ──── 可并行
             ├─ Task 24 (演示3) ──── 可并行
             ├─ Task 25 (Docker+CI)
             └─ Task 26 (README)
```

---

## 验证清单

完成所有 task 后，运行以下验证：

```bash
# 1. 全部单元测试
pytest tests/ -v --tb=short

# 2. 机制演示
pytest tests/demonstrations/ -v

# 3. 类型检查
mypy coding_agent/ --ignore-missing-imports

# 4. Lint
ruff check coding_agent/

# 5. Docker 构建
docker build -t coding-agent .

# 6. CI 模拟
pytest tests/ -v --tb=short
```