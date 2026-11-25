"""Emulator tests for the Little Trainer picture battle menu: ATTACK / SPECIAL / CATCH / RUN
buttons, one press each, with no move list and no bag."""
import unittest

from . import story
from .emu_milestone1 import BattleTestCase, CAUGHT, EMBER, GROWL, LEER, RAN, SCRATCH, TACKLE, TOUGH, WON, damage_rolls

STRUGGLE = 165
GASTLY, TYPE_GHOST, TYPE_POISON = 92, 7, 3


class SimpleBattleMenu(BattleTestCase):
    def start_battle(self, moves=None):
        g = self.g
        if moves:
            g.edit_party_mon(0, moves=moves)
        story.find_wild_battle(g)
        self.assertTrue(g.wait_action_menu())
        return g

    def press_and_watch(self, action):
        """Do a menu action and report whether the move list or the bag ever appeared."""
        g = self.g
        seen = set()
        action()
        for _ in range(400):
            if g.at_move_menu():
                seen.add("move list")
            if g.callback2() == "CB2_BagMenuRun":
                seen.add("bag")
            if not g.in_battle() or g.at_action_menu():
                break
            if g.callback2() == "CB2_NamingScreen":
                g.press("START", wait=20)
                g.press("A", wait=40)
            else:
                g.press("B", hold=3, wait=13)
        return seen

    def test_menu_screenshot(self):
        g = self.start_battle([SCRATCH, GROWL, EMBER, 0])
        g.frames(30)
        g.shot("m2-picture-menu-wild")
        g.press("RIGHT", wait=20)
        g.shot("m2-picture-menu-catch-selected")

    def test_cursor_starts_on_the_recommended_attack(self):
        g = self.start_battle([SCRATCH, GROWL, EMBER, 0])
        self.assertEqual(g.menu_cursor(), g.SPECIAL, "Ember (own type) beats Scratch")
        g.set_battle_hp(1, TOUGH)
        g.attack()                                   # the child chooses something else...
        self.assertTrue(g.wait_action_menu())
        self.assertEqual(g.menu_cursor(), g.ATTACK, "...and the cursor stays where they left it")

    def test_cursor_starts_on_first_button_when_there_is_one_attack(self):
        g = self.start_battle([SCRATCH, GROWL, 0, 0])
        self.assertEqual(g.menu_cursor(), g.ATTACK)

    def test_cursor_cannot_leave_the_row(self):
        g = self.start_battle()
        for _ in range(6):
            g.press("RIGHT", wait=8)
        self.assertEqual(g.menu_cursor(), g.RUN)
        for _ in range(6):
            g.press("LEFT", wait=8)
        self.assertEqual(g.menu_cursor(), g.ATTACK)
        g.press("UP", wait=8)
        g.press("DOWN", wait=8)
        self.assertEqual(g.menu_cursor(), g.ATTACK)
        self.assertTrue(g.at_action_menu())

    def test_ghost_opponent_cannot_leave_the_player_without_an_attack(self):
        g = self.start_battle([SCRATCH, GROWL, 0, 0])            # only a Normal-type attack
        foe_addr = g.sym("gBattleMons") + 0x58
        g.w16(foe_addr, GASTLY)                                  # set-up: turn the opponent into a Ghost
        g.w8(foe_addr + 0x21, TYPE_GHOST)
        g.w8(foe_addr + 0x22, TYPE_POISON)
        g.set_battle_hp(1, TOUGH)
        me, foe = self.battler_stats(0), self.battler_stats(1)
        self.press_and_watch(g.attack)
        self.assertEqual(g.last_move(0), STRUGGLE, "a typeless attack is borrowed when Scratch cannot hit")
        self.assertLess(g.battle_mon(1)["hp"], TOUGH, "and it does damage")
        taken = me["hp"] - self.battler_stats(0)["hp"]
        from_opponent = damage_rolls(foe["level"], foe["attack"], me["defense"], 35, 60) | {0}
        self.assertIn(taken, from_opponent, "no recoil damage on top of what the opponent did")

    def test_attack_is_one_press_and_uses_the_basic_move(self):
        g = self.start_battle([SCRATCH, GROWL, EMBER, 0])
        g.set_battle_hp(1, TOUGH)
        seen = self.press_and_watch(g.attack)
        self.assertEqual(seen, set(), "no move list and no bag")
        self.assertLess(g.battle_mon(1)["hp"], TOUGH)
        self.assertEqual(g.last_move(0), SCRATCH)

    def test_special_uses_the_pokemons_own_type_move(self):
        g = self.start_battle([SCRATCH, GROWL, EMBER, 0])
        g.set_battle_hp(1, TOUGH)
        seen = self.press_and_watch(g.special)
        self.assertEqual(seen, set())
        self.assertLess(g.battle_mon(1)["hp"], TOUGH)
        self.assertEqual(g.last_move(0), EMBER)

    def test_pokemon_without_attacks_borrows_tackle_and_keeps_its_own_moves(self):
        g = self.start_battle([GROWL, LEER, 0, 0])
        g.set_battle_hp(1, TOUGH)
        self.press_and_watch(g.attack)
        self.assertLess(g.battle_mon(1)["hp"], TOUGH, "the borrowed attack did damage")
        self.assertEqual(g.last_move(0), TACKLE)
        g.set_battle_hp(1, 1)
        self.assertEqual(self.fight(), WON)
        self.assertEqual(g.party()[0].moves, [GROWL, LEER, 0, 0], "real moves untouched after the battle")

    def test_catching_needs_no_bag_and_no_ball_in_it(self):
        g = self.g
        for expected_party in (2, 3):
            story.find_wild_battle(g)
            self.assertTrue(g.wait_action_menu())
            enemy = g.battle_mon(1)
            self.assertEqual(enemy["hp"], enemy["max_hp"], "caught at full health")
            seen = self.press_and_watch(g.catch)
            self.assertEqual(seen, set(), "the bag never opened")
            g.advance_text(g.free_to_move, what="control after catching")
            self.assertEqual(g.battle_outcome(), CAUGHT)
            self.assertEqual(g.party_count(), expected_party)
        g.shot("m2-after-two-catches")

    def test_run_always_works(self):
        g = self.g
        for _ in range(3):
            story.find_wild_battle(g)
            self.assertTrue(g.wait_action_menu())
            # set-up: make our Pokemon far slower than the wild one (vanilla would often fail to flee)
            g.w16(g.sym("gBattleMons") + 6, 1)
            g.run_away()
            g.advance_text(g.free_to_move, what="control after running")
            self.assertEqual(g.battle_outcome(), RAN)

    def test_b_button_does_nothing_in_the_menu(self):
        g = self.start_battle()
        hp = g.battle_mon(1)["hp"]
        for _ in range(10):
            g.press("B", wait=10)
        self.assertTrue(g.at_action_menu())
        self.assertEqual(g.battle_mon(1)["hp"], hp)


if __name__ == "__main__":
    unittest.main()
