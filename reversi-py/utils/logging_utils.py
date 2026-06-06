"""Utilities for logging: a throttling filter to suppress rapid duplicate messages.

This provides ThrottlingFilter which can be attached to a logger to drop
identical messages that occur more frequently than a configured interval.
"""

import time
import threading
import logging

__all__ = ["ThrottlingFilter"]


class ThrottlingFilter(logging.Filter):
    """A logging.Filter that throttles identical log messages.

    It suppresses repeated messages (same logger name, level and formatted
    message) that occur within `interval_seconds` of the previous occurrence.
    """

    def __init__(self, name: str = "", interval_seconds: float = 1.0):
        super().__init__(name)
        self.interval_seconds = float(interval_seconds)
        # map: (logger_name, levelno, message) -> last_timestamp
        self._last: dict[tuple[str, int, str], float] = {}
        self._lock = threading.Lock()

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:
            # fallback to raw msg if formatting fails
            message = str(record.msg)

        key = (record.name, record.levelno, message)
        now = time.time()
        with self._lock:
            last = self._last.get(key)
            if last is None or (now - last) >= self.interval_seconds:
                self._last[key] = now
                return True
            # suppress this record (it's too soon)
            return False
