"""write_calendar.py — Calendar write CLI.

Usage:
    python src/write_calendar.py create \\
        --calendar-id "primary" \\
        --summary "Dentist" \\
        --start "2026-03-20T10:00:00" \\
        --end "2026-03-20T11:00:00" \\
        [--description "Dr Smith"] \\
        [--location "Mall XYZ"] \\
        [--timezone "Asia/Singapore"] \\
        --confirm

    python src/write_calendar.py update \\
        --calendar-id "primary" \\
        --event-id "abc123" \\
        [--summary "New title"] \\
        [--start "2026-03-20T11:00:00"] \\
        [--end "2026-03-20T12:00:00"] \\
        [--description "..."] \\
        [--location "..."] \\
        --confirm

    python src/write_calendar.py delete \\
        --calendar-id "primary" \\
        --event-id "abc123" \\
        --confirm

IMPORTANT: --confirm is required for all write operations.
Never pass --confirm without live user approval in the current session.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow running from project root or src/
sys.path.insert(0, str(Path(__file__).parent))

from calendar_client import CalendarClient

_ROOT = Path(__file__).parent.parent
WRITE_LOG = _ROOT / "logs" / "calendar_writes.log"


def _audit_log(action: str, calendar_id: str, detail: dict) -> None:
    """Append a line to calendar_writes.log."""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    line = f"{now} | {action:10s} | calendar={calendar_id} | {json.dumps(detail)}\n"
    try:
        WRITE_LOG.parent.mkdir(exist_ok=True)
        with WRITE_LOG.open("a", encoding="utf-8") as fh:
            fh.write(line)
    except OSError as exc:
        print(f"WARNING: could not write audit log: {exc}", file=sys.stderr)


def cmd_create(args: argparse.Namespace, client: CalendarClient) -> None:
    event = client.create_event(
        calendar_id=args.calendar_id,
        summary=args.summary,
        start=args.start,
        end=args.end,
        description=args.description,
        location=args.location,
        timezone=args.timezone,
    )
    _audit_log("create", args.calendar_id, {
        "event_id": event.get("id"),
        "summary": args.summary,
        "start": args.start,
        "end": args.end,
    })
    print(json.dumps({
        "status": "created",
        "event_id": event.get("id"),
        "summary": event.get("summary"),
        "htmlLink": event.get("htmlLink"),
    }, indent=2))


def cmd_update(args: argparse.Namespace, client: CalendarClient) -> None:
    event = client.update_event(
        calendar_id=args.calendar_id,
        event_id=args.event_id,
        summary=args.summary,
        start=args.start,
        end=args.end,
        description=args.description,
        location=args.location,
        timezone=args.timezone,
    )
    _audit_log("update", args.calendar_id, {
        "event_id": args.event_id,
        "fields_changed": {k: v for k, v in {
            "summary": args.summary,
            "start": args.start,
            "end": args.end,
            "description": args.description,
            "location": args.location,
        }.items() if v is not None},
    })
    print(json.dumps({
        "status": "updated",
        "event_id": event.get("id"),
        "summary": event.get("summary"),
        "htmlLink": event.get("htmlLink"),
    }, indent=2))


def cmd_delete(args: argparse.Namespace, client: CalendarClient) -> None:
    client.delete_event(calendar_id=args.calendar_id, event_id=args.event_id)
    _audit_log("delete", args.calendar_id, {"event_id": args.event_id})
    print(json.dumps({"status": "deleted", "event_id": args.event_id}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Calendar write operations CLI")
    parser.add_argument(
        "--confirm", action="store_true",
        help="Required — confirms live user approval for this write operation",
    )
    sub = parser.add_subparsers(dest="command")

    # --- create ---
    p_create = sub.add_parser("create", help="Create a new event")
    p_create.add_argument("--calendar-id", required=True)
    p_create.add_argument("--summary", required=True)
    p_create.add_argument("--start", required=True, help="ISO 8601 datetime e.g. 2026-03-20T10:00:00")
    p_create.add_argument("--end", required=True, help="ISO 8601 datetime e.g. 2026-03-20T11:00:00")
    p_create.add_argument("--description", default=None)
    p_create.add_argument("--location", default=None)
    p_create.add_argument("--timezone", default="Asia/Singapore")

    # --- update ---
    p_update = sub.add_parser("update", help="Update fields on an existing event")
    p_update.add_argument("--calendar-id", required=True)
    p_update.add_argument("--event-id", required=True)
    p_update.add_argument("--summary", default=None)
    p_update.add_argument("--start", default=None)
    p_update.add_argument("--end", default=None)
    p_update.add_argument("--description", default=None)
    p_update.add_argument("--location", default=None)
    p_update.add_argument("--timezone", default="Asia/Singapore")

    # --- delete ---
    p_delete = sub.add_parser("delete", help="Permanently delete an event")
    p_delete.add_argument("--calendar-id", required=True)
    p_delete.add_argument("--event-id", required=True)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if not args.confirm:
        print(
            "ERROR: --confirm flag is required. "
            "Never pass --confirm without explicit live user approval.",
            file=sys.stderr,
        )
        sys.exit(2)

    client = CalendarClient()

    if args.command == "create":
        cmd_create(args, client)
    elif args.command == "update":
        cmd_update(args, client)
    elif args.command == "delete":
        cmd_delete(args, client)


if __name__ == "__main__":
    main()
