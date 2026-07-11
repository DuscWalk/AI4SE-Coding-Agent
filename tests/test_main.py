from __future__ import annotations

from coding_agent.main import _create_agent_loop


def test_create_agent_loop_registers_runtime_dependencies() -> None:
    loop = _create_agent_loop(hitl_enabled=True)

    assert loop.hitl_enabled is True
    assert {tool["name"] for tool in loop.tool_manager.list_defs()} == {
        "git_commit",
        "git_diff",
        "git_status",
        "list_dir",
        "read_file",
        "run_shell",
        "run_test",
        "search_files",
        "grep",
        "write_file",
    }
