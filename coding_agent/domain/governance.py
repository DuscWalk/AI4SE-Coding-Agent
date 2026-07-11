# coding_agent/domain/governance.py
from __future__ import annotations
from enum import Enum
import re
import time
from coding_agent.domain.models import Action, ActionType


class Permission(str, Enum):
    ALLOWED = "ALLOWED"
    BLOCKED = "BLOCKED"
    NEEDS_CONFIRMATION = "NEEDS_CONFIRMATION"
    NEEDS_HITL = "NEEDS_HITL"


class PermissionResult:
    def __init__(self, permission: Permission, reason: str = "") -> None:
        self.permission = permission
        self.reason = reason


class HITLState:
    HITL_TIMEOUT_S = 300  # 5 minutes

    def __init__(self) -> None:
        self._pending = False
        self._request_message = ""
        self._resolved = False
        self._approved = False
        self._request_time = 0.0

    def request(self, message: str) -> None:
        self._pending = True
        self._request_message = message
        self._resolved = False
        self._approved = False
        self._request_time = time.time()

    def approve(self) -> bool:
        self._resolved = True
        self._approved = True
        self._pending = False
        return True

    def deny(self) -> bool:
        self._resolved = True
        self._approved = False
        self._pending = False
        return False

    def is_resolved(self) -> bool:
        return self._resolved

    def is_approved(self) -> bool:
        return self._approved

    def is_expired(self) -> bool:
        """Check if the HITL request has timed out."""
        if self._resolved or not self._pending:
            return False
        return (time.time() - self._request_time) > self.HITL_TIMEOUT_S

    @property
    def message(self) -> str:
        return self._request_message


class Governance:
    # Tool permission levels (default mapping, overridable via set_tool_permissions)
    TOOL_PERMISSIONS = {
        "read_file": Permission.ALLOWED,
        "list_dir": Permission.ALLOWED,
        "search_files": Permission.ALLOWED,
        "grep": Permission.ALLOWED,
        "run_test": Permission.ALLOWED,
        "git_status": Permission.ALLOWED,
        "git_diff": Permission.ALLOWED,
        "write_file": Permission.NEEDS_CONFIRMATION,
        "git_commit": Permission.NEEDS_CONFIRMATION,
        "run_shell": Permission.NEEDS_HITL,
    }

    # Hard-blocked patterns (cannot be overridden by HITL)
    BLOCKED_PATTERNS = [
        r"rm\s+-rf\s+/",
        r"DROP\s+TABLE",
        r"git\s+push\s+--force\s+main",
        r"chmod\s+777\s+/",
        r"format\s+C:",
        r"del\s+/[fF]\s+[C-Z]:\\",
        r">\s*/dev/sda",
        r"mkfs\.",
        r"dd\s+if=",
    ]

    def __init__(self, blocked_patterns: list[str] | None = None) -> None:
        self._blocked = blocked_patterns or self.BLOCKED_PATTERNS
        self._tool_permissions: dict[str, Permission] = dict(self.TOOL_PERMISSIONS)

    def set_tool_permissions(self, permissions: dict[str, str]) -> None:
        """Update tool permissions from an external source (e.g. ToolManager).

        Accepts a mapping of tool_name -> permission string (safe/risky/dangerous).
        Converts to internal Permission enum.
        """
        mapping = {
            "safe": Permission.ALLOWED,
            "risky": Permission.NEEDS_CONFIRMATION,
            "dangerous": Permission.NEEDS_HITL,
        }
        for name, perm_str in permissions.items():
            if perm_str in mapping:
                self._tool_permissions[name] = mapping[perm_str]

    def check(self, action: Action) -> PermissionResult:
        if action.type == ActionType.DONE:
            return PermissionResult(Permission.ALLOWED, "task complete")

        tool_name = action.tool_name
        if tool_name is None:
            return PermissionResult(Permission.BLOCKED, "no tool specified")

        # Check hard-blocked patterns
        if tool_name in ("run_shell", "git_commit"):
            command = str(action.tool_args)
            for pattern in self._blocked:
                if re.search(pattern, command, re.IGNORECASE):
                    return PermissionResult(
                        Permission.BLOCKED,
                        f"Command matches blocked pattern: {pattern}"
                    )

        # Check tool permission level
        permission = self._tool_permissions.get(tool_name)
        if permission is None:
            return PermissionResult(Permission.BLOCKED, f"Unknown tool: {tool_name}")

        return PermissionResult(permission, f"Tool '{tool_name}' permission: {permission.value}")
