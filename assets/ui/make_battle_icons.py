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
    title_banner.png   32x128: the "LITTLE TRAINERS" title-screen banner as four 32x32 sprites
    start_menu_icons.png  16 px wide strip of 16x16 icons for the Start menu, drawn with the
                       colours every field menu window already has (white, greys, red, orange,
                       greens, blues), so no extra palette is needed
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


def render(layers, size=24, outline=True, outline_colour=None):
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
                    ink = DARK if outline_colour is None else outline_colour
                    if 0 <= nx < size and 0 <= ny < size and src[ny][nx] not in (T, ink):
                        grid[y][x] = ink
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


# --- Start menu icons ----------------------------------------------------------------------------
# Indices into graphics/interface/std_menu.pal / text_window/stdpal_*.pal (entries 0-9 are shared).
M_WHITE, M_DARK, M_LIGHT, M_RED, M_ORANGE, M_GREEN, M_LGREEN, M_BLUE, M_LBLUE = 1, 2, 3, 4, 5, 6, 7, 8, 9
MENU_PALETTE = [(115, 205, 164), (255, 255, 255), (98, 98, 98), (213, 213, 205), (230, 8, 8), (255, 189, 115),
                (32, 156, 8), (148, 246, 148), (49, 82, 205), (164, 197, 246)] + [(0, 0, 0)] * 6


def menu_icon(layers):
    """14x14 icon in the top-left of a 16x16 cell (rows are 15 px apart in the Start menu)."""
    icon = render(layers, size=14)          # outline colour DARK (2) is dark grey in this palette too
    return [row + [T, T] for row in icon] + [[T] * 16, [T] * 16]


def start_menu_icons():
    ball = ellipse(7, 7, 5.8)
    pokedex = menu_icon([(rounded(1, 1, 13, 13, 2.5), M_RED), (ellipse(4.6, 4.6, 2.3), M_WHITE), (ellipse(4.6, 4.6, 1.5), M_LBLUE),
                         (line(8.5, 4, 11.5, 4, 1.2), M_ORANGE), (rounded(3, 8, 11, 11.5, 1), M_WHITE)])
    pokemon = menu_icon([(ball, M_WHITE), (both(ball, lambda x, y: y < 7), M_RED), (both(ball, lambda x, y: abs(y - 7) < 0.9), M_DARK),
                         (ellipse(7, 7, 2.3), M_DARK), (ellipse(7, 7, 1.3), M_WHITE)])
    bag = menu_icon([(minus(ellipse(7, 3.6, 2.8), ellipse(7, 3.6, 1.5)), M_ORANGE), (rounded(2, 4, 12, 13, 2.6), M_GREEN),
                     (rounded(2, 4, 12, 8, 2.4), M_LGREEN), (line(2.5, 8, 11.5, 8, 0.9), M_DARK), (rounded(5.8, 7, 8.2, 9.6, 0.6), M_ORANGE)])
    card = menu_icon([(rounded(1, 2.5, 13, 11.5, 1.6), M_LBLUE), (ellipse(4.5, 6, 1.7), M_WHITE), (ellipse(4.5, 9.8, 2.5, 1.7), M_WHITE),
                      (line(8, 5.5, 11.3, 5.5, 1), M_BLUE), (line(8, 8, 11.3, 8, 1), M_BLUE)])
    save = menu_icon([(rounded(2, 1.5, 12.5, 12.5, 1.4), M_BLUE), (poly([(4.2, 3), (11, 3), (11, 11), (4.2, 11)]), M_WHITE),
                      (line(5.5, 6.5, 9.8, 6.5, 0.9), M_LIGHT), (line(5.5, 8.7, 9.8, 8.7, 0.9), M_LIGHT),
                      (poly([(8.2, 1.5), (10.4, 1.5), (10.4, 5.6), (9.3, 4.6), (8.2, 5.6)]), M_RED)])
    option = menu_icon([(star(7, 7, 6.4, 4.5, 8), M_LIGHT), (ellipse(7, 7, 4.5), M_LIGHT), (ellipse(7, 7, 2), M_DARK),
                        (ellipse(7, 7, 1.1), M_WHITE)])
    close = menu_icon([(line(3.2, 3.2, 10.8, 10.8, 2.7), M_RED), (line(10.8, 3.2, 3.2, 10.8, 2.7), M_RED)])
    retire = menu_icon([(poly([(4.6, 1.8), (12.3, 4.6), (4.6, 7.4)]), M_ORANGE), (line(4, 1.5, 4, 12.6, 1.3), M_DARK)])
    # Order matches the STARTMENU_* enum in src/start_menu.c
    return [pokedex, pokemon, bag, card, save, option, close, retire, card]


# --- navigation arrow ----------------------------------------------------------------------------
# Drawn with the player character's own sprite palette (graphics/object_events/palettes/player.pal),
# which is always loaded in the overworld: yellow 13, dark yellow 14, black 15.
PLAYER_PALETTE = [(131, 123, 164), (172, 123, 65), (255, 197, 148), (222, 148, 115), (123, 65, 65), (65, 65, 213),
                  (57, 57, 123), (115, 164, 197), (106, 41, 41), (238, 238, 255), (180, 180, 213), (255, 106, 74),
                  (197, 57, 57), (255, 222, 90), (189, 156, 57), (0, 0, 0)]


def nav_arrow_sheet():
    """32x16: an arrow pointing up, then one pointing right (the game flips them for down/left)."""
    up = [(7.5, 1.5), (13.5, 8.5), (10, 8.5), (10, 14.5), (5, 14.5), (5, 8.5), (1.5, 8.5)]
    right = [(15 - y, x) for x, y in up]
    frames = []
    for pts in (up, right):
        shade = poly([(x + 0.9, y + 0.9) for x, y in pts])
        frames.append(render([(shade, 14), (poly(pts), 13)], size=16, outline_colour=15))
    return [frames[0][y] + frames[1][y] for y in range(16)]


# --- title screen banner -------------------------------------------------------------------------
# "LITTLE / TRAINERS" in a chunky pixel font of our own, 128x32, cut into four 32x32 sprites.
FONT = {
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
}
BANNER_PALETTE = [(255, 0, 255), (40, 40, 56), (255, 222, 90), (255, 255, 255), (232, 120, 32)] + [(0, 0, 0)] * 11
B_OUTLINE, B_FILL, B_SHINE, B_SHADE = 1, 2, 3, 4


def title_banner():
    width, height, scale = 128, 32, 2
    grid = [[T] * width for _ in range(height)]
    for line, word in enumerate(("LITTLE", "TRAINERS")):
        x0 = (width - len(word) * 6 * scale + scale) // 2
        y0 = 1 + line * 16
        for i, ch in enumerate(word):
            for y, row in enumerate(FONT[ch]):
                for x, bit in enumerate(row):
                    if bit == "1":
                        for sy in range(scale):
                            for sx in range(scale):
                                colour = B_SHINE if (y == 0 and sy == 0) else B_SHADE if (y == 6 and sy == 1) else B_FILL
                                grid[y0 + y * scale + sy][x0 + (i * 6 + x) * scale + sx] = colour
    src = [r[:] for r in grid]
    for y in range(height):                 # dark outline, including diagonals, so it reads on any background
        for x in range(width):
            if src[y][x] != T:
                continue
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if 0 <= y + dy < height and 0 <= x + dx < width and src[y + dy][x + dx] not in (T, B_OUTLINE):
                        grid[y][x] = B_OUTLINE
    # four 32x32 frames stacked vertically, left to right
    return [grid[y][f * 32:(f + 1) * 32] for f in range(4) for y in range(32)]


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
    write_indexed_png(os.path.join(OUT, "nav_arrow.png"), nav_arrow_sheet(), PLAYER_PALETTE)
    write_indexed_png(os.path.join(OUT, "title_banner.png"), title_banner(), BANNER_PALETTE)
    with open(os.path.join(OUT, "title_banner.pal"), "w", newline="\r\n") as f:
        f.write("JASC-PAL\n0100\n16\n" + "".join(f"{r} {g} {b}\n" for r, g, b in BANNER_PALETTE))
    menu_cells = start_menu_icons()
    write_indexed_png(os.path.join(OUT, "start_menu_icons.png"), [row for cell in menu_cells for row in cell], MENU_PALETTE)
    if "--menu-preview" in sys.argv:
        big = []
        for y in range(16):
            row = []
            for cell in menu_cells:
                row += [MENU_PALETTE[1] if c == T else MENU_PALETTE[c] for c in cell[y]]
            for _ in range(8):
                big.append([c for c in row for _ in range(8)])
        raw = b"".join(b"\x00" + b"".join(bytes(c) for c in row) for row in big)
        with open(sys.argv[sys.argv.index("--menu-preview") + 1], "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", len(big[0]), len(big), 8, 2, 0, 0, 0))
                    + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
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
