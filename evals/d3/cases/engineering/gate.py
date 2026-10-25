"""Single-process in-memory rolling quota prototype; Python standard library only."""
from collections import deque
import math

class WindowGate:
    def __init__(self, limit, window):
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise ValueError("limit must be a positive integer")
        if isinstance(window, bool) or not isinstance(window, (int, float)) or not math.isfinite(window) or window <= 0:
            raise ValueError("window must be finite and positive")
        self.limit = limit
        self.window = float(window)
        self._accepted = {}
        self._last = {}

    def allow(self, client, timestamp):
        if not isinstance(client, str) or not client:
            raise ValueError("client must be a nonempty string")
        if isinstance(timestamp, bool) or not isinstance(timestamp, (int, float)) or not math.isfinite(timestamp) or timestamp < 0:
            raise ValueError("timestamp must be finite and nonnegative")
        timestamp = float(timestamp)
        if client in self._last and timestamp < self._last[client]:
            raise ValueError("timestamps must be nondecreasing per client")
        self._last[client] = timestamp
        active = self._accepted.setdefault(client, deque())
        cutoff = timestamp - self.window
        while active and active[0] < cutoff:
            active.popleft()
        if len(active) >= self.limit:
            return False
        active.append(timestamp)
        return True
