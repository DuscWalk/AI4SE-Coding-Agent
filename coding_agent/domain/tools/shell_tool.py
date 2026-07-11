# coding_agent/domain/tools/shell_tool.py
from coding_agent.infrastructure.subprocess_manager import SubprocessManager
from coding_agent.domain.tool_manager import ToolArgs, ToolDef, ToolManager, ToolPermission


def register_shell_tool(tm: ToolManager, sm: SubprocessManager) -> None:
    def run_shell(args: ToolArgs) -> str:
        result = sm.run(args["command"])
        return f"exit_code={result['exit_code']}\nstdout:\n{result['stdout']}\nstderr:\n{result['stderr']}"

    tm.register(ToolDef("run_shell", "Execute a shell command", {"command": "str"}, ToolPermission.DANGEROUS, run_shell))
