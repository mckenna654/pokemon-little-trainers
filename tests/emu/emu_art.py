"""The pictures in the built game are the ones in the art pack (`assets/generated/v1/gba/`).

The pack is the source of the battle buttons, the Start menu pictures and the title plaque. The
drawing program in `assets/ui/` once made all three, and running it used to overwrite them, so
this checks the game itself rather than the files it was built from. No emulator is needed: the
game stores these pictures uncompressed, so each one can be looked for in the ROM.
"""
import os
import unittest

from .firered import ROM, ROOT
from tests.test_art import PACK, PACK_SHEETS, art


def as_game_tiles(rows):
    """A picture as the GBA stores it: 8x8 tiles in reading order, two pixels to a byte."""
    out = bytearray()
    for ty in range(0, len(rows), 8):
        for tx in range(0, len(rows[0]), 8):
            for y in range(ty, ty + 8):
                for x in range(tx, tx + 8, 2):
                    out.append(rows[y][x] | rows[y][x + 1] << 4)
    return bytes(out)


class PackPicturesAreInTheGame(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(ROM, "rb") as f:
            cls.rom = f.read()

    def test_every_pack_picture_is_in_the_game(self):
        for name in PACK_SHEETS:
            with self.subTest(picture=name):
                rows = art.read_indexed_png(os.path.join(PACK, name))
                self.assertTrue(as_game_tiles(rows) in self.rom, f"{name} in the game is not the pack's")

    def test_the_old_drawn_pictures_are_gone(self):
        old = {"battle_icons.png": [row for _, draw in art.ICONS for row in art.button(draw())],
               "start_menu_icons.png": [row for cell in art.start_menu_icons() for row in cell],
               "title_banner.png": art.title_banner()}
        for name, rows in old.items():
            with self.subTest(picture=name):
                self.assertFalse(as_game_tiles(rows) in self.rom, f"the drawn {name} is still in the game")


if __name__ == "__main__":
    unittest.main()
