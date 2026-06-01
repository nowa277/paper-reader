"""Rate limiter for Jina Reader API calls.

Implements a sliding window rate limiter to respect the 20 RPM limit.
"""

import threading
import time
class RateLimiter:
    """Thread-safe sliding window rate limiter."""

    def __init__(self, rpm: int = 20, window_seconds: float = 60.0):
        """Initialize rate limiter.

        Args:
            rpm: Requests per minute allowed.
            window_seconds: Size of the sliding window in seconds.
        """
        self._rpm = rpm
        self._window_seconds = window_seconds
        self._lock = threading.Lock()
        self._window_start = time.time()
        self._request_times: list[float] = []

    def acquire(self) -> None:
        """Acquire permission to make a request.

        Blocks if the rate limit would be exceeded.
        """
        with self._lock:
            now = time.time()

            # Remove requests outside the window
            cutoff = now - self._window_seconds
            self._request_times = [t for t in self._request_times if t > cutoff]

            if len(self._request_times) >= self._rpm:
                # Need to wait until oldest request exits window
                oldest = self._request_times[0]
                wait_time = oldest + self._window_seconds - now
                if wait_time > 0:
                    time.sleep(wait_time)
                    # Recalculate after wait
                    now = time.time()
                    cutoff = now - self._window_seconds
                    self._request_times = [t for t in self._request_times if t > cutoff]
                    self._window_start = now

            self._request_times.append(now)

    def __enter__(self) -> "RateLimiter":
        self.acquire()
        return self

    def __exit__(self, *args) -> None:
        pass
