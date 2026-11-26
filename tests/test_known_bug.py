"""The `known_bug` marker in tests/emu/emu_qa_flows.py: an open bug may only count as an expected
failure when the bug check itself fails, never because the set-up broke."""
import contextlib
import io
import unittest

from tests.emu.emu_qa_flows import bug_check, known_bug


def example():
    """Made inside a function so that test discovery does not run it by itself."""
    class Example(unittest.TestCase):
        @known_bug("QA-x")
        def test_bug_shows(self):
            bug_check(False, "the bug")

        @known_bug("QA-x")
        def test_setup_breaks(self):
            self.assertEqual(1, 2, "set-up")
            bug_check(False, "the bug")

        @known_bug("QA-x")
        def test_bug_fixed(self):
            bug_check(True, "the bug")
    return Example


class KnownBugMarker(unittest.TestCase):
    def outcome(self, name):
        result = unittest.TestResult()
        with contextlib.redirect_stderr(io.StringIO()):
            example()(name).run(result)
        return result

    def test_the_bug_check_failing_is_an_expected_failure(self):
        result = self.outcome("test_bug_shows")
        self.assertEqual(len(result.expectedFailures), 1)
        self.assertTrue(result.wasSuccessful())

    def test_a_broken_set_up_fails_the_run(self):
        result = self.outcome("test_setup_breaks")
        self.assertEqual(len(result.unexpectedSuccesses), 1)
        self.assertFalse(result.wasSuccessful())

    def test_a_fixed_bug_fails_the_run_until_the_marker_is_removed(self):
        result = self.outcome("test_bug_fixed")
        self.assertEqual(len(result.unexpectedSuccesses), 1)
        self.assertFalse(result.wasSuccessful())


if __name__ == "__main__":
    unittest.main()
