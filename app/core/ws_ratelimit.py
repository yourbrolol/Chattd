import time
from collections import defaultdict, deque
from typing import Deque, Dict, Optional


class SlidingWindowLimiter:
    """In-process sliding-window rate limiter keyed by arbitrary strings
    (e.g. f"ws-connect:{username}"). Suitable for single-worker deployments."""

    def __init__(self, max_events: int, per_seconds: float):
        self.max_events = max_events
        self.per_seconds = per_seconds
        self._events: Dict[str, Deque[float]] = defaultdict(deque)

    def _cleanup(self, key: str, now: float) -> None:
        window = self._events[key]
        cutoff = now - self.per_seconds
        while window and window[0] <= cutoff:
            window.popleft()

    def quota_left(self, key: str) -> int:
        now = time.monotonic()
        self._cleanup(key, now)
        return max(0, self.max_events - len(self._events[key]))

    def retry_after(self, key: str) -> float:
        """Return seconds until the next event is allowed, or 0 if allowed now."""
        now = time.monotonic()
        self._cleanup(key, now)
        window = self._events[key]
        if len(window) < self.max_events:
            return 0.0
        oldest = window[0]
        return max(0.0, oldest + self.per_seconds - now)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        self._cleanup(key, now)
        window = self._events[key]
        if len(window) >= self.max_events:
            return False
        window.append(now)
        return True

    def status(self, key: str) -> dict:
        """Return full rate-limit status for a key."""
        now = time.monotonic()
        self._cleanup(key, now)
        window = self._events[key]
        remaining = max(0, self.max_events - len(window))
        retry = 0.0
        if remaining == 0 and window:
            retry = max(0.0, window[0] + self.per_seconds - now)
        return {
            "limit": self.max_events,
            "remaining": remaining,
            "reset": round(retry, 2),
        }
