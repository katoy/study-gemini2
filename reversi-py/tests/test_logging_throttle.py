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

    def test_handles_formatting_error_and_fallback(self):
        f = ThrottlingFilter(interval_seconds=1.0)
        with patch('utils.logging_utils.time.time') as mock_time:
            mock_time.return_value = 100.0
            # Create a LogRecord whose getMessage will raise due to format mismatch
            r = logging.LogRecord('test', logging.INFO, __file__, 1, 'bad %s %s', ('one',), None)
            # First call should pass (no prior message)
            self.assertTrue(f.filter(r))
            # Immediate second call should be throttled
            mock_time.return_value = 100.5
            self.assertFalse(f.filter(r))

    def test_max_entries_evicts_expired_entries(self):
        """上限到達時、期限切れエントリが掃除され新エントリが登録される"""
        f = ThrottlingFilter(interval_seconds=1.0, max_entries=2)
        with patch('utils.logging_utils.time.time') as mock_time:
            mock_time.return_value = 100.0
            r1 = logging.LogRecord('test', logging.INFO, __file__, 1, 'a', (), None)
            r2 = logging.LogRecord('test', logging.INFO, __file__, 2, 'b', (), None)
            self.assertTrue(f.filter(r1))
            self.assertTrue(f.filter(r2))
            self.assertEqual(len(f._last), 2)

            # 時間を進めて既存エントリを期限切れにしてから 3 件目を投入
            mock_time.return_value = 102.0
            r3 = logging.LogRecord('test', logging.INFO, __file__, 3, 'c', (), None)
            self.assertTrue(f.filter(r3))
            # 期限切れの a / b は掃除され、c のみ残る
            self.assertEqual(len(f._last), 1)

    def test_max_entries_clears_all_when_no_expired_entries(self):
        """上限到達時に全エントリが期限内なら全消去して新エントリを登録する"""
        f = ThrottlingFilter(interval_seconds=10.0, max_entries=2)
        with patch('utils.logging_utils.time.time') as mock_time:
            mock_time.return_value = 100.0
            r1 = logging.LogRecord('test', logging.INFO, __file__, 1, 'a', (), None)
            r2 = logging.LogRecord('test', logging.INFO, __file__, 2, 'b', (), None)
            self.assertTrue(f.filter(r1))
            self.assertTrue(f.filter(r2))

            # 全エントリが期限内のまま 3 件目を投入 → 全消去して登録
            mock_time.return_value = 100.5
            r3 = logging.LogRecord('test', logging.INFO, __file__, 3, 'c', (), None)
            self.assertTrue(f.filter(r3))
            self.assertEqual(len(f._last), 1)


if __name__ == '__main__':
    unittest.main()
