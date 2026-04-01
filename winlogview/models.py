"""
models.py - Data models for Windows Event Log records.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any


# Event Level mapping
EVENT_LEVELS = {
    0: "LogAlways",
    1: "Critical",
    2: "Error",
    3: "Warning",
    4: "Information",
    5: "Verbose",
}

# Event Level colors for terminal display
LEVEL_COLORS = {
    "Critical":    "\033[91m",   # Bright Red
    "Error":       "\033[31m",   # Red
    "Warning":     "\033[93m",   # Yellow
    "Information": "\033[94m",   # Blue
    "Verbose":     "\033[37m",   # Light Gray
    "LogAlways":   "\033[0m",    # Default
}
RESET_COLOR = "\033[0m"


@dataclass
class EventRecord:
    """Represents a single Windows Event Log record."""

    event_id: int
    log_name: str
    source: str
    level: str
    level_id: int
    time_created: datetime
    computer: str
    message: str
    task: Optional[str] = None
    keywords: Optional[str] = None
    record_id: Optional[int] = None
    user_id: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to a dictionary."""
        return {
            "record_id":    self.record_id,
            "event_id":     self.event_id,
            "log_name":     self.log_name,
            "source":       self.source,
            "level":        self.level,
            "level_id":     self.level_id,
            "time_created": self.time_created.isoformat() if self.time_created else None,
            "computer":     self.computer,
            "message":      self.message,
            "task":         self.task,
            "keywords":     self.keywords,
            "user_id":      self.user_id,
            **self.extra,
        }

    def colorized_level(self) -> str:
        """Return level string with ANSI color codes."""
        color = LEVEL_COLORS.get(self.level, "")
        return f"{color}{self.level}{RESET_COLOR}"

    def __str__(self) -> str:
        ts = self.time_created.strftime("%Y-%m-%d %H:%M:%S") if self.time_created else "N/A"
        return (
            f"[{ts}] [{self.colorized_level():>11}] "
            f"EventID={self.event_id} | {self.source} | {self.message[:120]}"
        )