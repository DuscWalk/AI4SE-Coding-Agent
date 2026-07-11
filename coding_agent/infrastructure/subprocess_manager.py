from __future__ import annotations
import subprocess
from typing import TypedDict


class SubprocessResult(TypedDict):
    exit_code: int
    stdout: str
    stderr: str


class SubprocessManager:
    def __init__(self, default_timeout: int = 120):
        self.default_timeout = default_timeout

    def run(
        self,
        command: str,
        timeout: int | None = None,
        cwd: str | None = None,
    ) -> SubprocessResult:
        timeout = timeout or self.default_timeout
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
            )
            return {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except subprocess.TimeoutExpired:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Command timeout after {timeout}s",
            }
