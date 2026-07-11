# coding_agent/domain/tools/file_tools.py
from coding_agent.infrastructure.file_system import FileSystemManager
from coding_agent.domain.tool_manager import ToolArgs, ToolDef, ToolManager, ToolPermission


def register_file_tools(tm: ToolManager, fs: FileSystemManager) -> None:
    def read_file(args: ToolArgs) -> str:
        return fs.read_file(args["path"])

    def write_file(args: ToolArgs) -> str:
        fs.write_file(args["path"], args["content"])
        return f"Written: {args['path']}"

    def list_dir(args: ToolArgs) -> str:
        items = fs.list_dir(args["path"])
        return "\n".join(items)

    tm.register(ToolDef("read_file", "Read a file", {"path": "str"}, ToolPermission.SAFE, read_file))
    tm.register(ToolDef("write_file", "Write a file", {"path": "str", "content": "str"}, ToolPermission.RISKY, write_file))
    tm.register(ToolDef("list_dir", "List directory contents", {"path": "str"}, ToolPermission.SAFE, list_dir))
