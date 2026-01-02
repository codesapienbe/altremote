"""
Log Service

Centralized logging and notification system.
Collects debug logs, errors, and notifications in memory.
"""

from datetime import datetime
from typing import List, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

from kivy.event import EventDispatcher
from kivy.properties import StringProperty, ListProperty, NumericProperty
from kivy.clock import Clock


class LogLevel(Enum):
    """Log severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


@dataclass
class LogEntry:
    """A single log entry."""
    timestamp: datetime
    level: LogLevel
    message: str
    source: str = ""

    def __str__(self):
        time_str = self.timestamp.strftime("%H:%M:%S")
        return f"[{time_str}] [{self.level.value.upper()}] {self.message}"


class LogService(EventDispatcher):
    """
    Centralized logging service.

    Features:
    - Collects all logs in memory (up to max_entries)
    - Provides the latest notification for display
    - Dispatches events when new logs arrive
    - Color-coded by log level
    """

    # Current notification to display in footer
    current_message = StringProperty("")
    current_level = StringProperty("info")
    unread_count = NumericProperty(0)

    def __init__(self, max_entries: int = 500, **kwargs):
        super().__init__(**kwargs)

        self._logs: deque = deque(maxlen=max_entries)
        self._callbacks: List[Callable] = []
        self._clear_timer = None

    def log(self, message: str, level: LogLevel = LogLevel.INFO, source: str = ""):
        """Add a log entry."""
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            message=message,
            source=source
        )
        self._logs.append(entry)

        # Update current notification
        self.current_message = message
        self.current_level = level.value
        self.unread_count += 1

        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(entry)
            except Exception:
                pass

        # Auto-clear notification after delay (except errors)
        if self._clear_timer:
            self._clear_timer.cancel()

        if level != LogLevel.ERROR:
            self._clear_timer = Clock.schedule_once(
                lambda dt: self._clear_current(),
                5.0  # Clear after 5 seconds
            )

        # Print to console as well
        print(str(entry))

    def _clear_current(self):
        """Clear the current notification."""
        self.current_message = ""
        self._clear_timer = None

    # Convenience methods
    def debug(self, message: str, source: str = ""):
        """Log a debug message."""
        self.log(message, LogLevel.DEBUG, source)

    def info(self, message: str, source: str = ""):
        """Log an info message."""
        self.log(message, LogLevel.INFO, source)

    def warning(self, message: str, source: str = ""):
        """Log a warning message."""
        self.log(message, LogLevel.WARNING, source)

    def error(self, message: str, source: str = ""):
        """Log an error message."""
        self.log(message, LogLevel.ERROR, source)

    def success(self, message: str, source: str = ""):
        """Log a success message."""
        self.log(message, LogLevel.SUCCESS, source)

    def get_logs(self, level: Optional[LogLevel] = None) -> List[LogEntry]:
        """Get all logs, optionally filtered by level."""
        if level is None:
            return list(self._logs)
        return [log for log in self._logs if log.level == level]

    def get_recent(self, count: int = 20) -> List[LogEntry]:
        """Get the most recent logs."""
        logs = list(self._logs)
        return logs[-count:] if len(logs) > count else logs

    def clear_logs(self):
        """Clear all logs."""
        self._logs.clear()
        self.unread_count = 0

    def mark_read(self):
        """Mark all notifications as read."""
        self.unread_count = 0

    def register_callback(self, callback: Callable):
        """Register a callback for new log entries."""
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def unregister_callback(self, callback: Callable):
        """Unregister a callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    @staticmethod
    def get_level_color(level: str) -> tuple:
        """Get color for a log level."""
        colors = {
            'debug': (0.5, 0.5, 0.5, 1),      # Gray
            'info': (0.7, 0.7, 0.7, 1),       # Light gray
            'warning': (1.0, 0.8, 0.2, 1),    # Yellow
            'error': (1.0, 0.3, 0.3, 1),      # Red
            'success': (0.3, 0.8, 0.3, 1),    # Green
        }
        return colors.get(level, (0.7, 0.7, 0.7, 1))
