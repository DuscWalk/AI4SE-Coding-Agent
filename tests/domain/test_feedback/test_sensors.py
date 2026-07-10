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