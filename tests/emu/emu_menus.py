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


class DifficultyPresets(unittest.TestCase):
    """The parent control: OPTION -> MODE switches between Little, Junior and Classic Trainer."""

    VAR_LT_DIFFICULTY = 0x4029

    def setUp(self):
        self.g = game_at("route1")

    def tearDown(self):
        self.g.close()

    def test_mode_is_changed_in_the_options_menu_and_kept(self):
        g = self.g
        self.assertEqual(g.var(self.VAR_LT_DIFFICULTY), 0, "a new game starts as Little Trainer")
        g.press("START", wait=40)
        for _ in range(3):                      # POKeMON, BAG, SAVE, OPTION
            g.press("DOWN", wait=10)
        g.press("A", wait=90)                   # open OPTION
        g.press("DOWN", wait=10)
        g.press("DOWN", wait=10)                # TEXT SPEED, BATTLE SCENE, MODE
        g.press("RIGHT", wait=20)
        g.shot("menu-options-mode")
        g.press("B", wait=120)                  # close OPTION (settings are kept), back to the Start menu
        g.press("B", wait=60)                   # close the Start menu
        self.assertTrue(g.free_to_move())
        self.assertEqual(g.var(self.VAR_LT_DIFFICULTY), 1, "now Junior Trainer")

    def test_classic_mode_uses_the_original_battle_menu(self):
        from . import story
        g = self.g
        g.set_var(self.VAR_LT_DIFFICULTY, 2)
        story.find_wild_battle(g)
        self.assertTrue(g.wait_action_menu())
        g.press("A", wait=30)                   # FIGHT
        g.run_until(g.at_move_menu, max_frames=300, what="the original move list")
        g.shot("menu-classic-move-list")

    def test_junior_mode_has_the_little_trainer_menus(self):
        from . import story
        g = self.g
        g.set_var(self.VAR_LT_DIFFICULTY, 1)
        g.frames(30)
        self.assertIsNotNone(g.nav_arrow(), "Junior still has the arrow")
        story.find_wild_battle(g)
        self.assertTrue(g.wait_action_menu())
        g.frames(30)
        g.shot("menu-junior-picture-menu")
        g.attack()
        for _ in range(200):
            self.assertFalse(g.at_move_menu(), "ATTACK is one press: no move list on Junior")
            if not g.in_battle() or g.at_action_menu():
                break
            g.press("B", hold=3, wait=13)

if __name__ == "__main__":
    unittest.main()
