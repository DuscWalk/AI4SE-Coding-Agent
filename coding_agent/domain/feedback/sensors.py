from __future__ import annotations
import py_compile
import subprocess
import time
from abc import ABC, abstractmethod
from pathlib import Path
from coding_agent.domain.models import (
    SensorReport, SensorFailure, FailureCategory, FailureSeverity
)


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


def _parse_structured_line(line: str) -> tuple[str, int | None, str]:
    """Parse a line like 'file.py:10: error: message' into (file, line, message)."""
    parts = line.split(":", 2)
    file_path = parts[0].strip() if len(parts) > 0 else ""
    line_num: int | None = None
    if len(parts) > 1 and parts[1].strip().isdigit():
        line_num = int(parts[1].strip())
    message = parts[2].strip() if len(parts) > 2 else line
    return file_path, line_num, message


class TypeCheckSensor(Sensor):
    name = "typecheck"

    def sense(self, changed_files: list[str]) -> SensorReport:
        start = time.time()
        failures: list[SensorFailure] = []
        py_files = [f for f in changed_files if f.endswith(".py")]

        if not py_files:
            return SensorReport(
                sensor_name=self.name, passed=True, failures=[], duration_ms=0
            )

        try:
            result = subprocess.run(
                ["mypy", "--no-error-summary", "--show-error-codes"] + py_files,
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode != 0:
                for line in result.stdout.splitlines():
                    stripped = line.strip()
                    if not stripped:
                        continue
                    # mypy error lines look like: file.py:line: error: message
                    if ":" in stripped:
                        file_path, line_num, message = _parse_structured_line(stripped)
                        failures.append(SensorFailure(
                            file_path=file_path,
                            line=line_num,
                            severity=FailureSeverity.ERROR,
                            category=FailureCategory.TYPE_ERROR,
                            message=message,
                            raw_output=stripped,
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
            return SensorReport(
                sensor_name=self.name, passed=True, failures=[], duration_ms=0
            )

        try:
            result = subprocess.run(
                ["ruff", "check"] + py_files,
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                for line in result.stdout.splitlines():
                    stripped = line.strip()
                    if not stripped:
                        continue
                    if ":" in stripped:
                        file_path, line_num, message = _parse_structured_line(stripped)
                        failures.append(SensorFailure(
                            file_path=file_path,
                            line=line_num,
                            severity=FailureSeverity.WARNING,
                            category=FailureCategory.LINT_WARNING,
                            message=message,
                            raw_output=stripped,
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

        if not changed_files:
            return SensorReport(
                sensor_name=self.name, passed=True, failures=[], duration_ms=0
            )

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
                            message=line.strip(),
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