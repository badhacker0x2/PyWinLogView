"""
filter.py - Flexible filtering for Event Log records.
"""

from datetime import datetime
from typing import List, Optional, Set

from .models import EventRecord


class EventFilter:
    """
    Chain-able filter for :class:`~winlogview.models.EventRecord` objects.

    All conditions are combined with AND logic.

    Examples
    --------
    >>> f = EventFilter().level("Error", "Critical").event_id(41, 1001)
    >>> reader.read(event_filter=f)
    """

    def __init__(self) -> None:
        self._levels: Optional[Set[str]] = None
        self._event_ids: Optional[Set[int]] = None
        self._sources: Optional[Set[str]] = None
        self._keywords: Optional[List[str]] = None
        self._after: Optional[datetime] = None
        self._before: Optional[datetime] = None

    # ------------------------------------------------------------------
    # Builder methods
    # ------------------------------------------------------------------

    def level(self, *levels: str) -> "EventFilter":
        """
        Filter by one or more level names.

        Valid values: ``"Critical"``, ``"Error"``, ``"Warning"``,
        ``"Information"``, ``"Verbose"``.
        """
        self._levels = {lvl.capitalize() for lvl in levels}
        return self

    def event_id(self, *ids: int) -> "EventFilter":
        """Filter by one or more Event IDs."""
        self._event_ids = set(ids)
        return self

    def source(self, *sources: str) -> "EventFilter":
        """Filter by event source / provider name (case-insensitive)."""
        self._sources = {s.lower() for s in sources}
        return self

    def keyword(self, *keywords: str) -> "EventFilter":
        """
        Filter records whose message contains **all** of the given keywords
        (case-insensitive).
        """
        self._keywords = [k.lower() for k in keywords]
        return self

    def after(self, dt: datetime) -> "EventFilter":
        """Only include events created **after** *dt*."""
        self._after = dt
        return self

    def before(self, dt: datetime) -> "EventFilter":
        """Only include events created **before** *dt*."""
        self._before = dt
        return self

    def time_range(self, start: datetime, end: datetime) -> "EventFilter":
        """Shortcut for ``.after(start).before(end)``."""
        return self.after(start).before(end)

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def matches(self, record: EventRecord) -> bool:
        """Return ``True`` if *record* passes every active condition."""
        if self._levels and record.level not in self._levels:
            return False

        if self._event_ids and record.event_id not in self._event_ids:
            return False

        if self._sources and record.source.lower() not in self._sources:
            return False

        if self._keywords:
            msg_lower = record.message.lower()
            if not all(kw in msg_lower for kw in self._keywords):
                return False

        if self._after and record.time_created:
            after = self._after
            tc = record.time_created
            # Make both tz-aware or both tz-naive
            if after.tzinfo is None and tc.tzinfo is not None:
                tc = tc.replace(tzinfo=None)
            elif after.tzinfo is not None and tc.tzinfo is None:
                from datetime import timezone
                tc = tc.replace(tzinfo=timezone.utc)
            if tc <= after:
                return False

        if self._before and record.time_created:
            before = self._before
            tc = record.time_created
            if before.tzinfo is None and tc.tzinfo is not None:
                tc = tc.replace(tzinfo=None)
            elif before.tzinfo is not None and tc.tzinfo is None:
                from datetime import timezone
                tc = tc.replace(tzinfo=timezone.utc)
            if tc >= before:
                return False

        return True

    def __repr__(self) -> str:
        parts = []
        if self._levels:
            parts.append(f"levels={self._levels}")
        if self._event_ids:
            parts.append(f"event_ids={self._event_ids}")
        if self._sources:
            parts.append(f"sources={self._sources}")
        if self._keywords:
            parts.append(f"keywords={self._keywords}")
        if self._after:
            parts.append(f"after={self._after}")
        if self._before:
            parts.append(f"before={self._before}")
        return f"EventFilter({', '.join(parts)})"