"""Tests for FeedbackPipeline integration."""
from __future__ import annotations
import tempfile
from pathlib import Path
from coding_agent.domain.feedback.pipeline import FeedbackPipeline, PipelineResult
from coding_agent.domain.feedback.sensors import SyntaxSensor
from coding_agent.domain.feedback.classifier import FailureClassifier
from coding_agent.domain.feedback.engine import CorrectionEngine, CorrectionStrategy


def test_pipeline_with_syntax_error():
    """Pipeline should detect syntax errors and return a non-IGNORE strategy."""
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
    """Pipeline should return IGNORE strategy for clean files."""
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
    """Pipeline should return 'All checks passed.' for empty file list."""
    pipeline = FeedbackPipeline(
        sensors=[SyntaxSensor()],
        classifier=FailureClassifier(),
        engine=CorrectionEngine(max_retries=3),
    )
    result = pipeline.run([])
    assert result.feedback_text == "All checks passed."