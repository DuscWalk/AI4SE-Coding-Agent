import sys
from coding_agent.infrastructure.subprocess_manager import SubprocessManager


def test_run_simple_command():
    mgr = SubprocessManager()
    result = mgr.run("echo hello")
    assert result["exit_code"] == 0
    assert "hello" in result["stdout"]


def test_run_failing_command():
    mgr = SubprocessManager()
    result = mgr.run(f"{sys.executable} -c \"import sys; sys.exit(1)\"")
    assert result["exit_code"] == 1


def test_run_timeout():
    mgr = SubprocessManager(default_timeout=1)
    result = mgr.run(f"{sys.executable} -c \"import time; time.sleep(10)\"", timeout=1)
    assert result["exit_code"] == -1
    assert "timeout" in result["stderr"].lower()