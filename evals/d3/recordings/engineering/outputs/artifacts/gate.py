"""Single-process, single-thread, in-memory rolling quota component.

Caller supplies time. Accepted requests occupy (timestamp - window, timestamp].
All validation completes before client state changes. No external I/O.
"""
from collections import deque
from fractions import Fraction
import math


def _number(value, *, positive, label):
    """Validate int/float without converting arbitrary-size integers to float."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{label} must be an int or float, excluding bool')
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f'{label} must be finite')
    if value <= 0 if positive else value < 0:
        raise ValueError(f'{label} must be positive' if positive else f'{label} must be nonnegative')
    # Fraction(float) preserves the precise binary value supplied by the caller.
    return Fraction(value)


class WindowGate:
    def __init__(self, limit, window):
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise ValueError('limit must be a positive integer')
        width = _number(window, positive=True, label='window')
        self.limit = limit
        self.window = window
        self._width = width
        self._accepted = {}
        self._last = {}

    def allow(self, client, timestamp):
        if not isinstance(client, str) or not client:
            raise ValueError('client must be a nonempty string')
        instant = _number(timestamp, positive=False, label='timestamp')
        if client in self._last and instant < self._last[client]:
            raise ValueError('timestamps must be nondecreasing per client')
        # All invalid-input paths have returned before any state mutation.
        self._last[client] = instant
        active = self._accepted.setdefault(client, deque())
        cutoff = instant - self._width
        while active and active[0] <= cutoff:
            active.popleft()
        if len(active) >= self.limit:
            return False
        active.append(instant)
        return True
