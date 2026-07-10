"""
机制演示 2: 反馈闭环——注入失败，agent 收到反馈并修正
使用 mock LLM 驱动，确定性验证反馈闭环的修正行为。
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from coding_agent.application.action_parser import ActionParser
from coding_agent.application.agent_loop import AgentLoop
from coding_agent.application.session_manager import SessionManager
from coding_agent.domain.config import Config
from coding_agent.domain.feedback.classifier import FailureClassifier
from coding_agent.domain.feedback.engine import CorrectionEngine, CorrectionStrategy
from coding_agent.domain.feedback.pipeline import FeedbackPipeline
from coding_agent.domain.feedback.sensors import SyntaxSensor
from coding_agent.domain.governance import Governance, Permission
from coding_agent.domain.memory import MemoryManager
from coding_agent.domain.tool_manager import ToolDef, ToolManager, ToolPermission
from coding_agent.infrastructure.file_system import FileSystemManager
from coding_agent.infrastructure.llm_provider import (
    LLMResponse,
    ScriptedMockLLM,
    ToolCall,
)
from coding_agent.infrastructure.vector_store import InMemoryVectorStore


def test_demo_feedback_loop_correction():
    """
    演示场景:
    1. Agent 写入一个语法错误的 Python 文件
    2. 反馈管线的 SyntaxSensor 检测到语法错误
    3. 反馈文本注入上下文
    4. Agent 收到反馈后修正文件
    5. 最终任务完成，文件内容正确
    """
    with tempfile.TemporaryDirectory() as td:
        bad_file = Path(td) / "broken.py"
        session_dir = Path(td) / "sessions"
        session_dir.mkdir()

        fs = FileSystemManager(allowed_dirs=[td])

        # Scripted mock LLM: 3 步响应序列
        responses = [
            # 第 1 步: 写错误文件
            LLMResponse(
                text="writing the broken file",
                tool_calls=[
                    ToolCall(
                        name="write_file",
                        arguments={
                            "path": str(bad_file),
                            "content": "def broken(\n    return 'oops'\n",
                            "_changed_files": [str(bad_file)],
                        },
                    )
                ],
            ),
            # 第 2 步: 收到 feedback 后修正
            LLMResponse(
                text="fixing the syntax error",
                tool_calls=[
                    ToolCall(
                        name="write_file",
                        arguments={
                            "path": str(bad_file),
                            "content": "def hello():\n    return 'world'\n",
                            "_changed_files": [str(bad_file)],
                        },
                    )
                ],
            ),
            # 第 3 步: 完成
            LLMResponse(text="all fixed and done", tool_calls=[]),
        ]

        llm = ScriptedMockLLM(responses)

        tm = ToolManager()
        tm.register(
            ToolDef(
                "write_file",
                "write a file to disk",
                {"path": "str", "content": "str", "_changed_files": "list"},
                ToolPermission.RISKY,
                lambda a: fs.write_file(a["path"], a["content"]) or "written",
            )
        )

        governance = Governance()
        pipeline = FeedbackPipeline(
            sensors=[SyntaxSensor()],
            classifier=FailureClassifier(),
            engine=CorrectionEngine(max_retries=3),
        )

        loop = AgentLoop(
            llm=llm,
            tool_manager=tm,
            governance=governance,
            feedback_pipeline=pipeline,
            action_parser=ActionParser(),
            session_manager=SessionManager(str(session_dir)),
            memory=MemoryManager(InMemoryVectorStore()),
            config=Config(max_steps=10),
        )

        # 演示需要 write_file 自动执行，临时将权限设为 ALLOWED
        original = Governance.TOOL_PERMISSIONS.get("write_file")
        Governance.TOOL_PERMISSIONS["write_file"] = Permission.ALLOWED
        try:
            result = loop.run(f"create {bad_file}")
        finally:
            if original is not None:
                Governance.TOOL_PERMISSIONS["write_file"] = original
            else:
                Governance.TOOL_PERMISSIONS.pop("write_file", None)

        # 验证: 任务成功完成
        assert result.success is True, f"agent should succeed, got error: {result.error}"
        assert result.answer == "all fixed and done"

        # 验证: 文件最终是正确的
        content = fs.read_file(str(bad_file))
        assert "def hello():" in content, f"file should contain fixed code, got:\n{content}"
        assert "def broken(" not in content, "broken syntax should have been replaced"


def test_demo_feedback_pipeline_detects_syntax_error():
    """
    直接验证反馈管线的错误检测与策略判定:
    1. SyntaxSensor 检测到语法错误
    2. FailureClassifier 分类为 SYNTAX_ERROR
    3. CorrectionEngine 判定为 RETRY（非 IGNORE）
    """
    with tempfile.TemporaryDirectory() as td:
        bad_file = Path(td) / "error.py"
        bad_file.write_text("def broken(\n    return 'oops'\n", encoding="utf-8")

        pipeline = FeedbackPipeline(
            sensors=[SyntaxSensor()],
            classifier=FailureClassifier(),
            engine=CorrectionEngine(max_retries=3),
        )

        fb_result = pipeline.run([str(bad_file)])

        # 验证: 反馈文本不是 "All checks passed."
        assert fb_result.feedback_text != "All checks passed.", (
            "should detect syntax error, not return all-passed"
        )

        # 验证: 反馈文本包含错误文件路径和错误类型
        assert "error.py" in fb_result.feedback_text, (
            f"feedback should mention the file, got: {fb_result.feedback_text}"
        )
        assert "syntax" in fb_result.feedback_text.lower(), (
            f"feedback should mention syntax error, got: {fb_result.feedback_text}"
        )

        # 验证: 策略是 RETRY（阻塞性错误），不是 IGNORE
        assert fb_result.strategy == CorrectionStrategy.RETRY, (
            f"correction strategy should be RETRY for blocking error, "
            f"got: {fb_result.strategy}"
        )
        assert fb_result.strategy != CorrectionStrategy.IGNORE, (
            "correction strategy should NOT be IGNORE for syntax error"
        )

        # 验证: sensor 报告正确
        assert len(fb_result.sensor_reports) == 1
        assert fb_result.sensor_reports[0].sensor_name == "syntax"
        assert fb_result.sensor_reports[0].passed is False
        assert len(fb_result.sensor_reports[0].failures) == 1
        assert fb_result.sensor_reports[0].failures[0].category.value == "syntax"


def test_demo_feedback_pipeline_passes_clean_file():
    """验证无错误时管线返回 IGNORE 策略和 All checks passed."""
    with tempfile.TemporaryDirectory() as td:
        good_file = Path(td) / "good.py"
        good_file.write_text("def hello():\n    return 'world'\n", encoding="utf-8")

        pipeline = FeedbackPipeline(
            sensors=[SyntaxSensor()],
            classifier=FailureClassifier(),
            engine=CorrectionEngine(max_retries=3),
        )

        fb_result = pipeline.run([str(good_file)])

        assert fb_result.feedback_text == "All checks passed."
        assert fb_result.strategy == CorrectionStrategy.IGNORE
        assert fb_result.sensor_reports[0].passed is True