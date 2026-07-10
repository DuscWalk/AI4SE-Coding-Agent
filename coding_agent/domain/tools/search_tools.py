# coding_agent/domain/tools/search_tools.py
import glob
import re
from pathlib import Path
from coding_agent.domain.tool_manager import ToolDef, ToolPermission


def register_search_tools(tm):
    def search_files(args):
        pattern = args.get("pattern", "**/*")
        matches = glob.glob(pattern, recursive=True)
        return "\n".join(matches[:50])

    def grep(args):
        pattern = args["pattern"]
        path = args.get("path", ".")
        results = []
        for f in Path(path).rglob("*.py"):
            try:
                for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                    if re.search(pattern, line):
                        results.append(f"{f}:{i}: {line.strip()}")
            except Exception:
                pass
        return "\n".join(results[:50])

    tm.register(ToolDef("search_files", "Search files by glob", {"pattern": "str"}, ToolPermission.SAFE, search_files))
    tm.register(ToolDef("grep", "Search file contents by regex", {"pattern": "str", "path": "str"}, ToolPermission.SAFE, grep))