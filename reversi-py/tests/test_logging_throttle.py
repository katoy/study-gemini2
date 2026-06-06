# tests/test_logging_throttle.py
import logging
import unittest
from unittest.mock import patch

from utils.logging_utils import ThrottlingFilter


class TestThrottlingFilter(unittest.TestCase):
    def test_throttle_allows_then_blocks_then_allows(self):
        f = ThrottlingFilter(interval_seconds=2.0)
        with patch('utils.logging_utils.time.time') as mock_time:
            mock_time.return_value = 100.0
            r1 = logging.LogRecord('test', logging.INFO, __file__, 1, 'hello %s', ('world',), None)
            self.assertTrue(f.filter(r1))
            mock_time.return_value = 101.0
            r2 = logging.LogRecord('test', logging.INFO, __file__, 2, 'hello %s', ('world',), None)
            self.assertFalse(f.filter(r2))
            mock_time.return_value = 103.0
            r3 = logging.LogRecord('test', logging.INFO, __file__, 3, 'hello %s', ('world',), None)
            self.assertTrue(f.filter(r3))

    def test_different_messages_not_throttled(self):
        f = ThrottlingFilter(interval_seconds=1.0)
        with patch('utils.logging_utils.time.time') as mock_time:
            mock_time.return_value = 100.0
            r1 = logging.LogRecord('test', logging.INFO, __file__, 1, 'a', (), None)
            r2 = logging.LogRecord('test', logging.INFO, __file__, 2, 'b', (), None)
            self.assertTrue(f.filter(r1))
            self.assertTrue(f.filter(r2))

    def test_different_levels_are_separate(self):
        f = ThrottlingFilter(interval_seconds=1.0)
        with patch('utils.logging_utils.time.time') as mock_time:
            mock_time.return_value = 100.0
            r_info = logging.LogRecord('test', logging.INFO, __file__, 1, 'same', (), None)
            r_warning = logging.LogRecord('test', logging.WARNING, __file__, 2, 'same', (), None)
            self.assertTrue(f.filter(r_info))
            self.assertTrue(f.filter(r_warning))


if __name__ == '__main__':
    unittest.main()
