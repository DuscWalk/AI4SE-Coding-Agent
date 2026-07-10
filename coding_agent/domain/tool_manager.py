# coding_agent/domain/tool_manager.py
from __future__ import annotations
from enum import Enum
from dataclasses import dataclass
from collections.abc import Callable
from coding_agent.domain.models import Action, ActionResult


class ToolPermission(str, Enum):
    SAFE = "safe"
    RISKY = "risky"
    DANGEROUS = "dangerous"


@dataclass
class ToolDef:
    name: str
    description: str
    parameters: dict
    permission: ToolPermission
    handler: Callable


class ToolManager:
    def __init__(self):
        self._tools: dict[str, ToolDef] = {}

    def register(self, tool: ToolDef) -> None:
        self._tools[tool.name] = tool

    def list_defs(self) -> list[dict]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
                "permission": t.permission.value,
            }
            for t in self._tools.values()
        ]

    def get(self, name: str) -> ToolDef | None:
        return self._tools.get(name)

    def dispatch(self, action: Action) -> ActionResult:
        tool = self._tools.get(action.tool_name or "")
        if tool is None:
            return ActionResult(
                success=False,
                error=f"Unknown tool: {action.tool_name}",
            )
        try:
            result = tool.handler(action.tool_args or {})
            changed_files = action.tool_args.get("_changed_files", []) if action.tool_args else []
            return ActionResult(
                success=True,
                output=str(result),
                changed_files=changed_files,
            )
        except Exception as e:
            return ActionResult(
                success=False,
                error=str(e),
            )