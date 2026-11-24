"""Emulator test: the opening of the game is playable from power-on with nothing but button
presses. This is the backbone every other emulator test builds on."""
import unittest

from . import story
from .firered import FireRed, OAKS_LAB, PALLET_TOWN, PLAYERS_HOUSE_2F, ROUTE1


class OpeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = FireRed()

    @classmethod
    def tearDownClass(cls):
        cls.g.close()

    def test_1_new_game_reaches_bedroom(self):
        self.g.start_new_game()
        self.assertEqual(self.g.location(), PLAYERS_HOUSE_2F)
        self.assertEqual(self.g.party_count(), 0)
        self.g.shot("01-bedroom")

    def test_2_leave_house(self):
        self.g.take_warp(10, 2)
        self.g.take_warp(4, 8)
        self.assertEqual(self.g.location(), PALLET_TOWN)
        self.g.shot("02-pallet-town")

    def test_3_oak_and_starter(self):
        story.meet_oak(self.g)
        self.assertEqual(self.g.location(), OAKS_LAB)
        self.g.shot("03-oaks-lab")
        mon = story.choose_starter(self.g, "charmander")
        self.assertEqual(mon.level, 5)
        self.assertEqual(mon.hp, mon.max_hp)

    def test_4_rival_battle_can_be_won_by_mashing_a(self):
        g = self.g
        story.start_rival_battle(g)
        # The very first battle already uses the picture menu, in its trainer layout:
        # ATTACK, SPECIAL, CHANGE and no RUN button.
        self.assertTrue(g.wait_action_menu())
        for _ in range(5):
            g.press("RIGHT", wait=8)
        self.assertEqual(g.menu_cursor(), g.CHANGE, "the row ends at CHANGE against a trainer")
        g.frames(20)
        g.shot("04-rival-battle-menu")
        for _ in range(5):
            g.press("LEFT", wait=8)
        outcome = story.finish_battle(g)
        self.assertEqual(outcome, 1, "B_OUTCOME_WON")
        self.assertTrue(self.g.free_to_move())

    def test_5_route1_wild_battle(self):
        story.to_route1(self.g)
        self.assertEqual(self.g.location(), ROUTE1)
        self.g.shot("05-route-1")
        story.find_wild_battle(self.g)
        self.assertTrue(self.g.in_battle())
        self.g.frames(240)
        self.g.shot("06-wild-battle")


if __name__ == "__main__":
    unittest.main()
