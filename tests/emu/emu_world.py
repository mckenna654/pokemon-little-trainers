"""Emulator tests for game-wide rules that need late-game situations. Set-up uses
FireRed.run_script (the game's own script engine) to reach them quickly."""
import unittest

from .checkpoints import game_at
from .maps import MapInfo
from .emu_milestone1 import WON

VERMILION_CITY, ROUTE21_NORTH, ROCK_TUNNEL_1F = (3, 5), (3, 39), (1, 81)
ITEM_HM01_CUT, ITEM_HM03_SURF = 339, 341
WATER = {0x10, 0x12, 0x15}                  # MB_POND_WATER, MB_DEEP_WATER, MB_OCEAN_WATER
BUG_CATCHER_DOUG, LEADER_BROCK, LEADER_MISTY, LEADER_LT_SURGE, LORELEI = 103, 414, 415, 416, 410


class WorldTestCase(unittest.TestCase):
    def setUp(self):
        self.g = game_at("route1")

    def tearDown(self):
        self.g.close()

    def win(self):
        g = self.g
        while g.wait_action_menu():
            g.set_battle_hp(1, 1)            # set-up: these tests are not about the fight itself
            g.attack()
        g.advance_text(g.free_to_move, max_presses=900, what="control after battle")
        return g.battle_outcome()


class TrainerTeams(WorldTestCase):
    def team_size(self, trainer):
        self.g.start_trainer_battle(trainer)
        return len(self.g.enemy_party())

    def test_ordinary_trainer_brings_at_most_two(self):
        g = self.g
        self.assertEqual(self.team_size(BUG_CATCHER_DOUG), 2, "Doug has three Pokemon in the original")
        self.assertTrue(g.wait_action_menu())
        g.frames(20)
        g.shot("world-trainer-battle-menu")
        self.assertEqual(self.win(), WON)

    def test_leader_teams_grow_with_badges(self):
        g = self.g
        self.assertEqual(self.team_size(LEADER_LT_SURGE), 2, "three in the original; two before any badge")
        self.assertEqual(self.win(), WON)
        g.give_badges(3)
        self.assertEqual(self.team_size(LEADER_LT_SURGE), 3, "all three once the player has three badges")
        self.assertEqual(self.win(), WON)

    def test_elite_four_bring_four_and_keep_their_strongest(self):
        g = self.g
        team = None
        g.start_trainer_battle(LORELEI)
        team = g.enemy_party()
        self.assertEqual(len(team), 4, "five in the original")
        self.assertEqual(team[-1].species, 131, "Lapras, her last and strongest, is kept")


class FieldMovesWithoutTeaching(WorldTestCase):
    def test_cut_needs_only_the_hm_and_the_badge(self):
        g = self.g
        tree = (19, 24)                                  # the tree in front of Vermilion Gym
        g.teleport(VERMILION_CITY, 19, 25)
        self.assertIn(tree, g.npc_tiles())
        g.face("UP")
        g.press("A", wait=30)
        g.advance_text(g.free_to_move, what="the 'can be cut' message to close")
        self.assertIn(tree, g.npc_tiles(), "without the HM and badge the tree stays")

        g.give_item(ITEM_HM01_CUT)
        g.give_badges(2)
        self.assertNotIn(15, g.party()[0].moves, "set-up: no Pokemon knows Cut")
        g.face("UP")
        g.press("A", wait=30)
        g.advance_text(lambda: g.free_to_move() and tree not in g.npc_tiles(), what="the tree to be cut")
        self.assertTrue(g.step("UP"), "the way is open")
        g.shot("world-cut-tree-gone")

    def test_surf_needs_only_the_hm_and_the_badge(self):
        g = self.g
        spot, direction = MapInfo(ROUTE21_NORTH).find_beside(WATER)
        g.teleport(ROUTE21_NORTH, *spot)
        g.face(direction)
        g.press("A", wait=40)
        self.assertFalse(g.is_surfing(), "no HM yet")
        g.advance_text(g.free_to_move, what="control")

        g.give_item(ITEM_HM03_SURF)
        g.give_badges(5)
        g.face(direction)
        g.press("A", wait=30)
        g.advance_text(lambda: g.is_surfing() and g.free_to_move(), what="surfing to start")
        g.shot("world-surfing")

    def test_caves_are_not_dark(self):
        g = self.g
        x, y, _ = MapInfo(ROCK_TUNNEL_1F).warps[0]
        g.teleport(ROCK_TUNNEL_1F, x, y)
        sb1 = g.r32(g.sym("gSaveBlock1Ptr"))
        self.assertEqual(g.r8(sb1 + 0x30), 0, "flash level 0 means fully lit")
        g.shot("world-rock-tunnel-lit")


if __name__ == "__main__":
    unittest.main()
