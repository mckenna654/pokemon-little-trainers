#!/usr/bin/env python3
"""Turn the large illustrations in v1/source/ into the small pictures the game uses (v1/gba/).

    python3 assets/generated/build_pack.py      # about two minutes; needs nothing but Python

Writes only inside this pack. `assets/ui/make_battle_icons.py` then copies the three illustrated
sheets (battle buttons, Start menu pictures, title plaque) into the game, so after changing a
source picture run this, then that, then `scripts/build.sh`.

The first version of this script (Codex, 2026-11-25) resized with an image library: smoothly for
the icons, by nearest pixel for the title. On the compiled screens the title's letters had run
together ("UTTLE TRAINERS") and the green bag had come out grey. Every picture is now shrunk by
vote instead (see shrink.py), which needs no image library and can be checked by the unit tests.
"""
import hashlib
import importlib.util
import json
import struct
import zlib
from pathlib import Path

import shrink

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PACK = HERE / "v1"
SOURCE = PACK / "source"
OUT = PACK / "gba"
PREVIEW = PACK / "preview"
spec = importlib.util.spec_from_file_location("legacy_art", ROOT / "assets/ui/make_battle_icons.py")
art = importlib.util.module_from_spec(spec)
spec.loader.exec_module(art)
BATTLE = [name for name, _ in art.ICONS]
MENU = ["pokedex", "pokemon", "bag", "card", "save", "option", "close", "retire", "card"]
BATTLE_COLOURS = list(range(2, 14))     # not 0 (see-through), 1 (panel) or 14 (the pulsing ring) or 15 (button cream)
MENU_COLOURS = [1, 2, 3, 4, 5, 6, 8, 9]   # the colours every field menu window has, except the pale green (7):
                                        # on the menu's white it left the bag with no edge to speak of
TITLE_COLOURS = [1, 2, 3, 4]
PAPER = (241, 239, 231)                 # preview background


def menu_source(name):
    """CATCH's capture ball doubles as the Pokémon entry's picture."""
    return SOURCE / "battle/catch.png" if name == "pokemon" else SOURCE / "menu" / f"{name}.png"


def battle_button(name):
    return art.button(shrink.shrink(SOURCE / "battle" / f"{name}.png", (24, 24), art.PALETTE, BATTLE_COLOURS))


def menu_picture(name):
    """14x14 in the top-left of a 16x16 cell: the Start menu's rows are 15 pixels apart."""
    return shrink.shrink(menu_source(name), (16, 16), art.MENU_PALETTE, MENU_COLOURS, box=(14, 14))


def title_plaque():
    """128x32. Generated pictures have faint see-through blemishes; none may stay inside the
    plaque, or the title screen's flames would show through it."""
    # The letters are fat and the gaps between them are about one game pixel wide, so the plaque
    # colour counts double (a gap survives when it covers a third of a pixel) and the thin border
    # double again. With an even vote the two Ts of LITTLE join and the bottom border breaks up.
    rows = shrink.shrink(SOURCE / "title/title.png", (128, 32), art.BANNER_PALETTE, TITLE_COLOURS,
                         weights={art.B_PLAQUE: 2, art.B_SHADE: 4})
    for row in rows:
        ink = [x for x, c in enumerate(row) if c]
        if ink:
            for x in range(ink[0], ink[-1] + 1):
                if row[x] == 0:
                    row[x] = art.B_PLAQUE
    return rows


def as_frames(rows, width=32):
    """A wide picture as the game wants it: `width`-pixel frames stacked vertically."""
    return [row[f * width:(f + 1) * width] for f in range(len(rows[0]) // width) for row in rows]


# --- writers ---------------------------------------------------------------------------------------
def write(name, rows, palette):
    art.write_indexed_png(str(OUT / name), rows, palette)


def pal(name, colours):
    (OUT / name).write_text("JASC-PAL\n0100\n16\n" + "".join(f"{r} {g} {b}\n" for r, g, b in colours))


def write_rgb(path, image):
    def chunk(tag, body):
        return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body))

    raw = b"".join(b"\x00" + bytes(v for pixel in row for v in pixel) for row in image)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", len(image[0]), len(image), 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def enlarged(rows, palette, scale, background=PAPER):
    return [[palette[c] if c else background for c in row for _ in range(scale)] for row in rows for _ in range(scale)]


def before_after(name, old, new, palette, per_row, scale, gap=4):
    """Pairs in sheet order, left to right then down: the old shape drawing above, the
    illustration below. (No labels: this script draws no text.)"""
    size = len(old[0])
    image = []
    for start in range(0, len(old), per_row):
        for cells in (old[start:start + per_row], new[start:start + per_row]):
            for y in range(size):
                image.append([c for cell in cells for c in cell[y] + [0] * gap] + [0] * (size + gap) * (per_row - len(cells)))
            image += [[0] * (size + gap) * per_row] * gap
        image += [[0] * (size + gap) * per_row] * (2 * gap)
    write_rgb(PREVIEW / name, enlarged(image, palette, scale))


# --- checks ----------------------------------------------------------------------------------------
def validate():
    expected = {"battle_icons.png": (32, 32 * len(BATTLE)), "battle_ring.png": (32, 32),
                "battle_marker.png": (8, 8), "hearts.png": (72, 8), "nav_arrow.png": (16, 48),
                "confetti.png": (32, 8), "start_menu_icons.png": (16, 16 * len(MENU)),
                "yes_no_icons.png": (16, 32), "title_banner.png": (32, 128)}
    report = {}
    for name, size in expected.items():
        rows = art.read_indexed_png(str(OUT / name))       # refuses anything but a 4-bit indexed picture
        if (len(rows[0]), len(rows)) != size:
            raise ValueError(f"Wrong size: {name}")
        report[name] = {"size": list(size), "bit_depth": 4, "palette_entries": 16,
                        "sha256": hashlib.sha256((OUT / name).read_bytes()).hexdigest()}
    if any(14 in row for row in art.read_indexed_png(str(OUT / "battle_icons.png"))):
        raise ValueError("A battle picture uses the pulsing ring colour")
    menu = art.read_indexed_png(str(OUT / "start_menu_icons.png"))
    for i in range(len(MENU)):
        if any(menu[i * 16 + 14]) or any(menu[i * 16 + 15]):
            raise ValueError("A menu picture runs into the next menu row")
    sources = {}
    for path in sorted(SOURCE.rglob("*.png")):
        rows = shrink.read_rgba(path)[2]                    # refuses anything but 8-bit RGBA
        if min(min(row[3::4]) for row in rows) != 0 or max(max(row[3::4]) for row in rows) < 192:
            raise ValueError(f"Source must have a see-through background and solid ink: {path}")
        if path.stat().st_size > 4 * 1024 * 1024:
            raise ValueError(f"Source is too large for the repository: {path}")
        sources[str(path.relative_to(PACK))] = hashlib.sha256(path.read_bytes()).hexdigest()
    if len(sources) != 27:
        raise ValueError(f"Expected 27 source pictures, found {len(sources)}")
    (PACK / "manifest.json").write_text(json.dumps({"battle_order": BATTLE, "menu_order": MENU,
                                                   "graphics": report, "source_sha256": sources}, indent=2) + "\n")
    print(f"checked {len(sources)} sources and {len(report)} game sheets")


def main():
    OUT.mkdir(exist_ok=True)
    PREVIEW.mkdir(exist_ok=True)
    battle = [battle_button(name) for name in BATTLE]
    write("battle_icons.png", [row for cell in battle for row in cell], art.PALETTE)
    pal("battle_icons.pal", art.PALETTE)
    # The fine control symbols stay the project's own pixel art; copies are kept here for reference.
    for name, rows, palette in [
        ("battle_ring.png", art.ring(), art.PALETTE),
        ("battle_marker.png", art.render([(art.star(4, 4, 3.4, 1.5, 4), art.YELLOW), (art.ellipse(4, 4, .9), art.WHITE)], size=8), art.PALETTE),
        ("hearts.png", art.hearts_strip(), art.HEALTHBOX_PALETTE),
        ("nav_arrow.png", art.nav_arrow_sheet(), art.PLAYER_PALETTE),
        ("confetti.png", art.confetti_sheet(), art.PLAYER_PALETTE),
        ("yes_no_icons.png", [row for cell in art.yes_no_icons() for row in cell], art.MENU_PALETTE),
    ]:
        write(name, rows, palette)
    drawn = art.start_menu_icons()
    menu = [drawn[i] if name in ("close", "retire") else menu_picture(name) for i, name in enumerate(MENU)]
    write("start_menu_icons.png", [row for cell in menu for row in cell], art.MENU_PALETTE)
    title = title_plaque()
    write("title_banner.png", as_frames(title), art.BANNER_PALETTE)
    pal("title_banner.pal", art.BANNER_PALETTE)

    # Previews: what changed, enlarged. The game screens themselves are the real check.
    before_after("battle-before-after.png", [art.button(draw()) for _, draw in art.ICONS], battle, art.PALETTE, 7, 4)
    before_after("menu-before-after.png", drawn, menu, art.MENU_PALETTE, 9, 6, gap=2)
    write_rgb(PREVIEW / "title.png", enlarged(title, art.BANNER_PALETTE, 8, (64, 176, 160)))
    write_rgb(PREVIEW / "menu-native.png", enlarged([[c for cell in menu for c in cell[y]] for y in range(16)], art.MENU_PALETTE, 1, (255, 255, 255)))
    # Larger menu pictures on battle-style buttons, for a future picture menu; not used by the game.
    large = PACK / "menu-32"
    large.mkdir(exist_ok=True)
    for name in sorted(set(MENU) - {"close", "retire"}):
        art.write_indexed_png(str(large / f"{name}.png"),
                              art.button(shrink.shrink(menu_source(name), (24, 24), art.PALETTE, BATTLE_COLOURS)), art.PALETTE)
    validate()


if __name__ == "__main__":
    main()
