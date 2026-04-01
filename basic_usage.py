"""
examples/basic_usage.py — Quick-start examples for WinLogView.

Run from the project root:
    python examples/basic_usage.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timedelta, timezone
from winlogview import EventLogReader, EventFilter, EventExporter


# ── 1. Read the last 20 System events ──────────────────────────────────────
print("=" * 60)
print("Example 1 – Last 20 System events")
print("=" * 60)

reader = EventLogReader("System")
for event in reader.read(max_records=20):
    print(event)

print()

# ── 2. Only errors & warnings from the last 6 hours ────────────────────────
print("=" * 60)
print("Example 2 – Errors & Warnings in the last 6 hours")
print("=" * 60)

since = datetime.now(tz=timezone.utc) - timedelta(hours=6)
f = EventFilter().level("Error", "Warning").after(since)

reader2 = EventLogReader("System")
critical_events = reader2.read_all(event_filter=f, max_records=50)
print(f"  Found {len(critical_events)} error/warning events.\n")
for e in critical_events[:5]:
    print(e)

print()

# ── 3. Filter by specific Event ID ─────────────────────────────────────────
print("=" * 60)
print("Example 3 – Event ID 41 (Kernel-Power unexpected shutdown)")
print("=" * 60)

f3 = EventFilter().event_id(41)
reader3 = EventLogReader("System")
shutdowns = reader3.read_all(event_filter=f3, max_records=10)
print(f"  Found {len(shutdowns)} unexpected shutdown event(s).\n")

print()

# ── 4. Export to multiple formats ──────────────────────────────────────────
print("=" * 60)
print("Example 4 – Export to CSV, JSON, HTML, and TXT")
print("=" * 60)

all_records = reader.read_all(max_records=30)
exporter = EventExporter(all_records)

import tempfile, os
with tempfile.TemporaryDirectory() as tmpdir:
    csv_path  = exporter.to_csv(os.path.join(tmpdir, "events.csv"))
    json_path = exporter.to_json(os.path.join(tmpdir, "events.json"))
    html_path = exporter.to_html(os.path.join(tmpdir, "events.html"), title="System Log Report")
    txt_path  = exporter.to_txt(os.path.join(tmpdir, "events.txt"))

    print(f"  ✅ CSV   → {csv_path}")
    print(f"  ✅ JSON  → {json_path}")
    print(f"  ✅ HTML  → {html_path}")
    print(f"  ✅ TXT   → {txt_path}")
    print(f"\n  (files written to temp dir and cleaned up)\n")

print()

# ── 5. Keyword search ──────────────────────────────────────────────────────
print("=" * 60)
print("Example 5 – Keyword search for 'failed'")
print("=" * 60)

f5 = EventFilter().keyword("failed")
reader5 = EventLogReader("System")
keyword_events = reader5.read_all(event_filter=f5, max_records=100)
print(f"  Found {len(keyword_events)} event(s) mentioning 'failed'.\n")
for e in keyword_events[:3]:
    print(e)