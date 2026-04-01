"""
cli.py - Command-line interface for WinLogView.

Usage
-----
    python -m winlogview --log System --level Error Warning --limit 100
    python -m winlogview --log Application --export report.html
    python -m winlogview --log Security --event-id 4625 --export audit.csv
"""

import argparse
import sys
from datetime import datetime, timedelta

from .reader import EventLogReader
from .filter import EventFilter
from .exporter import EventExporter


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="winlogview",
        description="WinLogView — Access Windows Event Viewer logs from Python.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m winlogview
  python -m winlogview --log Application --level Error --limit 50
  python -m winlogview --log Security --event-id 4625 4624
  python -m winlogview --log System --hours 24 --export report.html
  python -m winlogview --log System --export events.csv
        """,
    )
    p.add_argument("--log",      default="System",
                   help="Event log channel (default: System)")
    p.add_argument("--server",   default=None,
                   help="Remote computer name (default: local machine)")
    p.add_argument("--level",    nargs="+",
                   choices=["Critical","Error","Warning","Information","Verbose","AuditFailure","AuditSuccess"],
                   help="Filter by level(s)")
    p.add_argument("--event-id", nargs="+", type=int, dest="event_id",
                   help="Filter by Event ID(s)")
    p.add_argument("--source",   nargs="+",
                   help="Filter by source/provider name(s)")
    p.add_argument("--keyword",  nargs="+",
                   help="Filter by keyword(s) in message (all must match)")
    p.add_argument("--hours",    type=float,
                   help="Limit to events from the last N hours")
    p.add_argument("--limit",    type=int, default=200,
                   help="Maximum records to retrieve (default: 200)")
    p.add_argument("--export",   metavar="FILE",
                   help="Export to file: .csv / .json / .html / .txt")
    p.add_argument("--no-color", action="store_true",
                   help="Disable coloured terminal output")
    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    # Build filter
    f = EventFilter()
    if args.level:
        f.level(*args.level)
    if args.event_id:
        f.event_id(*args.event_id)
    if args.source:
        f.source(*args.source)
    if args.keyword:
        f.keyword(*args.keyword)
    if args.hours:
        since = datetime.utcnow() - timedelta(hours=args.hours)
        f.after(since)

    # Read
    reader = EventLogReader(log_name=args.log, server=args.server)
    print(f"📋  Reading '{args.log}' log  (limit={args.limit}) …\n")
    records = reader.read_all(event_filter=f, max_records=args.limit)

    if not records:
        print("  No records matched the given filters.")
        return 0

    # Print to terminal
    for r in records:
        if args.no_color:
            ts = r.time_created.strftime("%Y-%m-%d %H:%M:%S") if r.time_created else "N/A"
            print(f"[{ts}] [{r.level:<12}] ID={r.event_id} | {r.source}")
            print(f"  {r.message[:160]}")
        else:
            print(r)

    print(f"\n  ✅  {len(records)} record(s) retrieved.")

    # Export
    if args.export:
        exporter = EventExporter(records)
        ext = args.export.rsplit(".", 1)[-1].lower()
        dispatch = {
            "csv":  exporter.to_csv,
            "json": exporter.to_json,
            "html": exporter.to_html,
            "txt":  exporter.to_txt,
        }
        if ext not in dispatch:
            print(f"  ⚠️  Unknown extension '.{ext}'. Choose csv/json/html/txt.", file=sys.stderr)
            return 1
        out = dispatch[ext](args.export)
        print(f"  💾  Exported → {out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())