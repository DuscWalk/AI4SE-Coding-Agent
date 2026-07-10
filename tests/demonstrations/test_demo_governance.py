# tests/demonstrations/test_demo_governance.py
"""
机制演示 1: 治理护栏拦截危险动作
使用 mock LLM 驱动，确定性验证护栏拦截行为。
"""
from __future__ import annotations

import tempfile
from coding_agent.application.agent_loop import AgentLoop
from coding_agent.infrastructure.llm_provider import ScriptedMockLLM, LLMResponse, ToolCall
from coding_agent.domain.tool_manager import ToolManager, ToolDef, ToolPermission
from coding_agent.domain.governance import Governance, Permission
from coding_agent.domain.feedback.pipeline import FeedbackPipeline
from coding_agent.domain.feedback.sensors import SyntaxSensor
from coding_agent.domain.feedback.classifier import FailureClassifier
from coding_agent.domain.feedback.engine import CorrectionEngine
from coding_agent.application.action_parser import ActionParser
from coding_agent.application.session_manager import SessionManager
from coding_agent.domain.memory import MemoryManager
from coding_agent.infrastructure.vector_store import InMemoryVectorStore
from coding_agent.domain.config import Config
from coding_agent.domain.models import Action, ActionType


def test_demo_governance_blocks_dangerous_action():
    """
    演示场景:
    1. Agent 尝试执行 'rm -rf /' 命令
    2. 治理护栏检测到危险命令模式，返回 BLOCKED
    3. Agent 收到拦截消息后，放弃危险操作，改用安全命令
    4. Agent 正常完成任务
    """
    responses = [
        # 第 1 轮: 尝试执行危险命令
        LLMResponse(
            text="let me clean up",
            tool_calls=[ToolCall(name="run_shell", arguments={"command": "rm -rf /"})],
        ),
        # 第 2 轮: 被拦截后，换个安全方式
        LLMResponse(
            text="ok, let me just list files instead",
            tool_calls=[ToolCall(name="run_shell", arguments={"command": "ls -la"})],
        ),
        # 第 3 轮: 完成
        LLMResponse(text="task completed", tool_calls=[]),
    ]

    llm = ScriptedMockLLM(responses)
    tm = ToolManager()
    tm.register(ToolDef(
        name="run_shell",
        description="run a shell command",
        parameters={"command": "str"},
        permission=ToolPermission.DANGEROUS,
        handler=lambda a: f"executed: {a['command']}",
    ))

    governance = Governance()
    pipeline = FeedbackPipeline(
        sensors=[SyntaxSensor()],
        classifier=FailureClassifier(),
        engine=CorrectionEngine(max_retries=3),
    )
    parser = ActionParser()
    memory = MemoryManager(InMemoryVectorStore())
    config = Config(max_steps=10)

    with tempfile.TemporaryDirectory() as td:
        session_mgr = SessionManager(td)
        loop = AgentLoop(
            llm, tm, governance, pipeline, parser, session_mgr, memory, config
        )
        result = loop.run("clean up the project")

    # 验证: 任务最终成功完成（agent 放弃了危险操作）
    assert result.success is True
    assert result.answer == "task completed"

    # 验证: 危险命令被 governance 直接判定为 BLOCKED
    dangerous_action = Action(
        type=ActionType.CALL_TOOL,
        tool_name="run_shell",
        tool_args={"command": "rm -rf /"},
    )
    perm_result = governance.check(dangerous_action)
    assert perm_result.permission == Permission.BLOCKED
    assert "blocked pattern" in perm_result.reason.lower()