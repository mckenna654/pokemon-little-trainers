"""Emulator test: the whole game, played the way a small child would play it.

One continuous play from a new game. The test player knows nothing about Pokemon: it walks where
the on-screen arrow points and presses A when there is no arrow, when something is in the way,
and in battles (the battle cursor starts on the recommended attack). No other button is used,
nothing is read, and nothing is set up behind the game's back. It must collect all eight badges
and enter the Hall of Fame.

It takes several minutes, so it only runs when asked for:
    scripts/test.sh full            (or LT_FULL_RUN=1 with unittest)
"""
import os
import sys
import time
import unittest

from .firered import FireRed
from .gba import EmulatorError
from .maps import map_name

FLAG_BADGE01_GET, FLAG_SYS_GAME_CLEAR = 0x820, 0x82C
BADGES = ["Boulder", "Cascade", "Thunder", "Rainbow", "Soul", "Marsh", "Volcano", "Earth"]


@unittest.skipUnless(os.environ.get("LT_FULL_RUN"), "set LT_FULL_RUN=1 or run scripts/test.sh full (several minutes)")
class WholeGameByArrow(unittest.TestCase):
    def test_new_game_to_the_hall_of_fame_using_only_the_arrow_and_a(self):
        g = FireRed()
        started = time.time()
        seen = {"badges": 0, "map": None}

        def note(text):
            print(f"  [{time.time() - started:4.0f}s, {g.frame // 3600:3d} min of play] {text}", file=sys.stderr, flush=True)

        def finished():
            if g.flag(FLAG_SYS_GAME_CLEAR):
                return True
            if g.free_to_move():
                badges = sum(g.flag(FLAG_BADGE01_GET + b) for b in range(8))
                if badges > seen["badges"]:
                    seen["badges"] = badges
                    party = ", ".join(f"species {m.species} Lv{m.level}" for m in g.party())
                    note(f"{BADGES[badges - 1]} Badge ({badges}/8) in {map_name(g.location())}; party: {party}")
                    g.shot(f"full-badge-{badges}")
                seen["map"] = map_name(g.location())
            return False

        try:
            g.start_new_game()
            try:
                g.follow_arrow(finished, max_actions=400000, what="the Hall of Fame")
            except EmulatorError as error:
                g.shot("full-stopped")
                self.fail(f"stopped with {seen['badges']} badges in {seen['map']} after {g.frame // 3600} minutes of play: {error}")
            note("Hall of Fame")
            g.shot("full-hall-of-fame")
            self.assertEqual(seen["badges"], 8)
        finally:
            g.close()


if __name__ == "__main__":
    unittest.main()
