#!/usr/bin/env python3
"""
CLI entry point for the Body system.
Provides command-line access to the action coordinator.
"""

import sys
import json
import argparse
from body_coordinator import BodyCoordinator


def main():
    parser = argparse.ArgumentParser(
        description="Sovereign AI Body System — embodied action coordinator"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Execute action
    exec_parser = subparsers.add_parser("execute", help="Execute an action")
    exec_parser.add_argument("action_type", choices=["memory", "browser", "file"],
                             help="Type of action")
    exec_parser.add_argument("action_command", help="Command to execute")
    exec_parser.add_argument("--args", type=str, default="{}",
                             help="JSON arguments for the action")

    # Status
    subparsers.add_parser("status", help="Show body system status")

    # Undo
    subparsers.add_parser("undo", help="Undo last action")

    # Grant permission
    perm_parser = subparsers.add_parser("grant", help="Grant temporary path permission")
    perm_parser.add_argument("path", help="Path to grant access to")
    perm_parser.add_argument("--minutes", type=int, default=60,
                             help="Duration in minutes (default: 60)")

    # Memory triggers
    trigger_parser = subparsers.add_parser("add-trigger", help="Add memory-action trigger")
    trigger_parser.add_argument("--type", required=True, help="Trigger type")
    trigger_parser.add_argument("--keywords", required=True, help="Comma-separated keywords")
    trigger_parser.add_argument("--action-type", required=True, help="Action type to fire")
    trigger_parser.add_argument("--command", required=True, help="Command to execute")
    trigger_parser.add_argument("--action-args", type=str, default="{}",
                                help="JSON arguments for triggered action")

    subparsers.add_parser("list-triggers", help="List memory-action triggers")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    body = BodyCoordinator()

    try:
        if args.command == "execute":
            action_args = json.loads(args.args)
            result = body.execute_action(
                args.action_type, args.action_command, action_args
            )
            print(json.dumps(result, indent=2, default=str))

        elif args.command == "status":
            status = body.get_status()
            print(json.dumps(status, indent=2, default=str))

        elif args.command == "undo":
            result = body.undo_last_action()
            if result:
                print(json.dumps(result, indent=2, default=str))
            else:
                print("Nothing to undo.")

        elif args.command == "grant":
            body.grant_session_permission(args.path, args.minutes)
            print(f"Granted access to {args.path} for {args.minutes} minutes.")

        elif args.command == "add-trigger":
            from body_memory import BodyMemory
            bm = BodyMemory(body.db_path)
            keywords = [k.strip() for k in args.keywords.split(",")]
            action_args = json.loads(args.action_args)
            trigger_id = bm.add_trigger(
                args.type, keywords, args.action_type, args.command, action_args
            )
            print(f"Trigger created: {trigger_id}")

        elif args.command == "list-triggers":
            from body_memory import BodyMemory
            bm = BodyMemory(body.db_path)
            triggers = bm.list_triggers()
            print(json.dumps(triggers, indent=2, default=str))

    finally:
        body.shutdown()


if __name__ == "__main__":
    main()
