"""Emulator tests for the field menus."""
import unittest

from .checkpoints import game_at

POKEDEX, POKEMON, BAG, PLAYER, SAVE, OPTION, EXIT = range(7)


class StartMenu(unittest.TestCase):
    def setUp(self):
        self.g = game_at("route1")

    def tearDown(self):
        self.g.close()

    def entries(self):
        g = self.g
        count = g.r8(g.sym("sNumStartMenuItems"))
        return list(g.read(g.sym("sStartMenuOrder"), count))

    def test_start_menu_has_pictures_and_no_trainer_card(self):
        g = self.g
        g.press("START", wait=40)
        self.assertFalse(g.free_to_move(), "the menu is open")
        self.assertEqual(self.entries(), [POKEMON, BAG, SAVE, OPTION, EXIT],
                         "before the Pokedex is obtained; the trainer card entry is left out")
        g.shot("menu-start")

    def test_start_menu_can_be_closed_with_exit_or_b(self):
        g = self.g
        g.press("START", wait=40)
        for _ in range(len(self.entries()) - 1):
            g.press("DOWN", wait=10)
        self.assertEqual(g.r8(g.sym("sStartMenuCursorPos")), len(self.entries()) - 1)
        g.press("A", wait=40)
        self.assertTrue(g.free_to_move(), "EXIT closes the menu")
        g.press("START", wait=40)
        g.press("B", wait=40)
        self.assertTrue(g.free_to_move(), "B closes the menu")


    def test_save_from_the_menu_survives_a_reset(self):
        g = self.g
        before = (g.location(), g.position(), g.party()[0].species, g.party()[0].level, g.money())
        g.press("START", wait=40)
        for _ in range(self.entries().index(SAVE)):
            g.press("DOWN", wait=10)
        g.press("A", wait=60)
        g.shot("menu-save-question")
        g.advance_text(g.free_to_move, max_presses=200, what="control after saving")
        g.reset()                                    # power cycle; the cartridge save is kept
        g.advance_text(g.free_to_move, max_presses=400, what="control after CONTINUE")
        after = (g.location(), g.position(), g.party()[0].species, g.party()[0].level, g.money())
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
