from __future__ import annotations
import py_compile
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