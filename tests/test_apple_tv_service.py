"""
Tests for the AppleTVService async execution model.

The service must run pyatv coroutines on a background event loop thread so
that network operations never block the Kivy main thread.
"""

import os
import threading
import time
import unittest

os.environ.setdefault('KIVY_NO_ARGS', '1')

from src.services.apple_tv_service import AppleTVService


def make_service():
    """Create a service instance without touching credential storage."""
    service = AppleTVService.__new__(AppleTVService)
    service._log_service = None
    service._atv = None
    service._remote = None
    service._loop = None
    service._loop_thread = None
    service._setup_event_loop()
    return service


class TestAsyncExecution(unittest.TestCase):
    """Tests for the background event loop."""

    def setUp(self):
        self.service = make_service()

    def tearDown(self):
        if self.service._loop.is_running():
            self.service._loop.call_soon_threadsafe(self.service._loop.stop)
        self.service._loop_thread.join(timeout=2.0)

    def test_loop_runs_on_background_thread(self):
        """The event loop thread must not be the caller's thread."""
        self.assertTrue(self.service._loop.is_running())
        self.assertIsNot(self.service._loop_thread, threading.current_thread())
        self.assertTrue(self.service._loop_thread.daemon)

    def test_run_async_does_not_block_caller(self):
        """Submitting a slow coroutine must return immediately."""
        import asyncio

        done = threading.Event()

        async def slow():
            await asyncio.sleep(0.5)
            done.set()

        start = time.monotonic()
        self.service._run_async(slow(), timeout=5.0)
        elapsed = time.monotonic() - start

        self.assertLess(elapsed, 0.2, "caller thread was blocked")
        self.assertTrue(done.wait(timeout=2.0), "coroutine never completed")

    def test_run_async_executes_on_loop_thread(self):
        """The coroutine body must run on the background loop thread."""
        ran_on = {}
        done = threading.Event()

        async def probe():
            ran_on['thread'] = threading.current_thread()
            done.set()

        self.service._run_async(probe(), timeout=5.0)
        self.assertTrue(done.wait(timeout=2.0))
        self.assertIs(ran_on['thread'], self.service._loop_thread)

    def test_run_async_swallows_timeout(self):
        """A coroutine exceeding its timeout must not raise or hang."""
        import asyncio

        cancelled = threading.Event()

        async def too_slow():
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                cancelled.set()
                raise

        self.service._run_async(too_slow(), timeout=0.1)
        self.assertTrue(cancelled.wait(timeout=2.0), "coroutine was not cancelled")

    def test_run_async_swallows_exceptions(self):
        """Exceptions inside coroutines must be logged, not propagated."""
        raised = threading.Event()

        async def boom():
            raised.set()
            raise RuntimeError("expected failure")

        self.service._run_async(boom(), timeout=5.0)
        self.assertTrue(raised.wait(timeout=2.0))
        # Give the wrapper a moment to handle the exception
        time.sleep(0.1)
        self.assertTrue(self.service._loop.is_running(), "loop died on exception")

    def test_shutdown_stops_loop_thread(self):
        """shutdown() must stop the loop and join the thread."""
        self.service.is_connected = False
        self.service.connection_state = ""
        self.service.current_device_name = ""
        self.service.shutdown()
        self.assertFalse(self.service._loop.is_running())
        self.assertFalse(self.service._loop_thread.is_alive())


if __name__ == '__main__':
    unittest.main()
