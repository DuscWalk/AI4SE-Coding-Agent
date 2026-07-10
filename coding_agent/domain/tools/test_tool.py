# coding_agent/domain/tools/test_tool.py
from coding_agent.infrastructure.subprocess_manager import SubprocessManager
from coding_agent.domain.tool_manager import ToolDef, ToolPermission


def register_test_tool(tm, sm: SubprocessManager):
    def run_test(args):
        result = sm.run("pytest -v --tb=short")
        return f"exit_code={result['exit_code']}\n{result['stdout']}"

    tm.register(ToolDef("run_test", "Run test suite", {}, ToolPermission.SAFE, run_test))