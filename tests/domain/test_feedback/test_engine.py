# tests/domain/test_feedback/test_engine.py
from coding_agent.domain.feedback.engine import CorrectionEngine, CorrectionStrategy
from coding_agent.domain.feedback.classifier import ClassifiedResult


def test_retry_on_blocking():
    """有阻断性失败时，retry_count 未超限应返回 RETRY。"""
    engine = CorrectionEngine(max_retries=3)
    result = ClassifiedResult(has_blocking=True)
    assert engine.decide(result) == CorrectionStrategy.RETRY


def test_retry_then_rollback_then_ask_user():
    """渐进式升级：RETRY → ROLLBACK → ASK_USER。"""
    engine = CorrectionEngine(max_retries=2)
    result = ClassifiedResult(has_blocking=True)
    assert engine.decide(result) == CorrectionStrategy.RETRY
    assert engine.decide(result) == CorrectionStrategy.RETRY
    assert engine.decide(result) == CorrectionStrategy.ROLLBACK
    assert engine.decide(result) == CorrectionStrategy.ASK_USER


def test_ignore_when_no_blocking():
    """无阻断性失败时应返回 IGNORE。"""
    engine = CorrectionEngine(max_retries=3)
    result = ClassifiedResult(has_blocking=False)
    assert engine.decide(result) == CorrectionStrategy.IGNORE


def test_reset_retry_count():
    """reset() 后 retry_count 应归零。"""
    engine = CorrectionEngine(max_retries=2)
    result = ClassifiedResult(has_blocking=True)
    engine.decide(result)
    engine.reset()
    assert engine.retry_count == 0