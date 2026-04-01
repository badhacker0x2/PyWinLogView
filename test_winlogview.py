"""
tests/test_winlogview.py - Unit tests for WinLogView (cross-platform).
"""

import pytest
from datetime import datetime, timezone, timedelta

from winlogview.models import EventRecord
from winlogview.filter import EventFilter
from winlogview.reader import EventLogReader
from winlogview.exporter import EventExporter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_record(**kwargs) -> EventRecord:
    defaults = dict(
        event_id=1000,
        log_name="System",
        source="TestSource",
        level="Information",
        level_id=4,
        time_created=datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
        computer="TEST-PC",
        message="Test event message",
    )
    defaults.update(kwargs)
    return EventRecord(**defaults)


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class TestEventRecord:
    def test_to_dict_keys(self):
        r = make_record()
        d = r.to_dict()
        assert "event_id" in d
        assert "level" in d
        assert "message" in d

    def test_to_dict_time_is_iso(self):
        r = make_record()
        assert "T" in r.to_dict()["time_created"]  # ISO format

    def test_str_contains_event_id(self):
        r = make_record(event_id=9999)
        assert "9999" in str(r)

    def test_colorized_level_contains_level_name(self):
        r = make_record(level="Error")
        assert "Error" in r.colorized_level()


# ---------------------------------------------------------------------------
# Filter tests
# ---------------------------------------------------------------------------

class TestEventFilter:
    def test_no_conditions_matches_all(self):
        f = EventFilter()
        assert f.matches(make_record())

    def test_level_match(self):
        f = EventFilter().level("Error")
        assert f.matches(make_record(level="Error"))
        assert not f.matches(make_record(level="Information"))

    def test_multiple_levels(self):
        f = EventFilter().level("Error", "Warning")
        assert f.matches(make_record(level="Error"))
        assert f.matches(make_record(level="Warning"))
        assert not f.matches(make_record(level="Information"))

    def test_event_id_match(self):
        f = EventFilter().event_id(41, 7036)
        assert f.matches(make_record(event_id=41))
        assert not f.matches(make_record(event_id=999))

    def test_source_case_insensitive(self):
        f = EventFilter().source("kernel-power")
        assert f.matches(make_record(source="Kernel-Power"))
        assert not f.matches(make_record(source="DNS Client"))

    def test_keyword_match(self):
        f = EventFilter().keyword("rebooted")
        assert f.matches(make_record(message="The system has rebooted cleanly."))
        assert not f.matches(make_record(message="Normal startup."))

    def test_multiple_keywords_all_must_match(self):
        f = EventFilter().keyword("system", "rebooted")
        assert f.matches(make_record(message="The system has rebooted."))
        assert not f.matches(make_record(message="The system started."))

    def test_after_filter(self):
        cutoff = datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
        f = EventFilter().after(cutoff)
        assert f.matches(make_record(time_created=datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)))
        assert not f.matches(make_record(time_created=datetime(2024, 6, 1, 8, 0, 0, tzinfo=timezone.utc)))

    def test_before_filter(self):
        cutoff = datetime(2024, 6, 1, 14, 0, 0, tzinfo=timezone.utc)
        f = EventFilter().before(cutoff)
        assert f.matches(make_record(time_created=datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)))
        assert not f.matches(make_record(time_created=datetime(2024, 6, 1, 16, 0, 0, tzinfo=timezone.utc)))

    def test_time_range(self):
        start = datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
        end   = datetime(2024, 6, 1, 14, 0, 0, tzinfo=timezone.utc)
        f = EventFilter().time_range(start, end)
        assert f.matches(make_record(time_created=datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)))
        assert not f.matches(make_record(time_created=datetime(2024, 6, 1, 8, 0, 0, tzinfo=timezone.utc)))

    def test_combined_filters(self):
        f = EventFilter().level("Error").event_id(41)
        assert f.matches(make_record(level="Error", event_id=41))
        assert not f.matches(make_record(level="Warning", event_id=41))
        assert not f.matches(make_record(level="Error", event_id=7036))

    def test_repr(self):
        f = EventFilter().level("Error").event_id(41)
        assert "EventFilter" in repr(f)


# ---------------------------------------------------------------------------
# Reader tests (demo mode)
# ---------------------------------------------------------------------------

class TestEventLogReader:
    def test_read_returns_records(self):
        reader = EventLogReader("System")
        records = reader.read_all(max_records=5)
        assert len(records) <= 5
        assert all(isinstance(r, EventRecord) for r in records)

    def test_read_with_filter(self):
        reader = EventLogReader("System")
        f = EventFilter().level("Error")
        records = reader.read_all(event_filter=f, max_records=50)
        assert all(r.level == "Error" for r in records)

    def test_read_limit_respected(self):
        reader = EventLogReader("System")
        records = reader.read_all(max_records=3)
        assert len(records) <= 3

    def test_iterator_protocol(self):
        reader = EventLogReader("Application")
        it = reader.read(max_records=2)
        r = next(it)
        assert isinstance(r, EventRecord)


# ---------------------------------------------------------------------------
# Exporter tests
# ---------------------------------------------------------------------------

class TestEventExporter:
    def setup_method(self):
        self.records = [
            make_record(event_id=100, level="Error",       message="Disk failure detected"),
            make_record(event_id=200, level="Warning",     message="Memory usage high"),
            make_record(event_id=300, level="Information", message="Service started"),
        ]
        self.exporter = EventExporter(self.records)

    def test_to_csv(self, tmp_path):
        path = str(tmp_path / "out.csv")
        result = self.exporter.to_csv(path)
        assert result.endswith("out.csv")
        import csv
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 3
        assert rows[0]["level"] == "Error"

    def test_to_json(self, tmp_path):
        path = str(tmp_path / "out.json")
        self.exporter.to_json(path)
        import json
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) == 3
        assert data[0]["event_id"] == 100

    def test_to_txt(self, tmp_path):
        path = str(tmp_path / "out.txt")
        self.exporter.to_txt(path)
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "Disk failure" in content
        assert "Service started" in content

    def test_to_html(self, tmp_path):
        path = str(tmp_path / "out.html")
        self.exporter.to_html(path, title="Test Report")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "Test Report" in content
        assert "Disk failure" in content
        assert "<table" in content

    def test_empty_records(self, tmp_path):
        exp = EventExporter([])
        path = str(tmp_path / "empty.json")
        exp.to_json(path)
        import json
        with open(path) as f:
            assert json.load(f) == []