"""Timer context manager for measuring and logging elapsed time."""
import time
import logging
from typing import Optional


class Timer:
    """Context manager that measures elapsed time and optionally logs it."""

    def __init__(self, label: str = "operation", logger: Optional[logging.Logger] = None):
        self.label = label
        self.logger = logger
        self.elapsed: float = 0.0
        self._start: float = 0.0

    def __enter__(self) -> "Timer":
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args) -> None:
        self.elapsed = time.perf_counter() - self._start
        msg = f"{self.label} completed in {self.elapsed:.3f}s"
        if self.logger:
            self.logger.debug(msg)
        else:
            logging.getLogger("timer").debug(msg)

    def __str__(self) -> str:
        return f"{self.label}: {self.elapsed:.3f}s"
