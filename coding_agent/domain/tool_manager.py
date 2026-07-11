# coding_agent/domain/tool_manager.py
from __future__ import annotations
from enum import Enum
from dataclasses import dataclass
from collections.abc import Callable
from typing import Any, TypeAlias
from coding_agent.domain.models import Action, ActionResult


class ToolPermission(str, Enum):
    SAFE = "safe"
    RISKY = "risky"
    DANGEROUS = "dangerous"


ToolArgs: TypeAlias = dict[str, Any]
ToolHandler: TypeAlias = Callable[[ToolArgs], str]
ToolDefinition: TypeAlias = dict[str, Any]


@dataclass
class ToolDef:
    name: str
    description: str
    parameters: dict[str, str]
    permission: ToolPermission
    handler: ToolHandler


class ToolManager:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDef] = {}

    def register(self, tool: ToolDef) -> None:
        self._tools[tool.name] = tool

    def list_defs(self) -> list[ToolDefinition]:
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
            tool_args = action.tool_args or {}
            result = tool.handler(tool_args)
            changed_files = tool_args.get("_changed_files", [])
            if tool.name == "write_file" and isinstance(tool_args.get("path"), str):
                changed_files = [tool_args["path"]]
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
