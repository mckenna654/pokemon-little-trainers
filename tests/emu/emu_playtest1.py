"""Emulator tests for what the first hands-on playtest found (GitHub issue #1). Every one of these
was visible on the screen and invisible to tests that only read the game's memory, so these tests
look at what is drawn: screen pixels, and the arrow's picture as the console holds it."""
import unittest

from . import story
from .checkpoints import game_at
from .emu_milestone1 import EMBER, GROWL, SCRATCH, TOUGH

LOST = 2
PIDGEY, CHARMANDER = 16, 4
VAR_LT_DIFFICULTY, CLASSIC = 0x4029, 2
PANEL = (41, 82, 107)                   # the battle box's own blue, as the screen shows it
BOX_TOP, BOX_BOTTOM = 120, 152          # the four rows of tiles inside the battle message box
BUTTON_LEFT, BUTTON_STEP, BUTTON_SIZE = 18, 34, 32
OAK_WINDOW = 24                         # the window Professor Oak's battle lecture is written in
TEXT_PRINTER_SIZE, TEXT_PRINTER_ACTIVE = 0x24, 0x1B


def region(pixels, x0, x1, y0=BOX_TOP, y1=BOX_BOTTOM):
    return {pixels[y][x] for y in range(y0, y1) for x in range(x0, x1)}


def button_area(pixels, position):
    """The colours where the button in this position (0 = leftmost) is drawn."""
    left = BUTTON_LEFT + BUTTON_STEP * position
    return region(pixels, left, left + BUTTON_SIZE)


def button_picture(pixels, position):
    """The button in this position, pixel for pixel."""
    left = BUTTON_LEFT + BUTTON_STEP * position
    return [row[left:left + BUTTON_SIZE] for row in pixels[BOX_TOP:BOX_BOTTOM]]


def lecture_tasks_running(g):
    """Is the party screen's first-battle lecture (Oak explaining the list of Pokemon) running?"""
    names = [name for name in g.symbols if name.startswith("Task_FirstBattleEnterParty_")]
    funcs = {g.sym(name) | 1 for name in names}
    tasks = g.sym("gTasks")
    return any(g.r8(tasks + 0x28 * i + 4) and g.r32(tasks + 0x28 * i) | 1 in funcs for i in range(16))


class PictureMenuOnScreen(unittest.TestCase):
    def setUp(self):
        self.g = game_at("route1")

    def tearDown(self):
        self.g.close()

    def wild_battle(self, moves):
        g = self.g
        g.edit_party_mon(0, moves=moves)
        story.find_wild_battle(g)
        self.assertTrue(g.wait_action_menu())
        g.frames(20)
        return g

    def test_the_menu_fills_the_whole_box_with_nothing_left_over_at_the_ends(self):
        g = self.wild_battle([SCRATCH, GROWL, EMBER, 0])
        pixels = g.pixels()
        self.assertEqual(region(pixels, 8, 16), {PANEL}, "left end of the box is plain panel")
        self.assertEqual(region(pixels, 224, 232), {PANEL}, "right end of the box is plain panel")

    def test_the_box_never_shows_a_half_drawn_menu(self):
        """Each time the buttons came back, the box flashed white for a tenth of a second with
        part of the first button in it: the game was showing the menu while it was still being
        drawn, in the message box's colours. Watch every frame of a turn."""
        g = self.wild_battle([SCRATCH, GROWL, EMBER, 0])
        g.set_battle_hp(1, 300)                         # set-up: the wild Pokemon lasts the turn
        g.attack()
        worst, frames = 0, 0
        for frames in range(1, 1500):
            g.frames(1)
            pixels = g.pixels()
            inside = [pixels[y][x] for y in range(124, 148, 4) for x in range(60, 220, 8)]
            worst = max(worst, sum(colour != PANEL for colour in inside))
            if frames > 60 and g.at_action_menu():
                break
        self.assertTrue(g.at_action_menu(), "set-up: the buttons came back")
        # Text and buttons cover part of the box; a box that is anything but panel nearly
        # everywhere is the flash.
        self.assertLess(worst, len(inside) * 3 // 4, f"in {frames} frames the inside of the box was never blanked out")

    def test_two_attacks_get_two_attack_buttons(self):
        g = self.wild_battle([SCRATCH, GROWL, EMBER, 0])
        pixels = g.pixels()
        for position in range(4):                        # ATTACK, SPECIAL, CATCH, RUN
            self.assertNotEqual(button_area(pixels, position), {PANEL}, f"button {position + 1} is drawn")

    def test_one_attack_gets_one_attack_button(self):
        """Jake: "It's showing the same text for both attacks." A Pokemon with a single attacking
        move must not get two buttons that do the same thing."""
        g = self.wild_battle([SCRATCH, GROWL, 0, 0])
        pixels = g.pixels()
        for position in range(3):                        # ATTACK, CATCH, RUN
            self.assertNotEqual(button_area(pixels, position), {PANEL}, f"button {position + 1} is drawn")
        self.assertEqual(button_area(pixels, 3), {PANEL}, "there is no fourth button")
        self.assertEqual(g.menu_cursor(), g.ATTACK)
        g.press("RIGHT", wait=8)
        self.assertEqual(g.menu_cursor(), g.CATCH, "one step right of ATTACK is CATCH")
        g.press("RIGHT", wait=8)
        self.assertEqual(g.menu_cursor(), g.RUN)
        g.press("LEFT", wait=8)
        g.press("LEFT", wait=8)
        self.assertEqual(g.menu_cursor(), g.ATTACK, "and back again")
        g.set_battle_hp(1, TOUGH)
        g.press("A", wait=20)
        self.assertTrue(g.wait_action_menu())
        self.assertEqual(g.last_move(0), SCRATCH)

    def test_the_buttons_close_up_when_the_second_attack_goes_away(self):
        """The ring was left on SPECIAL and then there is only one attack to offer (set-up: the
        second attack is taken away mid-battle). The ring goes back to ATTACK, and each picture
        still sits on the button that does what it shows."""
        g = self.wild_battle([SCRATCH, GROWL, EMBER, 0])
        self.assertEqual(g.menu_cursor(), g.SPECIAL)
        ball, shoe = button_picture(g.pixels(), 2), button_picture(g.pixels(), 3)
        g.set_battle_hp(1, TOUGH)
        g.press("A", wait=20)                                       # Ember
        g.w16(g.sym("gBattleMons") + 0x0C + 2 * 2, 0)               # ...which is then forgotten
        self.assertTrue(g.wait_action_menu())
        g.frames(20)
        self.assertEqual(g.menu_cursor(), g.ATTACK, "the ring is not left on a button that is gone")
        pixels = g.pixels()
        self.assertEqual(button_picture(pixels, 1), ball, "the ball has moved up beside ATTACK")
        self.assertEqual(button_picture(pixels, 2), shoe, "and the shoe beside the ball")
        self.assertEqual(button_area(pixels, 3), {PANEL})
        g.press("RIGHT", wait=8)
        self.assertEqual(g.menu_cursor(), g.CATCH, "and the button under the ball is CATCH")


class FirstRivalBattle(unittest.TestCase):
    """Jake: "wrong colour in text during fight". Professor Oak's battle lecture was still being
    shown, drawn with the picture menu's colours. A child who cannot read gets no lecture."""

    def setUp(self):
        self.g = game_at("starter")

    def tearDown(self):
        self.g.close()

    def oak_is_talking(self):
        g = self.g
        return g.r8(g.sym("sTextPrinters") + TEXT_PRINTER_SIZE * OAK_WINDOW + TEXT_PRINTER_ACTIVE) != 0

    def play(self, before_each_turn=lambda: None, stop_at_lecture=False):
        """Press A to the end of the battle; report whether Oak's lecture window was ever written in."""
        g = self.g
        story.start_rival_battle(g)
        lectured = False
        for _ in range(3000):
            if (not g.in_battle() and g.free_to_move()) or (lectured and stop_at_lecture):
                return lectured
            lectured = lectured or self.oak_is_talking()
            if g.at_action_menu():
                before_each_turn()
            g.press("A", hold=3, wait=13)
        self.fail("the battle did not end")

    def test_no_lecture_when_winning(self):
        self.assertFalse(self.play(), "Oak's lecture window stayed empty")
        self.assertEqual(self.g.battle_outcome(), 1, "set-up: the battle was won")

    def test_no_lecture_when_losing(self):
        g = self.g

        def nearly_beaten():
            g.set_battle_hp(0, 1)
            g.set_battle_hp(1, TOUGH)

        self.assertFalse(self.play(nearly_beaten), "Oak's lecture window stayed empty")
        self.assertEqual(g.battle_outcome(), LOST, "set-up: the battle was lost")

    def test_classic_trainer_still_gets_the_lecture(self):
        """The original game is untouched on the Classic preset. (This also proves that the two
        tests above are looking in the right place.)"""
        self.g.set_var(VAR_LT_DIFFICULTY, CLASSIC)
        self.assertTrue(self.play(stop_at_lecture=True), "Oak spoke up during the battle")

    def test_no_change_button_with_nobody_to_change_to(self):
        """With one Pokemon, CHANGE led to a list with nobody to pick: a place where pressing A
        goes round in circles. The button is only offered when it can do something."""
        g = self.g
        story.start_rival_battle(g)
        self.assertTrue(g.wait_action_menu())
        g.frames(20)
        pixels = g.pixels()
        self.assertNotEqual(button_area(pixels, 0), {PANEL}, "ATTACK is drawn")
        self.assertEqual(button_area(pixels, 1), {PANEL}, "and nothing beside it")
        g.press("RIGHT", wait=8)
        self.assertEqual(g.menu_cursor(), g.ATTACK, "the ring has nowhere else to go")

    def test_change_sends_out_the_other_pokemon_with_a_alone_and_no_lecture(self):
        g = self.g
        g.run_script([0x79, PIDGEY, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])   # set-up: givemon PIDGEY, 5
        self.assertEqual(g.party_count(), 2)
        story.start_rival_battle(g)
        self.assertTrue(g.wait_action_menu())
        g.frames(20)
        self.assertEqual(g.battle_mon(0)["species"], CHARMANDER)
        g.press("RIGHT", wait=8)
        self.assertEqual(g.menu_cursor(), g.CHANGE)
        lectured = False
        for _ in range(300):
            g.press("A", hold=3, wait=13)
            lectured = lectured or lecture_tasks_running(g) or self.oak_is_talking()
            if g.at_action_menu() and g.battle_mon(0)["species"] != CHARMANDER:
                break
        self.assertEqual(g.battle_mon(0)["species"], PIDGEY, "pressing A sent out the other Pokemon")
        self.assertFalse(lectured, "nobody explained the list of Pokemon")


class ArrowPicture(unittest.TestCase):
    """Jake: "The arrow is bugged." Its picture was assembled from the wrong pieces: half of one
    arrow on top of half of another."""

    def arrow_picture(self, g):
        """The arrow as the console draws it: 16 rows of 16 booleans (True = part of the arrow)."""
        sprite = g.sym("gSprites") + 0x44 * g.r8(g.sym("sArrowSpriteId"))
        attr1, attr2 = g.r16(sprite + 2), g.r16(sprite + 4)
        tiles = g.read(0x06010000 + (attr2 & 0x3FF) * 32, 4 * 32)
        grid = [[False] * 16 for _ in range(16)]
        for tile in range(4):
            for y in range(8):
                for x in range(8):
                    byte = tiles[tile * 32 + y * 4 + x // 2]
                    grid[(tile // 2) * 8 + y][(tile % 2) * 8 + x] = bool(byte >> 4 if x % 2 else byte & 0xF)
        if attr1 & 0x1000:
            grid = [row[::-1] for row in grid]
        if attr1 & 0x2000:
            grid = grid[::-1]
        return grid

    def check_arrow(self, grid, direction):
        # Turn the picture so that it should point up, then judge it as an up arrow.
        if direction == "DOWN":
            grid = grid[::-1]
        elif direction == "LEFT":
            grid = [list(row) for row in zip(*grid)]
        elif direction == "RIGHT":
            grid = [list(row) for row in zip(*[row[::-1] for row in grid])]
        columns = [x for x in range(16) if any(row[x] for row in grid)]
        grid = [row[columns[0]:columns[-1] + 1] for row in grid if any(row)]
        picture = "\n".join("".join("#" if c else "." for c in row) for row in grid)
        widths = [sum(row) for row in grid]
        for row in grid:
            self.assertEqual(row, row[::-1], f"{direction}: the two sides of the arrow match\n{picture}")
        self.assertLessEqual(widths[0], 4, f"{direction}: it comes to a point at the front\n{picture}")
        widest = widths.index(max(widths))
        self.assertEqual(widths[:widest + 1], sorted(widths[:widest + 1]), f"{direction}: the head widens steadily\n{picture}")
        self.assertLess(widths[-1], max(widths), f"{direction}: the tail is narrower than the head\n{picture}")
        tail = widths[widest:]
        self.assertEqual(tail, sorted(tail, reverse=True), f"{direction}: behind the head it only gets narrower\n{picture}")

    def test_the_arrow_is_one_whole_arrow_both_upright_and_sideways(self):
        g = game_at("route1")
        try:
            seen = {}

            def seen_both_ways():
                direction = g.nav_arrow_shown() if g.free_to_move() else None
                if direction and "-" not in direction and direction not in seen:
                    seen[direction] = self.arrow_picture(g)
                return bool(seen.keys() & {"UP", "DOWN"}) and bool(seen.keys() & {"LEFT", "RIGHT"})

            g.follow_arrow(seen_both_ways, max_actions=600, what="an arrow pointing up or down and one pointing sideways")
            for direction, grid in seen.items():
                self.check_arrow(grid, direction)
        finally:
            g.close()


if __name__ == "__main__":
    unittest.main()
