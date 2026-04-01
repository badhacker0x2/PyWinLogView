"""
reader.py - Core Windows Event Log reader.

Uses the `pywin32` library (win32evtlog / win32evtlogutil) on Windows,
and falls back to a mock/demo mode on non-Windows platforms so the code
can still be imported and tested on Linux / macOS CI runners.
"""

import platform
import logging
from datetime import datetime, timezone
from typing import Iterator, List, Optional

from .models import EventRecord, EVENT_LEVELS
from .filter import EventFilter

logger = logging.getLogger(__name__)

IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    try:
        import win32evtlog
        import win32evtlogutil
        import win32con
        import pywintypes
        _WIN32_AVAILABLE = True
    except ImportError:
        _WIN32_AVAILABLE = False
        logger.warning(
            "pywin32 is not installed. Run `pip install pywin32` to enable "
            "real Event Log access."
        )
else:
    _WIN32_AVAILABLE = False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class EventLogReader:
    """
    Read Windows Event Viewer logs programmatically.

    Parameters
    ----------
    log_name : str
        Name of the Event Log channel, e.g. ``"System"``, ``"Application"``,
        ``"Security"``, or a custom channel like
        ``"Microsoft-Windows-PowerShell/Operational"``.
    server : str, optional
        Remote computer name (``None`` = local machine).
    max_records : int, optional
        Maximum number of records to read per call (``0`` = unlimited).

    Examples
    --------
    >>> reader = EventLogReader("System")
    >>> for event in reader.read(max_records=50):
    ...     print(event)
    """

    def __init__(
        self,
        log_name: str = "System",
        server: Optional[str] = None,
        max_records: int = 0,
    ) -> None:
        self.log_name = log_name
        self.server = server
        self.max_records = max_records

    # ------------------------------------------------------------------
    # Reading
    # ------------------------------------------------------------------

    def read(
        self,
        event_filter: Optional[EventFilter] = None,
        max_records: Optional[int] = None,
    ) -> Iterator[EventRecord]:
        """
        Yield :class:`~winlogview.models.EventRecord` objects.

        Parameters
        ----------
        event_filter : EventFilter, optional
            Pre-built filter to apply while reading.
        max_records : int, optional
            Override the instance-level ``max_records``.
        """
        limit = max_records if max_records is not None else self.max_records

        if _WIN32_AVAILABLE:
            yield from self._read_win32(event_filter, limit)
        else:
            logger.info("Running in DEMO mode (non-Windows / pywin32 missing).")
            yield from self._read_demo(event_filter, limit)

    def read_all(
        self,
        event_filter: Optional[EventFilter] = None,
        max_records: Optional[int] = None,
    ) -> List[EventRecord]:
        """Return all matching records as a list."""
        return list(self.read(event_filter=event_filter, max_records=max_records))

    # ------------------------------------------------------------------
    # Win32 backend
    # ------------------------------------------------------------------

    def _read_win32(
        self,
        event_filter: Optional[EventFilter],
        limit: int,
    ) -> Iterator[EventRecord]:
        flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
        handle = win32evtlog.OpenEventLog(self.server, self.log_name)
        count = 0

        try:
            while True:
                events = win32evtlog.ReadEventLog(handle, flags, 0)
                if not events:
                    break
                for ev in events:
                    record = self._parse_win32_event(ev)
                    if event_filter and not event_filter.matches(record):
                        continue
                    yield record
                    count += 1
                    if limit and count >= limit:
                        return
        finally:
            win32evtlog.CloseEventLog(handle)

    def _parse_win32_event(self, ev) -> EventRecord:
        """Convert a raw win32evtlog event object to an EventRecord."""
        level_id = ev.EventType  # 1=Error, 2=Warning, 4=Info, 8=Audit success, 16=Audit failure
        # Map win32 type to standard level
        _win32_level_map = {
            win32evtlog.EVENTLOG_ERROR_TYPE:          (2, "Error"),
            win32evtlog.EVENTLOG_WARNING_TYPE:        (3, "Warning"),
            win32evtlog.EVENTLOG_INFORMATION_TYPE:    (4, "Information"),
            win32evtlog.EVENTLOG_AUDIT_SUCCESS:       (4, "AuditSuccess"),
            win32evtlog.EVENTLOG_AUDIT_FAILURE:       (2, "AuditFailure"),
        }
        lid, lname = _win32_level_map.get(ev.EventType, (0, "Unknown"))

        try:
            message = win32evtlogutil.SafeFormatMessage(ev, self.log_name)
        except Exception:
            message = " | ".join(ev.StringInserts or [])

        time_created = None
        if ev.TimeGenerated:
            try:
                time_created = datetime.fromtimestamp(
                    int(ev.TimeGenerated), tz=timezone.utc
                )
            except Exception:
                pass

        return EventRecord(
            event_id=ev.EventID & 0xFFFF,
            log_name=self.log_name,
            source=ev.SourceName,
            level=lname,
            level_id=lid,
            time_created=time_created,
            computer=ev.ComputerName,
            message=message.strip() if message else "",
            record_id=ev.RecordNumber,
        )

    # ------------------------------------------------------------------
    # Demo / mock backend (cross-platform)
    # ------------------------------------------------------------------

    def _read_demo(
        self,
        event_filter: Optional[EventFilter],
        limit: int,
    ) -> Iterator[EventRecord]:
        """Yield realistic-looking fake events for testing on non-Windows."""
        import random

        samples = [
            (41,  "Kernel-Power",        2, "Error",       "The system has rebooted without cleanly shutting down first."),
            (7036, "Service Control Manager", 4, "Information", "The Windows Update service entered the running state."),
            (1014, "DNS Client Events",   3, "Warning",     "Name resolution for the name timed out after none of the configured DNS servers responded."),
            (6005, "EventLog",            4, "Information", "The Event log service was started."),
            (4625, "Security",            2, "Error",       "An account failed to log on. Logon Type: 3"),
            (4624, "Security",            4, "Information", "An account was successfully logged on."),
            (7023, "Service Control Manager", 2, "Error",   "The Print Spooler service terminated with the following error."),
            (1001, "Windows Error Reporting", 4, "Information", "Fault bucket, type 0. Event Name: APPCRASH. Response: Not available."),
            (10016, "DistributedCOM",     3, "Warning",     "The machine-default permission settings do not grant Local Activation permission."),
            (51,  "Disk",                 3, "Warning",     "An error was detected on device \\Device\\Harddisk0 during a paging operation."),
        ]

        now = datetime.now(tz=timezone.utc)
        count = 0
        for i, (eid, src, lid, lvl, msg) in enumerate(samples * 5):
            from datetime import timedelta
            record = EventRecord(
                event_id=eid,
                log_name=self.log_name,
                source=src,
                level=lvl,
                level_id=lid,
                time_created=now - timedelta(minutes=random.randint(1, 1440)),
                computer="DESKTOP-DEMO",
                message=msg,
                record_id=1000 + i,
            )
            if event_filter and not event_filter.matches(record):
                continue
            yield record
            count += 1
            if limit and count >= limit:
                return