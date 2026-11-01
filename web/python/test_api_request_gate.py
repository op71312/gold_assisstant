import unittest
from types import SimpleNamespace
from unittest.mock import patch

from web.python import gaib_pipeline


class ApiRequestGateTests(unittest.TestCase):
    def test_retry_after_wait_is_capped(self):
        error = RuntimeError("rate limited")
        error.response = SimpleNamespace(
            status_code=429,
            headers={"Retry-After": "1200"},
        )
        gate = gaib_pipeline.ApiRequestGate("test", 1)

        with patch.object(gaib_pipeline.time, "monotonic", return_value=100):
            delay = gate.defer_after_error(error, 0)

        self.assertEqual(delay, gaib_pipeline.API_RETRY_MAX_WAIT_SECONDS)
        self.assertEqual(
            gate.blocked_until,
            100 + gaib_pipeline.API_RETRY_MAX_WAIT_SECONDS,
        )

    def test_short_retry_after_is_respected(self):
        error = RuntimeError("rate limited")
        error.response = SimpleNamespace(
            status_code=429,
            headers={"Retry-After": "12"},
        )
        gate = gaib_pipeline.ApiRequestGate("test", 1)

        with patch.object(gaib_pipeline.time, "monotonic", return_value=100):
            delay = gate.defer_after_error(error, 0)

        self.assertEqual(delay, 12)
        self.assertEqual(gate.blocked_until, 112)


if __name__ == "__main__":
    unittest.main()
