"""Catching on Little Trainer: easier than Junior, but no longer a certainty.

Jake's rule (2026-11-25): Classic is the original game, Junior is two and a half times easier,
and Little Trainer is twice as easy as Junior. So a ball on Little Trainer has five times the
original odds, and the original shape is kept: common Pokemon are caught almost every time, rare
ones break free more often than not, and weakening one first helps. A miss costs nothing: the
free ball is never used up and the Pokemon stays to be tried again.
"""
import os
import tempfile
import unittest

from . import story
from .checkpoints import game_at

THROWS = 40
VAR_LT_DIFFICULTY, CLASSIC = 0x4029, 2
POKE_BALL = 4
ONIX = 95           # hard to catch: about six balls in a hundred catch a healthy one in the original game


class Catching(unittest.TestCase):
    def setUp(self):
        self.g = game_at("route1")
        self.state = os.path.join(tempfile.mkdtemp(prefix="lt-catch-"), "wild.ss")

    def tearDown(self):
        self.g.close()
        if os.path.exists(self.state):
            os.remove(self.state)
        os.rmdir(os.path.dirname(self.state))

    def meet(self, species=None, level=5):
        """A wild battle: a chosen Pokemon, or whatever lives on Route 1 (Pidgey or Rattata, the
        easiest there are to catch)."""
        g = self.g
        if species:
            g.start_wild_battle(species, level)
        else:
            story.find_wild_battle(g)
        self.assertTrue(g.wait_action_menu())
        if species:
            self.assertEqual(g.battle_mon(1)["species"], species)

    def throws_from_the_same_moment(self, count, throw=None):
        """Throw one ball `count` times at the same wild Pokemon, each time from the same saved
        moment but a few frames later, so every throw gets different luck. Yields caught or not."""
        g = self.g
        g.save_state(self.state)
        for i in range(count):
            g.load_state(self.state)
            g.frames(2 + 3 * i)
            yield (throw or g.throw_ball)()

    def test_a_common_pokemon_is_caught_nearly_every_time(self):
        self.meet()
        caught = sum(self.throws_from_the_same_moment(20))
        self.assertGreaterEqual(caught, 19, f"{caught} of 20 balls caught a Route 1 Pokemon")

    def test_a_rare_pokemon_breaks_free_more_often_than_not_and_weakening_it_helps(self):
        g = self.g
        self.meet(ONIX)
        healthy = sum(self.throws_from_the_same_moment(THROWS))
        g.load_state(self.state)
        g.set_battle_hp(1, 1)                       # set-up: nearly beaten
        weakened = sum(self.throws_from_the_same_moment(20))
        # Worked out from the game's own sum: 34% at full health, all but certain when nearly
        # beaten. The limits for the healthy one are about four standard deviations either side.
        self.assertGreaterEqual(healthy, 3, f"{healthy} of {THROWS} caught a healthy Onix: Little Trainer should be far kinder than the original 6%")
        self.assertLessEqual(healthy, 26, f"{healthy} of {THROWS} caught a healthy Onix: it should usually break free")
        self.assertGreaterEqual(weakened, 19, f"{weakened} of 20 caught a nearly beaten Onix: weakening it first should all but settle it")

    def test_a_miss_costs_nothing_and_the_next_ball_can_still_catch(self):
        g = self.g
        self.meet(ONIX)
        before = g.battle_mon(1)
        for caught in self.throws_from_the_same_moment(THROWS):
            if not caught:
                break
        else:
            self.fail(f"no miss in {THROWS} throws")
        self.assertTrue(g.at_action_menu(), "after a miss the buttons are back")
        after = g.battle_mon(1)
        self.assertEqual(after["species"], before["species"], "the wild Pokemon is still there")
        self.assertEqual(after["hp"], before["hp"], "and no weaker or stronger for it")
        self.assertEqual(g.party_count(), 1)
        g.shot("catch-broke-free")
        g.set_battle_hp(0, g.battle_mon(0)["max_hp"])   # set-up: the test's Pokemon lasts as long as it takes
        throws = g.catch()                              # the bag is still empty: the free ball never runs out
        g.advance_text(g.free_to_move, what="control after catching")
        self.assertEqual(g.party_count(), 2, f"caught after {throws} more throw(s)")

    def test_classic_keeps_the_original_odds(self):
        """A healthy Route 1 Pokemon breaks out of a plain Poke Ball more often than not in the
        original game (about one catch in three)."""
        g = self.g
        g.set_var(VAR_LT_DIFFICULTY, CLASSIC)
        g.give_item(POKE_BALL, 99)                  # Classic has no free ball
        self.meet()
        caught = sum(self.throws_from_the_same_moment(THROWS, g.throw_ball_from_bag))
        self.assertLessEqual(caught, 26, f"{caught} of {THROWS} caught on Classic: that is not the original game's odds")
        self.assertGreaterEqual(caught, 3, f"{caught} of {THROWS} caught on Classic")


if __name__ == "__main__":
    unittest.main()
