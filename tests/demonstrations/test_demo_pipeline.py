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
        assert len(result.sensor_reports) == 1
        assert result.sensor_reports[0].sensor_name == "syntax"
        assert result.sensor_reports[0].passed is False


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
    """验证渐进式升级：RETRY → ROLLBACK → ASK_USER"""
    engine = CorrectionEngine(max_retries=2)
    from coding_agent.domain.feedback.classifier import ClassifiedResult

    blocking_result = ClassifiedResult(has_blocking=True, total_failures=1, summary="error")

    assert engine.decide(blocking_result) == CorrectionStrategy.RETRY
    assert engine.decide(blocking_result) == CorrectionStrategy.RETRY
    assert engine.decide(blocking_result) == CorrectionStrategy.ROLLBACK
    assert engine.decide(blocking_result) == CorrectionStrategy.ASK_USER