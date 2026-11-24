"""Emulator tests for the Little Trainer battle menu: ATTACK / CATCH / SPECIAL / RUN, one press
each, with no move list and no bag."""
import unittest

from . import story
from .emu_milestone1 import BattleTestCase, CAUGHT, EMBER, GROWL, LEER, RAN, SCRATCH, TACKLE, TOUGH, WON


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
        g = self.start_battle()
        g.frames(30)
        g.shot("m2-simple-menu-wild")

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

    def test_one_attack_only_means_both_buttons_use_it(self):
        g = self.start_battle([SCRATCH, GROWL, 0, 0])
        g.set_battle_hp(1, TOUGH)
        self.press_and_watch(g.special)
        self.assertEqual(g.last_move(0), SCRATCH)

    def test_pokemon_without_attacks_borrows_tackle_and_keeps_its_own_moves(self):
        g = self.start_battle([GROWL, LEER, 0, 0])
        g.set_battle_hp(1, TOUGH)
        self.press_and_watch(g.attack)
        self.assertLess(g.battle_mon(1)["hp"], TOUGH, "the borrowed attack did damage")
        self.assertEqual(g.last_move(0), TACKLE)
        g.set_battle_hp(1, 1)
        self.assertEqual(self.fight(), WON)
        self.assertEqual(g.party()[0].moves, [GROWL, LEER, 0, 0], "real moves untouched after the battle")

    def test_catch_is_one_press_with_an_empty_bag(self):
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
