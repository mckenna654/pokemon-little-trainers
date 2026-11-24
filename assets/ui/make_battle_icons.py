#!/usr/bin/env python3
"""Draws the Little Trainers battle-menu icons (original art, generated from shapes).

    python3 assets/ui/make_battle_icons.py            # writes into game/graphics/little_trainers/
    python3 assets/ui/make_battle_icons.py --preview FILE.png   # also writes an enlarged preview

Outputs (all 16-colour indexed, GBA-ready):
    battle_icons.png   32 px wide strip, one 32x32 button per icon, in the order of ICONS below
    battle_ring.png    32x32 selection ring
    battle_marker.png  8x8 star shown on the recommended attack
    hearts.png         72x8 strip of health hearts (empty, half, full), drawn with the colours of
                       the game's own health-box palette so no extra palette is needed
    battle_icons.pal   JASC palette (index 0 is transparent, index 14 is the ring, which the game pulses)

Each button is a cream badge on the battle panel with a 24x24 icon. Shapes are rasterised with
4x supersampling, reduced to palette indices by majority vote, then given a 1 px dark outline.
"""
import math
import os
import struct
import sys
import zlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "game", "graphics", "little_trainers")

T, PANEL, DARK, WHITE, LGREY, GREY, RED, DRED, ORANGE, YELLOW, BLUE, LBLUE, GREEN, PURPLE, RING, CREAM = range(16)
PALETTE = [
    (255, 0, 255),    # 0 transparent
    (41, 82, 106),    # 1 battle panel (same as the message box)
    (40, 40, 56),     # 2 outline
    (248, 248, 248),  # 3 white
    (200, 204, 212),  # 4 light grey
    (136, 144, 160),  # 5 grey
    (232, 64, 48),    # 6 red
    (160, 40, 40),    # 7 dark red
    (248, 144, 32),   # 8 orange
    (248, 216, 56),   # 9 yellow
    (56, 120, 232),   # 10 blue
    (136, 200, 248),  # 11 light blue
    (72, 184, 80),    # 12 green
    (168, 96, 208),   # 13 purple
    (248, 216, 56),   # 14 selection ring (animated in game)
    (248, 240, 216),  # 15 badge cream
]
SS = 4  # supersampling factor


# --- shape helpers (coordinates in icon pixels, 0..24) -------------------------------------------
def poly(points):
    def inside(x, y):
        hit = False
        n = len(points)
        for i in range(n):
            x1, y1 = points[i]
            x2, y2 = points[(i + 1) % n]
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                hit = not hit
        return hit
    return inside


def ellipse(cx, cy, rx, ry=None):
    ry = rx if ry is None else ry
    return lambda x, y: ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1


def line(x1, y1, x2, y2, width):
    def inside(x, y):
        dx, dy = x2 - x1, y2 - y1
        t = max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
        return math.hypot(x - (x1 + t * dx), y - (y1 + t * dy)) <= width / 2
    return inside


def star(cx, cy, outer, inner, points, rotation=-90):
    pts = []
    for i in range(points * 2):
        r = outer if i % 2 == 0 else inner
        a = math.radians(rotation + i * 180 / points)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return poly(pts)


def both(a, b):
    return lambda x, y: a(x, y) and b(x, y)


def either(*shapes):
    return lambda x, y: any(s(x, y) for s in shapes)


def minus(a, b):
    return lambda x, y: a(x, y) and not b(x, y)


def render(layers, size=24, outline=True):
    """layers: list of (shape, colour). Returns size x size grid of palette indices (T = empty)."""
    grid = []
    for py in range(size):
        row = []
        for px in range(size):
            votes = {}
            for sy in range(SS):
                for sx in range(SS):
                    x, y = px + (sx + 0.5) / SS, py + (sy + 0.5) / SS
                    c = T
                    for shape, colour in layers:
                        if shape(x, y):
                            c = colour
                    votes[c] = votes.get(c, 0) + 1
            best = max(votes, key=lambda c: (votes[c], c != T))
            if best == T and votes.get(T, 0) < SS * SS * 0.6:      # mostly covered: keep the ink
                best = max((c for c in votes if c != T), key=lambda c: votes[c])
            row.append(best)
        grid.append(row)
    if outline:
        src = [r[:] for r in grid]
        for y in range(size):
            for x in range(size):
                if src[y][x] != T:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < size and 0 <= ny < size and src[ny][nx] not in (T, DARK):
                        grid[y][x] = DARK
                        break
    return grid


# --- the icons -------------------------------------------------------------------------------------
def icon_attack():      # impact burst
    return render([(star(12, 12, 10.5, 5.5, 8), ORANGE), (star(12, 12, 7.2, 3.4, 8, -67.5), YELLOW),
                   (ellipse(12, 12, 2.4), WHITE)])


def icon_sparkle():     # generic special attack
    return render([(star(11, 13, 9.5, 2.8, 4), YELLOW), (ellipse(11, 13, 2.2), WHITE),
                   (star(18.5, 5.5, 4.2, 1.3, 4), WHITE)])


def icon_fire():
    flame = poly([(12.5, 1.5), (15.5, 6), (19, 10.5), (19.5, 15.5), (17, 20), (12, 22), (7, 20), (4.5, 15.5),
                  (5, 11.5), (7.5, 8.5), (9, 11), (10.5, 6)])
    inner = poly([(12.5, 8), (15.5, 12.5), (16, 17), (14, 20), (12, 20.8), (10, 20), (8, 17), (8.5, 13.5), (10.5, 14)])
    return render([(flame, RED), (inner, ORANGE), (ellipse(12, 17.5, 2.4, 3), YELLOW)])


def icon_water():
    drop = either(ellipse(12, 15, 7.3), poly([(12, 1.5), (5.6, 11.5), (18.4, 11.5)]))
    return render([(drop, BLUE), (ellipse(9.2, 14.5, 1.6, 3.2), LBLUE), (ellipse(14, 19, 1.2), LBLUE)])


def icon_grass():
    leaf = both(ellipse(6.5, 6.5, 14.5), ellipse(17.5, 17.5, 14.5))     # lens shape, tip to tip
    return render([(leaf, GREEN), (line(5, 19, 18.5, 5.5, 1.3), DARK), (line(9.5, 14.5, 9.5, 9.5, 1), DARK),
                   (line(13.5, 10.5, 13.5, 6.5, 1), DARK), (line(9.5, 14.5, 14.5, 14.5, 1), DARK),
                   (line(13.5, 10.5, 17.5, 10.5, 1), DARK), (line(3, 21, 5.5, 18.5, 2), DARK)])


def icon_electric():
    return render([(poly([(14.5, 1.5), (5.5, 13.5), (10.8, 13.5), (8, 22.5), (18.5, 9.5), (13, 9.5), (17, 1.5)]), YELLOW)])


def icon_ice():
    layers = []
    for a in (0, 60, 120):
        r = math.radians(a)
        dx, dy = 10 * math.cos(r), 10 * math.sin(r)
        layers.append((line(12 - dx, 12 - dy, 12 + dx, 12 + dy, 2.2), LBLUE))
        for sign in (1, -1):
            bx, by = 12 + sign * 6.5 * math.cos(r), 12 + sign * 6.5 * math.sin(r)
            for side in (50, -50):
                rr = math.radians(a + side)
                layers.append((line(bx, by, bx + sign * 3.2 * math.cos(rr), by + sign * 3.2 * math.sin(rr), 1.6), LBLUE))
    layers.append((ellipse(12, 12, 2), WHITE))
    return render(layers)


def icon_rock():
    rock = poly([(4.5, 18), (3.5, 12), (8, 5.5), (15, 3.5), (20, 8.5), (21, 16), (17, 21), (8.5, 21)])
    return render([(rock, GREY), (poly([(8, 5.5), (15, 3.5), (13, 10), (7, 12)]), LGREY),
                   (poly([(13, 10), (20, 8.5), (21, 16), (15, 15)]), LGREY), (line(7, 12, 13, 10, 1), DARK),
                   (line(13, 10, 15, 15, 1), DARK), (line(15, 15, 17, 21, 1), DARK), (line(7, 12, 8.5, 21, 1), DARK)])


def icon_psychic():     # hypnotic eye
    return render([(ellipse(12, 12, 10.2, 7), PURPLE), (ellipse(12, 12, 7.6, 4.8), WHITE),
                   (ellipse(12, 12, 4.2), PURPLE), (ellipse(12, 12, 1.9), DARK), (ellipse(10.6, 10.6, 0.9), WHITE)])


def icon_catch():       # Poke Ball
    ball = ellipse(12, 12, 10.3)
    return render([(ball, WHITE), (both(ball, lambda x, y: y < 12), RED), (both(ball, lambda x, y: abs(y - 12) < 1.3), DARK),
                   (ellipse(12, 12, 3.6), DARK), (ellipse(12, 12, 2.3), WHITE), (ellipse(8, 7, 1.6, 1.1), WHITE)])


def icon_change():      # swap arrows
    right = poly([(2.5, 5.5), (14, 5.5), (14, 2.5), (21.5, 7.8), (14, 13), (14, 10), (2.5, 10)])
    left = poly([(21.5, 14), (10, 14), (10, 11), (2.5, 16.3), (10, 21.5), (10, 18.5), (21.5, 18.5)])
    return render([(right, BLUE), (left, GREEN)])


def icon_run():         # running shoe with speed lines
    upper = poly([(8, 16.5), (8, 7.5), (12.5, 7.5), (14.5, 11), (19, 12.5), (22, 14.5), (22.5, 16.5)])
    sole = poly([(7.5, 16.5), (22.8, 16.5), (22.8, 19.5), (7.5, 19.5)])
    return render([(upper, RED), (sole, WHITE), (line(12.5, 10.5, 15, 13.5, 1.1), WHITE),
                   (line(10.5, 10.5, 13, 13.8, 1.1), WHITE), (ellipse(10, 8.2, 1.6, 0.9), DRED),
                   (line(1.5, 9, 5.5, 9, 1.4), LGREY), (line(0.8, 13, 5.5, 13, 1.4), LGREY), (line(2, 17, 5.5, 17, 1.4), LGREY)])


# Order matters: src/battle_controller_player.c indexes the strip with the LT_ICON_* enum.
ICONS = [("attack", icon_attack), ("sparkle", icon_sparkle), ("fire", icon_fire), ("water", icon_water),
         ("grass", icon_grass), ("electric", icon_electric), ("ice", icon_ice), ("rock", icon_rock),
         ("psychic", icon_psychic), ("catch", icon_catch), ("change", icon_change), ("run", icon_run)]


def rounded(x0, y0, x1, y1, r):
    def inside(x, y):
        cx = min(max(x, x0 + r), x1 - r)
        cy = min(max(y, y0 + r), y1 - r)
        return x0 <= x <= x1 and y0 <= y <= y1 and math.hypot(x - cx, y - cy) <= r
    return inside


def button(icon):
    cell = render([(rounded(2, 2, 30, 30, 5), GREY), (rounded(3, 3, 29, 29, 4.2), CREAM)], size=32, outline=False)
    for y in range(24):
        for x in range(24):
            if icon[y][x] != T:
                cell[y + 4][x + 4] = icon[y][x]
    return cell


def ring():
    return render([(minus(rounded(0, 0, 32, 32, 6.5), rounded(2.2, 2.2, 29.8, 29.8, 4.6)), RING)], size=32, outline=False)


# --- health hearts -------------------------------------------------------------------------------
# One 8x8 tile replaces each 8-pixel slice of the HP bar. The engine asks for a tile by how many
# of the slice's 8 pixels are filled (0-8); hearts show that as empty (0), half (1-4) or full (5-8).
# Colours are indices into graphics/battle_interface/healthbox.pal (the health box's own palette).
HB_CLEAR, HB_WHITE, HB_GREY, HB_DARK, HB_FRAME, HB_RED, HB_DRED = 0, 2, 4, 5, 6, 14, 15
HEALTHBOX_PALETTE = [(0, 0, 0), (57, 57, 57), (255, 255, 255), (213, 205, 189), (131, 131, 139), (74, 65, 90),
                     (82, 106, 90), (255, 213, 82), (255, 180, 65), (222, 106, 90), (115, 255, 172), (90, 213, 131),
                     (255, 230, 57), (205, 172, 8), (255, 90, 57), (172, 65, 74)]
HEART_SHAPE = [".XX.XX..",
               "XXXXXXX.",
               "XXXXXXX.",
               ".XXXXX..",
               "..XXX..."]


def heart_tile(filled_pixels):
    red_columns = 0 if filled_pixels == 0 else 4 if filled_pixels <= 4 else 8
    rows = [[HB_CLEAR] * 8, [HB_FRAME] * 8]
    for y, line in enumerate(HEART_SHAPE):
        row = []
        for x, ch in enumerate(line):
            if ch != "X":
                row.append(HB_WHITE)
            elif x < red_columns:
                row.append(HB_DRED if y == 4 else HB_RED)
            else:
                row.append(HB_DARK if y == 4 else HB_GREY)
        rows.append(row)
    rows.append([HB_FRAME] * 8)
    return rows


def hearts_strip():
    tiles = [heart_tile(n) for n in range(9)]
    return [[px for tile in tiles for px in tile[y]] for y in range(8)]


# --- file writers ----------------------------------------------------------------------------------
def chunk(tag, body):
    return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body))


def write_indexed_png(path, rows, palette=None):
    """4-bit indexed PNG, the format the decomp's gbagfx tool expects."""
    palette = palette or PALETTE
    h, w = len(rows), len(rows[0])
    raw = bytearray()
    for row in rows:
        raw.append(0)
        for i in range(0, w, 2):
            raw.append((row[i] << 4) | row[i + 1])
    plte = b"".join(bytes(c) for c in palette)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 4, 3, 0, 0, 0))
                + chunk(b"PLTE", plte) + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))


def write_preview(path, cells, scale=4, per_row=6):
    rows_of_cells = [cells[i:i + per_row] for i in range(0, len(cells), per_row)]
    out = []
    for group in rows_of_cells:
        for y in range(32):
            line_px = []
            for cell in group + [[[PANEL] * 32] * 32] * (per_row - len(group)):
                line_px += [PANEL if c == T else c for c in cell[y]] + [PANEL] * 4
            for _ in range(scale):
                out.append([c for c in line_px for _ in range(scale)])
        out += [[PANEL] * len(out[0])] * (4 * scale)
    raw = b"".join(b"\x00" + b"".join(bytes(PALETTE[c]) for c in row) for row in out)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", len(out[0]), len(out), 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def main():
    cells = [button(draw()) for _, draw in ICONS]
    os.makedirs(OUT, exist_ok=True)
    write_indexed_png(os.path.join(OUT, "battle_icons.png"), [row for cell in cells for row in cell])
    write_indexed_png(os.path.join(OUT, "battle_ring.png"), ring())
    write_indexed_png(os.path.join(OUT, "battle_marker.png"),
                      render([(star(4, 4, 3.4, 1.5, 4), YELLOW), (ellipse(4, 4, 0.9), WHITE)], size=8))
    write_indexed_png(os.path.join(OUT, "hearts.png"), hearts_strip(), HEALTHBOX_PALETTE)
    with open(os.path.join(OUT, "battle_icons.pal"), "w", newline="\r\n") as f:
        f.write("JASC-PAL\n0100\n16\n" + "".join(f"{r} {g} {b}\n" for r, g, b in PALETTE))
    if "--preview" in sys.argv:
        selected = []
        r = ring()
        for i, cell in enumerate(cells):
            if i % 3 == 0:      # show the ring on a few buttons
                cell = [[r[y][x] if r[y][x] != T else cell[y][x] for x in range(32)] for y in range(32)]
            selected.append(cell)
        write_preview(sys.argv[sys.argv.index("--preview") + 1], selected)
    print(f"wrote {len(cells)} icons to {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
