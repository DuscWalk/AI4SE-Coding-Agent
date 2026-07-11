# tests/domain/test_tool_manager.py
from coding_agent.domain.tool_manager import ToolManager, ToolDef, ToolPermission
from coding_agent.domain.models import Action, ActionType

def test_register_and_list_tools():
    tm = ToolManager()
    tm.register(ToolDef(
        name="echo", description="echo back",
        parameters={}, permission=ToolPermission.SAFE,
        handler=lambda args: "echo: " + str(args)
    ))
    defs = tm.list_defs()
    assert len(defs) == 1
    assert defs[0]["name"] == "echo"

def test_dispatch_tool():
    tm = ToolManager()
    tm.register(ToolDef(
        name="double", description="double a number",
        parameters={"n": "int"}, permission=ToolPermission.SAFE,
        handler=lambda args: args["n"] * 2
    ))
    action = Action(type=ActionType.CALL_TOOL, tool_name="double", tool_args={"n": 5})
    result = tm.dispatch(action)
    assert result.success is True
    assert result.output == "10"

def test_dispatch_unknown_tool():
    tm = ToolManager()
    action = Action(type=ActionType.CALL_TOOL, tool_name="nonexistent", tool_args={})
    result = tm.dispatch(action)
    assert result.success is False
    assert "unknown" in result.error.lower()

def test_tool_permission():
    tool = ToolDef(
        name="rm", description="delete",
        parameters={}, permission=ToolPermission.DANGEROUS,
        handler=lambda args: "deleted"
    )
    assert tool.permission == ToolPermission.DANGEROUS