# tests/domain/test_tools/test_file_tools.py
import tempfile
from pathlib import Path
from coding_agent.domain.tool_manager import ToolManager
from coding_agent.domain.tools.file_tools import register_file_tools
from coding_agent.infrastructure.file_system import FileSystemManager
from coding_agent.domain.models import Action, ActionType

def test_read_file_tool():
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "test.txt"
        f.write_text("hello", encoding="utf-8")
        tm = ToolManager()
        fs = FileSystemManager(allowed_dirs=[td])
        register_file_tools(tm, fs)
        action = Action(type=ActionType.CALL_TOOL, tool_name="read_file", tool_args={"path": str(f)})
        result = tm.dispatch(action)
        assert result.success is True
        assert result.output == "hello"

def test_write_file_tool():
    with tempfile.TemporaryDirectory() as td:
        tm = ToolManager()
        fs = FileSystemManager(allowed_dirs=[td])
        register_file_tools(tm, fs)
        f = Path(td) / "out.txt"
        action = Action(type=ActionType.CALL_TOOL, tool_name="write_file", tool_args={"path": str(f), "content": "data"})
        result = tm.dispatch(action)
        assert result.success is True
        assert f.read_text(encoding="utf-8") == "data"