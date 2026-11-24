"""Emulator tests for game-wide rules that need late-game situations. Set-up uses
FireRed.run_script (the game's own script engine) to reach them quickly."""
import struct
import unittest

from . import emu_arrow_goals as goals
from .checkpoints import game_at
from .maps import MapInfo, location_of
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
            g.set_battle_hp(1, 1)            # set-up: these tests are not about the fight itself,
            g.set_battle_hp(0, g.battle_mon(0)["max_hp"])    # so the Route 1 starter must not lose it:
            mine = g.sym("gBattleMons")
            for stat in (0x04, 0x06, 0x0A):                  # defence, speed, special defence
                g.w16(mine + stat, 999)
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


class PuzzlesMadeSimple(WorldTestCase):
    def story_state(self, before_goal):
        """Set the flags and hand over the HMs the story would have by the time of `before_goal`."""
        g = self.g
        script = []
        for earlier in goals.GOALS:
            if earlier["id"] == before_goal:
                break
            done = earlier["done"]
            if "flag" in done:
                script += [0x29] + g._u16(goals.FLAGS[done["flag"]])
            elif "item" in done:
                script += [0x44] + g._u16(goals.ITEMS[done["item"]]) + g._u16(1)
            else:
                script += [0x16] + g._u16(goals.VARS[done["var"]]) + g._u16(done["ge"])
            if earlier["id"] in goals.HM_AFTER:
                script += [0x44] + g._u16(goals.HM_AFTER[earlier["id"]]) + g._u16(1)
        g.run_script(script)

    def test_lift_opens_on_the_floor_the_story_needs(self):
        g = self.g
        self.story_state("rocket_hideout")              # has the Lift Key; next: Giovanni on B4F
        cabin = location_of("RocketHideout_Elevator")
        g.teleport(cabin, *goals.standing_tile("RocketHideout_Elevator"))
        g.frames(60)
        g.follow_arrow(lambda: g.location() != cabin and g.free_to_move(), max_actions=200, what="leaving the lift")
        self.assertEqual(g.location(), location_of("RocketHideout_B4F"), "no floor menu needed")

    def test_spin_tiles_do_not_spin(self):
        g = self.g
        floor = location_of("RocketHideout_B2F")
        spot, direction = MapInfo(floor).find_beside({0x54, 0x55, 0x56, 0x57})     # MB_SPIN_RIGHT/LEFT/UP/DOWN
        dx, dy = {"UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0)}[direction]
        g.teleport(floor, *spot)
        self.assertTrue(g.step(direction))
        g.frames(90)
        self.assertEqual(g.position(), (spot[0] + dx, spot[1] + dy), "standing on the arrow tile, not carried away")

    def test_surges_gates_are_open_and_the_arrow_leads_to_him(self):
        g = self.g
        self.story_state("lt_surge")
        gym = location_of("VermilionCity_Gym")
        g.teleport(gym, *goals.standing_tile("VermilionCity_Gym"))
        g.frames(60)
        g.follow_arrow(lambda: g.in_battle() and g.r16(g.sym("gTrainerBattleOpponent_A")) == LEADER_LT_SURGE,
                       max_actions=600, on_battle=self.win, what="the battle with Lt. Surge")

    def test_arrow_leads_through_the_elite_four_to_the_hall_of_fame(self):
        """Each room's way out is shut until its trainer is beaten: the arrow must lead to the
        trainer first, then to the door, five times over."""
        g = self.g
        self.story_state("league")
        g.teleport(location_of("IndigoPlateau_PokemonCenter_1F"), 4, 4)
        g.frames(60)
        rooms = []

        def in_hall_of_fame():
            if g.in_overworld() and (not rooms or rooms[-1] != g.location()):
                rooms.append(g.location())                # (the Champion speaks as soon as his room is entered)
            return g.flag(0x82C)                          # FLAG_SYS_GAME_CLEAR

        def win():
            while g.wait_action_menu():
                g.set_battle_hp(1, 1)                     # as in WorldTestCase.win
                g.set_battle_hp(0, g.battle_mon(0)["max_hp"])
                for stat in (0x04, 0x06, 0x0A):
                    g.w16(g.sym("gBattleMons") + stat, 999)
                g.attack()
            # (after the Champion, the story runs on into the Hall of Fame and the credits by itself)
            g.advance_text(lambda: in_hall_of_fame() or g.free_to_move(), max_presses=2500, what="control after battle")

        g.follow_arrow(in_hall_of_fame, max_actions=6000, on_battle=win, what="the Hall of Fame")
        names = ["Loreleis", "Brunos", "Agathas", "Lances", "Champions"]
        self.assertEqual(rooms[1:6], [location_of(f"PokemonLeague_{n}Room") for n in names])

    def test_victory_road_barrier_is_down(self):
        g = self.g
        g.teleport(location_of("VictoryRoad_1F"), *goals.standing_tile("VictoryRoad_1F"))
        width = g.r32(g.sym("VMap"))
        blocks = g.r32(g.sym("VMap") + 8)
        for y in (14, 15):                                # where the rock barrier stands in the original
            block = g.r16(blocks + 2 * ((y + 7) * width + (12 + 7)))
            self.assertEqual((block >> 10) & 3, 0, "the barrier tile can be walked through")


class PeopleWhoStopWhereTheyWereBeaten(WorldTestCase):
    """Found by the whole-game run: a trainer who wanders about stands still for good once beaten,
    wherever that happens to be. The arrow kept avoiding the spot the trainer started from and
    walking into the trainer; with Surf it then led into the water and straight back out, for ever."""

    ROUTE13 = location_of("Route13")
    SEBASTIAN, HIS_SPOT = 2, (63, 12)       # a wandering Rocker at the corner of the boardwalk
    CORNER, NORTH_OF_IT = (62, 12), (62, 11)

    def sebastian(self):
        g = self.g
        base = g.sym("gObjectEvents")
        for i in range(1, 16):
            raw = g.read(base + i * 0x24, 0x18)
            if raw[0] & 1 and raw[8] == self.SEBASTIAN:
                x, y = struct.unpack_from("<hh", raw, 0x10)
                return x - 7, y - 7
        return None

    def beat_him_north_of_the_corner(self, delay):
        """Stand on the corner and fight him when he wanders onto the tile to the north. He walks
        at random, so this can go wrong (he may challenge the player from somewhere else)."""
        g = self.g
        PuzzlesMadeSimple.story_state(self, "blaine")          # six badges, Surf owned, heading for Cinnabar
        g.frames(delay)
        g.teleport(self.ROUTE13, *self.CORNER)
        g.face("UP")
        for _ in range(3000):
            if g.in_battle():
                break
            if g.free_to_move() and self.sebastian() == self.NORTH_OF_IT:
                g.press("A", wait=10)
            else:
                g.press("B", wait=6)                           # (B also moves his greeting along)
        if not g.in_battle() or self.sebastian() != self.NORTH_OF_IT:
            return False
        self.assertEqual(self.win(), WON)
        return self.sebastian() == self.NORTH_OF_IT

    def test_the_arrow_gets_past_a_beaten_wanderer(self):
        for delay in range(0, 400, 37):                        # a different moment each try
            if self.beat_him_north_of_the_corner(delay):
                break
            self.g.close()
            self.g = game_at("route1")
        else:
            self.fail("set-up: could not get the wandering trainer beaten north of the corner")
        g = self.g
        self.assertEqual(g.position(), self.CORNER)

        def past_him():
            x, y = g.position()
            return g.location() != self.ROUTE13 or (y <= 9 and x >= 62)

        g.follow_arrow(past_him, max_actions=120, what="the boardwalk north of the beaten trainer")
        self.assertFalse(g.is_surfing(), "and the way past is on foot, round the other side of him")


class VersionExclusives(WorldTestCase):
    def test_leafgreen_only_pokemon_turn_up_in_the_wild(self):
        """Route 6 has Oddish in FireRed and Bellsprout in LeafGreen. Meet forty wild Pokemon there
        (running from each): both must turn up, and nothing that does not belong on the route."""
        g = self.g
        route6 = location_of("Route6")
        info = MapInfo(route6)
        grass = [(x, y) for y in range(info.height) for x in range(info.width)
                 if info.behavior(x, y) == 0x02 and info.passable(x, y)]
        a = next(t for t in grass if (t[0] + 1, t[1]) in grass)
        g.teleport(route6, *a)
        seen = {}
        for _ in range(40):
            for _ in range(400):
                if g.in_battle():
                    break
                g.step("RIGHT" if g.position() == a else "LEFT")
            else:
                self.fail("no wild Pokemon appeared")
            g.wait_action_menu()
            species = g.enemy().species
            seen[species] = seen.get(species, 0) + 1
            g.run_away()
            g.advance_text(lambda: not g.in_battle() and g.free_to_move(), max_presses=300, what="running away")
        ODDISH, BELLSPROUT, PIDGEY, MEOWTH = 43, 69, 16, 52
        self.assertIn(BELLSPROUT, seen, f"met: {seen}")
        self.assertIn(ODDISH, seen, f"met: {seen}")
        self.assertLessEqual(set(seen), {ODDISH, BELLSPROUT, PIDGEY, MEOWTH}, f"met: {seen}")
        self.assertGreater(seen[ODDISH] + seen.get(PIDGEY, 0) + seen.get(MEOWTH, 0), seen[BELLSPROUT],
                           "the LeafGreen Pokemon is the rarer one")


if __name__ == "__main__":
    unittest.main()
