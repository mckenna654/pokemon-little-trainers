"""Checks on the art we generate ourselves (assets/ui/make_battle_icons.py)."""
import importlib.util
import os
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
spec = importlib.util.spec_from_file_location("make_battle_icons", os.path.join(ROOT, "assets", "ui", "make_battle_icons.py"))
art = importlib.util.module_from_spec(spec)
spec.loader.exec_module(art)


class TitleBanner(unittest.TestCase):
    def banner(self):
        frames = art.title_banner()             # four 32x32 frames stacked vertically
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

    def test_the_letters_stand_out_from_the_plaque(self):
        rows = self.banner()
        colours = {c for row in rows for c in row} - {art.T}
        self.assertGreaterEqual(len(colours), 3, "plaque, border and lettering")


if __name__ == "__main__":
    unittest.main()
