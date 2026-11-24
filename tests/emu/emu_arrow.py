"""Emulator test: the first-gym slice played the way a small child would play it.

The test player knows nothing about the game. It walks where the on-screen arrow points, presses
A when there is no arrow or something is in the way, and presses ATTACK in battles. Starting from
a new game it must reach every story milestone up to the Boulder Badge.
"""
import unittest

from .firered import FireRed, PALLET_TOWN

VAR_OAKS_LAB_SCENE, VAR_VIRIDIAN_MART_SCENE = 0x4055, 0x4057
FLAG_SYS_POKEDEX_GET, FLAG_BADGE01_GET = 0x829, 0x820
PEWTER_CITY_GYM = (6, 2)


class FollowTheArrow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = FireRed()
        cls.g.start_new_game()

    @classmethod
    def tearDownClass(cls):
        cls.g.close()

    def follow(self, until, what, max_actions=6000):
        self.g.follow_arrow(lambda: until() and self.g.free_to_move(), max_actions=max_actions, what=what)

    def test_1_out_of_the_house(self):
        g = self.g
        g.frames(60)
        self.assertEqual(g.nav_arrow(), "RIGHT", "in the bedroom the arrow points towards the stairs")
        g.shot("arrow-1-bedroom")
        self.follow(lambda: g.location() == PALLET_TOWN, "Pallet Town")
        g.frames(60)
        self.assertIsNotNone(g.nav_arrow(), "the arrow is showing outdoors")
        g.shot("arrow-2-pallet-town")

    def test_2_choose_a_starter(self):
        g = self.g
        self.follow(lambda: g.party_count() == 1, "a starter Pokemon")
        self.assertIn(g.party()[0].species, (1, 4, 7))

    def test_3_first_battle(self):
        g = self.g
        self.follow(lambda: g.var(VAR_OAKS_LAB_SCENE) >= 4, "the end of the rival battle")

    def test_4_fetch_and_deliver_the_parcel(self):
        g = self.g
        self.follow(lambda: g.var(VAR_VIRIDIAN_MART_SCENE) >= 1, "Oak's parcel")
        g.shot("arrow-3-viridian-city")
        self.follow(lambda: g.flag(FLAG_SYS_POKEDEX_GET), "the Pokedex")

    def test_5_through_the_forest_to_brock(self):
        g = self.g
        self.follow(lambda: g.location() == PEWTER_CITY_GYM, "Pewter Gym", max_actions=12000)
        g.shot("arrow-4-pewter-gym")
        self.follow(lambda: g.flag(FLAG_BADGE01_GET), "the Boulder Badge", max_actions=3000)
        g.shot("arrow-5-boulder-badge")
        self.assertGreaterEqual(g.party()[0].level, 10)
        self.assertEqual(g.party()[0].hp, g.party()[0].max_hp, "healed after beating Brock")


if __name__ == "__main__":
    unittest.main()
