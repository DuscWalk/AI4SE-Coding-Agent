import argparse
import sys
from pathlib import Path
from getpass import getpass


def main():
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

        app = create_app()
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
        print("CLI run mode: use 'serve' for WebUI, or run tests directly.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()