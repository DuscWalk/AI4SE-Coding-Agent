# coding_agent/domain/tools/git_tools.py
from coding_agent.infrastructure.subprocess_manager import SubprocessManager
from coding_agent.domain.tool_manager import ToolDef, ToolManager, ToolPermission


def register_git_tools(tm: ToolManager, sm: SubprocessManager) -> None:
    def _git(cmd: str) -> str:
        r = sm.run(f"git {cmd}")
        return r["stdout"] + r["stderr"]

    tm.register(ToolDef("git_status", "Show git status", {}, ToolPermission.SAFE, lambda _args: _git("status --short")))
    tm.register(ToolDef("git_diff", "Show git diff", {}, ToolPermission.SAFE, lambda _args: _git("diff")))
    tm.register(ToolDef("git_commit", "Create a git commit", {"message": "str"}, ToolPermission.RISKY,
                         lambda args: _git(f'commit -m "{args["message"]}"')))
