# tests/domain/test_feedback/test_classifier.py
from coding_agent.domain.feedback.classifier import FailureClassifier
from coding_agent.domain.models import SensorReport, SensorFailure, FailureCategory, FailureSeverity


def test_classify_empty():
    """空报告列表应返回 total_failures=0 且 has_blocking=False。"""
    classifier = FailureClassifier()
    result = classifier.classify([])
    assert result.total_failures == 0
    assert result.has_blocking is False


def test_classify_single_failure():
    """单个语法错误应被正确识别为阻断性失败。"""
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
    """混合失败（ERROR + WARNING）应正确聚合 by_file 和 by_category。"""
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
    """仅有 WARNING 不应标记为阻断性失败。"""
    failure = SensorFailure(
        file_path="test.py", line=1, severity=FailureSeverity.WARNING,
        category=FailureCategory.LINT_WARNING, message="warn", raw_output="warn"
    )
    report = SensorReport(sensor_name="lint", passed=False, failures=[failure], duration_ms=5)
    classifier = FailureClassifier()
    result = classifier.classify([report])
    assert result.has_blocking is False


def test_summary_text():
    """summary 应包含文件名和失败类别信息。"""
    failure = SensorFailure(
        file_path="test.py", line=5, severity=FailureSeverity.ERROR,
        category=FailureCategory.SYNTAX_ERROR, message="invalid syntax", raw_output="err"
    )
    report = SensorReport(sensor_name="syntax", passed=False, failures=[failure], duration_ms=10)
    classifier = FailureClassifier()
    result = classifier.classify([report])
    assert "test.py" in result.summary
    assert "syntax" in result.summary.lower()


def test_blocking_failures_field():
    """blocking_failures 应仅包含 ERROR 严重度的失败。"""
    failures = [
        SensorFailure(file_path="a.py", line=1, severity=FailureSeverity.ERROR,
                      category=FailureCategory.SYNTAX_ERROR, message="e1", raw_output="e1"),
        SensorFailure(file_path="b.py", line=2, severity=FailureSeverity.WARNING,
                      category=FailureCategory.LINT_WARNING, message="w1", raw_output="w1"),
        SensorFailure(file_path="c.py", line=3, severity=FailureSeverity.ERROR,
                      category=FailureCategory.TYPE_ERROR, message="e2", raw_output="e2"),
    ]
    report = SensorReport(sensor_name="multi", passed=False, failures=failures, duration_ms=30)
    classifier = FailureClassifier()
    result = classifier.classify([report])
    assert len(result.blocking_failures) == 2
    assert all(f.severity == FailureSeverity.ERROR for f in result.blocking_failures)


def test_summary_all_passed():
    """全部通过时 summary 应给出通过信息。"""
    classifier = FailureClassifier()
    result = classifier.classify([])
    assert "All checks passed" in result.summary or "passed" in result.summary.lower()