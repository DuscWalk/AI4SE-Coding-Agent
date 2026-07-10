import tempfile
from pathlib import Path
from coding_agent.domain.feedback.sensors import (
    SyntaxSensor, TypeCheckSensor, LintSensor, TestSensor, SensorReport
)
from coding_agent.domain.models import FailureCategory


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


# --- Task 11: TypeCheck, Lint, Test sensors ---


def test_typecheck_sensor_pass():
    """TypeCheckSensor should pass on a correctly typed file."""
    sensor = TypeCheckSensor()
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "typed.py"
        f.write_text("def add(a: int, b: int) -> int:\n    return a + b\n")
        report = sensor.sense([str(f)])
        assert isinstance(report, SensorReport)
        assert report.passed is True
        assert len(report.failures) == 0


def test_typecheck_sensor_fail():
    """TypeCheckSensor should detect a type error (returning str when int is expected)."""
    sensor = TypeCheckSensor()
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "bad_type.py"
        f.write_text("def add(a: int, b: int) -> str:\n    return a + b\n")
        report = sensor.sense([str(f)])
        assert isinstance(report, SensorReport)
        if not report.passed:
            assert any(
                f.category == FailureCategory.TYPE_ERROR for f in report.failures
            )


def test_typecheck_sensor_empty_files():
    """TypeCheckSensor should return passed=True when no files given."""
    sensor = TypeCheckSensor()
    report = sensor.sense([])
    assert report.passed is True


def test_lint_sensor():
    """LintSensor should produce a SensorReport on a file with lint issues."""
    sensor = LintSensor()
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "style.py"
        f.write_text("import os\nimport sys\n\ndef foo():\n    pass\n")
        report = sensor.sense([str(f)])
        assert isinstance(report, SensorReport)


def test_lint_sensor_empty_files():
    """LintSensor should return passed=True when no files given."""
    sensor = LintSensor()
    report = sensor.sense([])
    assert report.passed is True


def test_test_sensor_pass():
    """TestSensor should produce a SensorReport on a passing test file."""
    sensor = TestSensor()
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "test_ok.py"
        f.write_text("def test_pass():\n    assert True\n")
        report = sensor.sense([str(f)])
        assert isinstance(report, SensorReport)


def test_test_sensor_fail():
    """TestSensor should detect a failing test."""
    sensor = TestSensor()
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "test_fail.py"
        f.write_text("def test_fail():\n    assert False\n")
        report = sensor.sense([str(f)])
        assert isinstance(report, SensorReport)
        if not report.passed:
            assert any(
                f.category == FailureCategory.TEST_FAILURE for f in report.failures
            )


def test_test_sensor_empty_files():
    """TestSensor should return passed=True when no files given."""
    sensor = TestSensor()
    report = sensor.sense([])
    assert report.passed is True