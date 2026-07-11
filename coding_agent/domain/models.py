from __future__ import annotations
import datetime
import uuid
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class ActionType(str, Enum):
    CALL_TOOL = "call_tool"
    DONE = "done"
    TAKE_NOTE = "take_note"


class Action(BaseModel):
    type: ActionType
    tool_name: str | None = None
    tool_args: dict[str, Any] | None = None
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
    tool_calls: list[Any] | None = None


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
    llm_response: Any | None = None
    governance_result: Any | None = None
    feedback_report: Any | None = None
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
