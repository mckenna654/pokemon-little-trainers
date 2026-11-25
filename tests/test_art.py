"""Checks on the art that goes into the game.

The battle buttons, Start menu pictures and title plaque are illustrations kept in
`assets/generated/v1/gba/` (the pack). The small control symbols (ring, star, hearts, arrow,
confetti, tick and cross) are drawn by `assets/ui/make_battle_icons.py`, which also copies the
pack's three sheets into the game. These tests need neither the game source nor an image library.
"""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import tempfile
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
spec = importlib.util.spec_from_file_location("make_battle_icons", os.path.join(ROOT, "assets", "ui", "make_battle_icons.py"))
art = importlib.util.module_from_spec(spec)
spec.loader.exec_module(art)
PACK, PACK_SHEETS = art.PACK, art.PACK_SHEETS
RING = 14                       # the colour the game pulses for the selection ring


def sheet(name):
    return art.read_indexed_png(os.path.join(PACK, name))


def shapes(rows, colour, smallest=6):
    """How many separate patches of a colour (touching sideways or up and down) a picture has,
    ignoring specks."""
    todo = {(x, y) for y, row in enumerate(rows) for x, c in enumerate(row) if c == colour}
    count = 0
    while todo:
        stack, size = [todo.pop()], 0
        while stack:
            x, y = stack.pop()
            size += 1
            for near in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if near in todo:
                    todo.remove(near)
                    stack.append(near)
        count += size >= smallest
    return count


class TitleBanner(unittest.TestCase):
    def banner(self):
        frames = sheet("title_banner.png")      # four 32x32 frames stacked vertically
        self.assertEqual((len(frames[0]), len(frames)), (32, 128))
        return [[c for f in range(4) for c in frames[f * 32 + y]] for y in range(32)]

    def test_the_words_sit_on_a_solid_plaque(self):
        """The title screen has flames and a horizon behind the banner. Nothing may show through
        between the letters, or the words become hard to read."""
        rows = self.banner()
        inked = [(x, y) for y, row in enumerate(rows) for x, c in enumerate(row) if c != art.T]
        left, right = min(x for x, _ in inked), max(x for x, _ in inked)
        top, bottom = min(y for _, y in inked), max(y for _, y in inked)
        holes = [(x, y) for y in range(top, bottom + 1) for x in range(left, right + 1) if rows[y][x] == art.T]
        corners = [(x, y) for x, y in holes if min(x - left, right - x) + min(y - top, bottom - y) <= 3]
        self.assertEqual(holes, corners, "see-through pixels only at the rounded corners")

    def test_the_letters_are_separate_shapes(self):
        """Shrunk carelessly, the L and I of LITTLE joined into a U and the title read UTTLE."""
        rows = self.banner()
        lettering = max({c for row in rows for c in row} - {art.T, art.B_PLAQUE},
                        key=lambda colour: sum(row[4:-4].count(colour) for row in rows[4:-4]))
        split = max(range(8, 24), key=lambda y: sum(c != lettering for c in rows[y]))   # the gap between the two words
        self.assertEqual(shapes(rows[:split], lettering), 6, "LITTLE is six letters")
        self.assertGreaterEqual(shapes(rows[split:], lettering), 6, "most of TRAINERS' eight letters stand apart")

    def test_the_letters_stand_out_from_the_plaque(self):
        rows = self.banner()
        colours = {c for row in rows for c in row} - {art.T}
        self.assertGreaterEqual(len(colours), 3, "plaque, border and lettering")
        self.assertLessEqual(max(colours), len(art.BANNER_PALETTE) - 1)


class BattleButtons(unittest.TestCase):
    def test_one_button_for_every_icon_the_game_knows(self):
        rows = sheet("battle_icons.png")
        self.assertEqual((len(rows[0]), len(rows)), (32, 32 * len(art.ICONS)))

    def test_no_picture_uses_the_pulsing_ring_colour(self):
        """The game animates that colour: a picture using it would flash."""
        self.assertNotIn(RING, {c for row in sheet("battle_icons.png") for c in row})

    def test_every_button_has_a_picture_on_it(self):
        rows = sheet("battle_icons.png")
        blank = art.button([[art.T] * 24 for _ in range(24)])
        seen = set()
        for i, (name, _) in enumerate(art.ICONS):
            cell = tuple(tuple(row) for row in rows[i * 32:(i + 1) * 32])
            self.assertNotEqual(cell, tuple(tuple(row) for row in blank), f"{name} is an empty button")
            self.assertNotIn(cell, seen, f"{name} repeats another button")
            seen.add(cell)


class StartMenuPictures(unittest.TestCase):
    def test_pictures_fit_the_menu_rows_and_its_colours(self):
        """Menu rows are 15 pixels apart and the window owns only colours 1 to 9."""
        rows = sheet("start_menu_icons.png")
        self.assertEqual((len(rows[0]), len(rows)), (16, 16 * 9))
        for i in range(9):
            cell = rows[i * 16:(i + 1) * 16]
            self.assertTrue(any(c for row in cell for c in row), f"picture {i} is empty")
            self.assertFalse(any(cell[14]) or any(cell[15]), f"picture {i} runs into the next row")
            self.assertLessEqual(max(c for row in cell for c in row), 9, f"picture {i} uses a colour the menu does not have")


    def test_the_bag_is_a_green_bag(self):
        """The illustration is a green backpack. Matched to the menu's colours by plain RGB
        distance, its green turned grey and nobody could say what it was."""
        rows = sheet("start_menu_icons.png")
        bag = [c for row in rows[2 * 16:3 * 16] for c in row]
        green = bag.count(6) + bag.count(7)
        grey = bag.count(2) + bag.count(3)
        self.assertGreater(green, grey, "more green than grey in the bag")


class Shrinking(unittest.TestCase):
    """`assets/generated/shrink.py` chooses the game colour for each part of an illustration."""
    @classmethod
    def setUpClass(cls):
        path = os.path.join(ROOT, "assets", "generated", "shrink.py")
        spec = importlib.util.spec_from_file_location("shrink", path)
        cls.shrink = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.shrink)

    def nearest(self, colour, palette):
        return min(palette, key=lambda c: self.shrink.colour_distance(colour, c))

    def test_a_mid_green_stays_green(self):
        """By plain RGB distance this green is nearer the menu's grey than its greens."""
        menu = art.MENU_PALETTE[1:10]
        self.assertIn(self.nearest((76, 175, 80), menu), (art.MENU_PALETTE[6], art.MENU_PALETTE[7]))

    def test_plain_colours_stay_themselves(self):
        menu = art.MENU_PALETTE[1:10]
        for colour in menu:
            self.assertEqual(self.nearest(colour, menu), colour)
        self.assertEqual(self.nearest((40, 40, 60), menu), art.MENU_PALETTE[2], "a dark outline is the dark grey")


class Pipeline(unittest.TestCase):
    def test_the_generator_keeps_the_packs_pictures(self):
        """Running the drawing program must not put the old shape drawings back."""
        with tempfile.TemporaryDirectory() as out:
            with contextlib.redirect_stdout(io.StringIO()):
                art.main(out=out)
            for name in PACK_SHEETS:
                with open(os.path.join(out, name), "rb") as made, open(os.path.join(PACK, name), "rb") as pack:
                    self.assertEqual(made.read(), pack.read(), f"{name} was not taken from the pack")
            for name in ("battle_ring.png", "battle_marker.png", "hearts.png", "nav_arrow.png",
                         "confetti.png", "yes_no_icons.png", "battle_icons.pal", "title_banner.pal"):
                self.assertTrue(os.path.exists(os.path.join(out, name)), name)

    def test_the_packs_palettes_are_the_games_palettes(self):
        """The pack's pictures are colour numbers; they only look right in the palettes the
        generator writes for the game."""
        for name, palette in (("battle_icons.pal", art.PALETTE), ("title_banner.pal", art.BANNER_PALETTE)):
            with open(os.path.join(PACK, name)) as f:
                lines = f.read().split()
            colours = [tuple(int(v) for v in lines[i:i + 3]) for i in range(3, len(lines), 3)]
            self.assertEqual(colours, [tuple(c) for c in palette], name)

    def test_the_pack_is_the_one_that_was_delivered(self):
        with open(os.path.join(PACK, "..", "manifest.json")) as f:
            manifest = json.load(f)
        self.assertEqual(manifest["battle_order"], [name for name, _ in art.ICONS])
        for name in PACK_SHEETS:
            with open(os.path.join(PACK, name), "rb") as f:
                self.assertEqual(hashlib.sha256(f.read()).hexdigest(), manifest["graphics"][name]["sha256"], name)


if __name__ == "__main__":
    unittest.main()
