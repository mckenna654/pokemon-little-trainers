"""The shrinker in tests/emu/qa_property.py, on a made-up failure (no emulator)."""
import unittest
from unittest import mock

from tests.emu import qa_property


def fake_run(needed, other_failure=None):
    """A stand-in for run_one: fails 'lost' when every action in `needed` is present."""
    def run_one(task, actions):
        if other_failure and other_failure in actions:
            return False, "stuck: somewhere else", actions
        if all(a in actions for a in needed):
            return False, "1 Pokemon lost", actions
        return True, {}, actions
    return run_one


class Shrink(unittest.TestCase):
    def test_finds_the_two_actions_that_matter(self):
        actions = [("press", ("UP", 3, 12))] * 20 + [("press", ("B", 3, 12))] + [("step", "LEFT")] * 30 + [("press", ("A", 3, 12))]
        needed = [("press", ("B", 3, 12)), ("press", ("A", 3, 12))]
        with mock.patch.object(qa_property, "run_one", fake_run(needed)):
            small, runs = qa_property.shrink({}, actions, "1 Pokemon lost")
        self.assertEqual(sorted(small), sorted(needed))
        self.assertLessEqual(runs, 150)

    def test_never_slides_to_a_different_failure(self):
        needed = [("press", ("B", 3, 12))]
        decoy = ("step", "DOWN")
        actions = [decoy] + [("step", "LEFT")] * 10 + needed
        with mock.patch.object(qa_property, "run_one", fake_run(needed, other_failure=decoy)):
            small, _ = qa_property.shrink({}, actions, "1 Pokemon lost")
        ok, detail, _ = fake_run(needed)({}, small)
        self.assertFalse(ok)
        self.assertEqual(detail, "1 Pokemon lost")

    def test_stops_at_its_budget(self):
        actions = [("step", "LEFT")] * 400 + [("press", ("B", 3, 12))]
        with mock.patch.object(qa_property, "run_one", fake_run([("press", ("B", 3, 12))])):
            _, runs = qa_property.shrink({}, actions, "1 Pokemon lost", budget=10)
        self.assertLessEqual(runs, 10)


if __name__ == "__main__":
    unittest.main()
