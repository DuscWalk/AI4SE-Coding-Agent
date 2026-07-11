import argparse
import sys
from pathlib import Path
from getpass import getpass
from coding_agent.application.agent_loop import AgentLoop


def _create_agent_loop(hitl_enabled: bool = False) -> AgentLoop:
    """Create a fully wired AgentLoop with all components."""
    from coding_agent.domain.config import Config
    from coding_agent.domain.tool_manager import ToolManager
    from coding_agent.domain.governance import Governance
    from coding_agent.domain.memory import MemoryManager
    from coding_agent.domain.feedback.sensors import SyntaxSensor, TypeCheckSensor, LintSensor, TestSensor
    from coding_agent.domain.feedback.classifier import FailureClassifier
    from coding_agent.domain.feedback.engine import CorrectionEngine
    from coding_agent.domain.feedback.pipeline import FeedbackPipeline
    from coding_agent.application.action_parser import ActionParser
    from coding_agent.application.session_manager import SessionManager
    from coding_agent.application.agent_loop import AgentLoop
    from coding_agent.infrastructure.credential_store import CredentialStore
    from coding_agent.infrastructure.real_llm import RealLLMProvider
    from coding_agent.infrastructure.vector_store import InMemoryVectorStore
    from coding_agent.infrastructure.file_system import FileSystemManager
    from coding_agent.infrastructure.subprocess_manager import SubprocessManager
    from coding_agent.domain.tools.file_tools import register_file_tools
    from coding_agent.domain.tools.search_tools import register_search_tools
    from coding_agent.domain.tools.git_tools import register_git_tools
    from coding_agent.domain.tools.shell_tool import register_shell_tool
    from coding_agent.domain.tools.test_tool import register_test_tool

    config = Config.load(Path.cwd())
    credential_store = CredentialStore()
    llm = RealLLMProvider(credential_store, model_name=config.model_name)

    tool_manager = ToolManager()
    file_system = FileSystemManager(config.allowed_dirs)
    subprocess_manager = SubprocessManager()
    register_file_tools(tool_manager, file_system)
    register_search_tools(tool_manager)
    register_git_tools(tool_manager, subprocess_manager)
    register_shell_tool(tool_manager, subprocess_manager)
    register_test_tool(tool_manager, subprocess_manager)

    governance = Governance(blocked_patterns=config.blocked_patterns if config.blocked_patterns else None)
    governance.set_tool_permissions({
        name: t.permission.value
        for name, t in tool_manager._tools.items()
    })

    vector_store = InMemoryVectorStore()
    memory = MemoryManager(vector_store)

    sensors = [SyntaxSensor(), TypeCheckSensor(), LintSensor(), TestSensor()]
    classifier = FailureClassifier()
    engine = CorrectionEngine(max_retries=config.max_retries)
    feedback_pipeline = FeedbackPipeline(sensors, classifier, engine)

    action_parser = ActionParser()
    session_manager = SessionManager()

    return AgentLoop(
        llm=llm,
        tool_manager=tool_manager,
        governance=governance,
        feedback_pipeline=feedback_pipeline,
        action_parser=action_parser,
        session_manager=session_manager,
        memory=memory,
        config=config,
        hitl_enabled=hitl_enabled,
    )


def main() -> None:
    parser = argparse.ArgumentParser(prog="coding-agent", description="Coding Agent Harness")
    sub = parser.add_subparsers(dest="command")

    serve_parser = sub.add_parser("serve", help="Start WebUI server")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8080)

    cred_parser = sub.add_parser("credentials", help="Manage API credentials")
    cred_parser.add_argument("action", choices=["set", "status", "clear"])

    run_parser = sub.add_parser("run", help="Run a task from CLI")
    run_parser.add_argument("goal", nargs="+")

    args = parser.parse_args()

    if args.command == "serve":
        from coding_agent.presentation.app import create_app
        import uvicorn

        loop = _create_agent_loop(hitl_enabled=True)
        app = create_app(loop=loop)
        uvicorn.run(app, host=args.host, port=args.port)

    elif args.command == "credentials":
        from coding_agent.infrastructure.credential_store import CredentialStore

        store = CredentialStore()
        if args.action == "set":
            key = getpass("Enter API key: ")
            store.set_api_key(key)
            print("API key saved.")
        elif args.action == "status":
            status = store.get_status()
            print(f"Configured: {status['configured']}")
        elif args.action == "clear":
            store.clear_api_key()
            print("API key cleared.")

    elif args.command == "run":
        goal = " ".join(args.goal)
        print(f"Task: {goal}")
        print("Initializing agent loop...")
        loop = _create_agent_loop(hitl_enabled=False)
        print("Running...")
        result = loop.run(goal)
        if result.success:
            print(f"Done: {result.answer}")
        else:
            print(f"Failed: {result.error}")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
