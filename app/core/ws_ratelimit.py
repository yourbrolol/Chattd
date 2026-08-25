import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple


class SlidingWindowLimiter:
    """In-process sliding-window rate limiter keyed by arbitrary strings
    (e.g. f"ws-connect:{username}"). Suitable for single-worker deployments."""

    def __init__(self, max_events: int, per_seconds: float):
        self.max_events = max_events
        self.per_seconds = per_seconds
        self._events: Dict[str, Deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        window = self._events[key]
        cutoff = now - self.per_seconds
        while window and window[0] <= cutoff:
            window.popleft()
        if len(window) >= self.max_events:
            return False
        window.append(now)
        return True

