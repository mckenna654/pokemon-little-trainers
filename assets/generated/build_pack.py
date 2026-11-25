#!/usr/bin/env python3
"""Convert the generated illustrations into existing Little Trainers graphics contracts.

Requires Pillow (requirements.txt). Does not write to game/ or alter the legacy generator.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

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


def illustration(path, width, height, resample):
    image = Image.open(path).convert("RGBA")
    # Crop by solid ink, excluding faint generated edge halos. Source alpha is preserved on disk.
    bounds = image.getchannel("A").point(lambda x: 255 if x >= 192 else 0).getbbox()
    if bounds is None:
        raise ValueError(f"No solid artwork: {path}")
    return ImageOps.contain(image.crop(bounds), (width, height), resample)


def indexed(path, size, palette, allowed, box, resample=Image.Resampling.LANCZOS):
    image = illustration(path, *box, resample)
    canvas = Image.new("RGBA", size)
    canvas.paste(image, ((box[0] - image.width) // 2, (box[1] - image.height) // 2))
    rows = []
    for y in range(size[1]):
        row = []
        for x in range(size[0]):
            r, g, b, a = canvas.getpixel((x, y))
            row.append(0 if a < 160 else min(allowed, key=lambda i: sum((v - c) ** 2 for v, c in zip((r, g, b), palette[i]))))
        rows.append(row)
    return rows


def write(name, rows, palette):
    art.write_indexed_png(str(OUT / name), rows, palette)
    return rows


def pal(name, colours):
    (OUT / name).write_text("JASC-PAL\n0100\n16\n" + "".join(f"{r} {g} {b}\n" for r, g, b in colours))


def rgba(rows, palette):
    result = Image.new("RGBA", (len(rows[0]), len(rows)))
    result.putdata([(*palette[c], 0 if c == 0 else 255) for row in rows for c in row])
    return result


def contact(name, labels, old, new, palette, cell_size):
    scale, cols = (4, 6) if cell_size == 32 else (6, 5)
    width, height = cell_size * scale + 44, cell_size * scale * 2 + 82
    sheet = Image.new("RGB", (cols * width, ((len(labels) + cols - 1) // cols) * height), "#f1efe7")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=14)
    for i, label in enumerate(labels):
        x, y = i % cols * width, i // cols * height
        draw.text((x + 8, y + 6), f"{i:02} {label}", fill="#282838", font=font)
        for j, rows in enumerate((old[i], new[i])):
            icon = rgba(rows, palette).resize((cell_size * scale,) * 2, Image.Resampling.NEAREST)
            sheet.paste(icon, (x + 28, y + 30 + j * (cell_size * scale + 28)), icon)
            draw.text((x + 4, y + 30 + j * (cell_size * scale + 28)), "old" if j == 0 else "new", fill="#282838", font=font)
    sheet.save(PREVIEW / name)


def validate():
    expected = {"battle_icons.png": (32, 672), "battle_ring.png": (32, 32),
                "battle_marker.png": (8, 8), "hearts.png": (72, 8), "nav_arrow.png": (16, 32),
                "confetti.png": (32, 8), "start_menu_icons.png": (16, 144),
                "yes_no_icons.png": (16, 32), "title_banner.png": (32, 128)}
    report = {}
    for name, size in expected.items():
        path = OUT / name
        data = path.read_bytes()
        with Image.open(path) as image:
            if image.size != size or image.mode != "P" or data[24:26] != bytes([4, 3]):
                raise ValueError(f"Wrong graphics contract: {name}")
            if max(image.get_flattened_data()) > 15:
                raise ValueError(f"Out of palette: {name}")
        report[name] = {"size": list(size), "bit_depth": 4, "palette_entries": 16,
                        "sha256": hashlib.sha256(data).hexdigest()}
    # No icon ink may use the engine's cycling selection-ring index.
    pixels = list(Image.open(OUT / "battle_icons.png").get_flattened_data())
    if 14 in pixels:
        raise ValueError("Battle icon uses animated ring colour")
    menu = Image.open(OUT / "start_menu_icons.png")
    for i in range(9):
        if any(menu.getpixel((x, i * 16 + y)) for x in range(16) for y in (14, 15)):
            raise ValueError("Menu icon exceeds the 15-pixel row spacing")
    packed = Image.open(OUT / "title_banner.png")
    for y in range(32):
        row = [packed.getpixel((x % 32, x // 32 * 32 + y)) for x in range(128)]
        ink = [x for x, c in enumerate(row) if c]
        if ink and any(c == 0 for c in row[ink[0]:ink[-1] + 1]):
            raise ValueError("Hole inside title plaque")
    sources = {}
    for path in sorted(SOURCE.rglob("*.png")):
        with Image.open(path) as image:
            low, high = image.convert("RGBA").getchannel("A").getextrema()
            if image.mode != "RGBA" or low != 0 or high < 192:
                raise ValueError(f"Source must preserve true transparency: {path}")
        if path.stat().st_size > 4 * 1024 * 1024:
            raise ValueError(f"Source exceeds repository size guard: {path}")
        sources[str(path.relative_to(PACK))] = hashlib.sha256(path.read_bytes()).hexdigest()
    if len(sources) != 27:
        raise ValueError(f"Expected 27 generated source images, found {len(sources)}")
    (PACK / "manifest.json").write_text(json.dumps({"battle_order": BATTLE, "menu_order": MENU,
                                                   "graphics": report, "source_sha256": sources}, indent=2) + "\n")
    print(f"Validated {len(sources)} transparent sources and {len(report)} four-bit PNGs; palettes, sprite layout, solid plaque and row spacing checked")


def main():
    OUT.mkdir(exist_ok=True)
    PREVIEW.mkdir(exist_ok=True)
    battle = [art.button(indexed(SOURCE / "battle" / f"{name}.png", (24, 24), art.PALETTE,
                                list(range(2, 14)), (24, 24))) for name in BATTLE]
    write("battle_icons.png", [row for cell in battle for row in cell], art.PALETTE)
    pal("battle_icons.pal", art.PALETTE)
    # Fine control symbols retain the project's existing original pixel art.
    for name, rows, palette in [
        ("battle_ring.png", art.ring(), art.PALETTE),
        ("battle_marker.png", art.render([(art.star(4, 4, 3.4, 1.5, 4), art.YELLOW), (art.ellipse(4, 4, .9), art.WHITE)], size=8), art.PALETTE),
        ("hearts.png", art.hearts_strip(), art.HEALTHBOX_PALETTE),
        ("nav_arrow.png", art.nav_arrow_sheet(), art.PLAYER_PALETTE),
        ("confetti.png", art.confetti_sheet(), art.PLAYER_PALETTE),
        ("yes_no_icons.png", [row for cell in art.yes_no_icons() for row in cell], art.MENU_PALETTE),
    ]:
        write(name, rows, palette)
    legacy = art.start_menu_icons()
    menu = []
    large_menu = []
    for i, name in enumerate(MENU):
        if name in ("close", "retire"):
            menu.append(legacy[i])
            large_menu.append(None)
        else:
            path = SOURCE / "battle/catch.png" if name == "pokemon" else SOURCE / "menu" / f"{name}.png"
            menu.append(indexed(path, (16, 16), art.MENU_PALETTE, list(range(1, 10)), (14, 14)))
            large_menu.append(art.button(indexed(path, (24, 24), art.PALETTE, list(range(2, 14)), (24, 24))))
    write("start_menu_icons.png", [row for cell in menu for row in cell], art.MENU_PALETTE)
    # Generated title is a separate 128x32 wordmark, packed as four vertical 32x32 frames.
    title = indexed(SOURCE / "title/title.png", (128, 32), art.BANNER_PALETTE, [1, 2, 3, 4], (128, 32), Image.Resampling.NEAREST)
    # Alpha defects inside the solid plaque must not expose the original title animation.
    for row in title:
        ink = [x for x, c in enumerate(row) if c]
        if ink:
            for x in range(ink[0], ink[-1] + 1):
                if row[x] == 0:
                    row[x] = 1
    write("title_banner.png", [row[f * 32:(f + 1) * 32] for f in range(4) for row in title], art.BANNER_PALETTE)
    pal("title_banner.pal", art.BANNER_PALETTE)
    rgba(title, art.BANNER_PALETTE).resize((1024, 256), Image.Resampling.NEAREST).save(PREVIEW / "title.png")
    contact("battle-before-after.png", BATTLE, [art.button(draw()) for _, draw in art.ICONS], battle, art.PALETTE, 32)
    contact("menu-before-after.png", MENU, legacy, menu, art.MENU_PALETTE, 16)
    # Native-size menu strip for checking the real footprint without enlargement.
    strip = Image.new("RGBA", (16 * 9, 16))
    for i, cell in enumerate(menu):
        strip.paste(rgba(cell, art.MENU_PALETTE), (i * 16, 0))
    strip.save(PREVIEW / "menu-native.png")
    # Optional larger originals for Claude's future picture-menu work; not drop-in GBA sheets.
    large_dir = PACK / "menu-32"
    large_dir.mkdir(exist_ok=True)
    for name, cell in zip(MENU, large_menu):
        if cell is not None:
            art.write_indexed_png(str(large_dir / f"{name}.png"), cell, art.PALETTE)
    validate()


if __name__ == "__main__":
    main()
