"""Emulator test: the arrow has somewhere to point at every stage of the story.

For each story goal after the Boulder Badge the test recreates "everything before this is done"
(using the game's script engine to set the same flags the story would set and hand over the HMs
earned so far), puts the player in the place where the previous goal ended, and checks that the
game picks the right goal and shows an arrow. The route tables come from tools/gen_nav.py; this
proves the game reads them the same way, on the real maps, all the way to the Pokemon League.
"""
import os
import sys
import unittest

from .checkpoints import game_at
from .gba import ROOT
from .maps import MapInfo, location_of

sys.path.insert(0, os.path.join(ROOT, "tools"))
import gen_nav  # noqa: E402

SPEC = gen_nav.load_json(gen_nav.SPEC)
GOALS = SPEC["objectives"]
FLAGS = gen_nav.constants("flags.h", "FLAG_", seed=gen_nav.constants("opponents.h", ""))
VARS = gen_nav.constants("vars.h", "VAR_")
ITEMS = gen_nav.constants("items.h", "ITEM_")
HM_AFTER = {"ss_anne": 339, "safari_surf": 341, "warden": 342}      # HM01 Cut, HM03 Surf, HM04 Strength


def standing_tile(map_name):
    """A walkable tile just inside the map's first door."""
    m = MapInfo(location_of(map_name))
    for x, y, _ in m.warps:
        for dx, dy in ((0, 0), (0, 1), (0, -1), (1, 0), (-1, 0)):
            if m.passable(x + dx, y + dy):
                return x + dx, y + dy
    raise AssertionError(f"no walkable tile beside a door on {map_name}")


class ArrowAtEveryGoal(unittest.TestCase):
    def test_goals_file_matches_the_maps(self):
        """The generator's own check: every goal can be reached from the one before it."""
        old = sys.argv
        sys.argv = ["gen_nav.py", "--check"]
        try:
            self.assertEqual(gen_nav.main(), 0)
        finally:
            sys.argv = old

    def test_arrow_shows_for_every_goal(self):
        first = next(i for i, goal in enumerate(GOALS) if goal["id"] == "misty")
        for i in range(first, len(GOALS)):
            if GOALS[i].get("skipped_by_simple_puzzles"):
                continue                                    # already done on the Little Trainer preset
            with self.subTest(goal=GOALS[i]["id"]):
                g = game_at("route1")
                try:
                    script = []
                    for earlier in GOALS[:i]:
                        done = earlier["done"]
                        if "flag" in done:
                            script += [0x29] + g._u16(FLAGS[done["flag"]])
                        elif "item" in done:
                            script += [0x44] + g._u16(ITEMS[done["item"]]) + g._u16(1)
                        else:
                            script += [0x16] + g._u16(VARS[done["var"]]) + g._u16(done["ge"])
                        if earlier["id"] in HM_AFTER:
                            script += [0x44] + g._u16(HM_AFTER[earlier["id"]]) + g._u16(1)
                    g.run_script(script)
                    previous = GOALS[i - 1]["map"]
                    g.teleport(location_of(previous), *standing_tile(previous))
                    g.run_script(script)        # again: arriving somewhere can reset a local flag (Bill's cottage does)
                    g.frames(90)
                    self.assertEqual(g.nav_goal(), i, "the game picked this goal")
                    self.assertIsNotNone(g.nav_arrow(), f"an arrow is showing in {previous}")
                finally:
                    g.close()


if __name__ == "__main__":
    unittest.main()
