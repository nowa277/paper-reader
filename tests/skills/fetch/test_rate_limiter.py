"""Tests for rate limiter."""

import time
import threading
from skills.fetch.rate_limiter import RateLimiter


class TestRateLimiterInit:
    """Tests for RateLimiter initialization."""

    def test_default_rpm_is_20(self):
        """Default RPM is 20."""
        limiter = RateLimiter()
        assert limiter._rpm == 20

    def test_custom_rpm(self):
        """Custom RPM is respected."""
        limiter = RateLimiter(rpm=10)
        assert limiter._rpm == 10


class TestRateLimiterAcquire:
    """Tests for RateLimiter.acquire()."""

    def test_acquire_returns_without_wait_when_idle(self):
        """Acquire returns immediately when under limit."""
        limiter = RateLimiter(rpm=60, window_seconds=1.0)
        start = time.time()
        limiter.acquire()
        elapsed = time.time() - start
        assert elapsed < 0.1

    def test_context_manager_works(self):
        """Context manager enters and exits correctly."""
        with RateLimiter(rpm=20) as limiter:
            assert limiter is not None

    def test_concurrent_acquire_is_rate_limited(self):
        """Concurrent requests are rate limited to RPM."""
        limiter = RateLimiter(rpm=10, window_seconds=1.0)
        results = []

        def worker():
            start = time.time()
            limiter.acquire()
            results.append(time.time() - start)

        # 20 threads exceeding rpm=10 limit — last 10 must wait
        threads = [threading.Thread(target=worker) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Last few requests should have waited
        assert max(results) > 0.5


class TestRateLimiterState:
    """Tests for internal state tracking."""

    def test_window_start_initialized(self):
        """Window start is initialized on first use."""
        limiter = RateLimiter()
        assert limiter._window_start is not None
