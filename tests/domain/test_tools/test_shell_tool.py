# tests/domain/test_tools/test_shell_tool.py
from coding_agent.domain.tool_manager import ToolManager
from coding_agent.domain.tools.shell_tool import register_shell_tool
from coding_agent.infrastructure.subprocess_manager import SubprocessManager
from coding_agent.domain.models import Action, ActionType

def test_run_shell_tool():
    tm = ToolManager()
    sm = SubprocessManager()
    register_shell_tool(tm, sm)
    action = Action(type=ActionType.CALL_TOOL, tool_name="run_shell", tool_args={"command": "echo hello"})
    result = tm.dispatch(action)
    assert result.success is True
    assert "hello" in result.output