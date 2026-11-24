"""Screen tour: play through the screens a child sees and save a picture of every different one.

Automated tests read the game's memory; they do not look at the screen. This tool is for looking.
It walks the opening of the game, the first rival battle, a wild battle and a catch, the menus and
a few special moments, pressing A like a child, and writes numbered contact sheets for a reviewer
(a person, or an agent using the `playtest` skill) to inspect one by one.

    python3 -m tests.emu.screen_tour            # -> builds/screenshots/tour/sheet-01.png ...

Nothing here asserts anything. Add a scene whenever a new kind of screen is added to the game.
"""
import hashlib
import os
import struct
import sys
import zlib

from . import story
from .checkpoints import game_at
from .firered import FireRed, SHOTS

OUT = os.path.join(SHOTS, "tour")
LEADER_BROCK = 414
FLAG_BADGE02_GET = 0x821
PER_SHEET, COLUMNS, SCALE, GAP = 12, 3, 3, 12


class Tour:
    def __init__(self):
        os.makedirs(OUT, exist_ok=True)
        for name in os.listdir(OUT):
            if name.endswith(".png"):
                os.remove(os.path.join(OUT, name))
        self.shots = []         # (path, scene)
        self.seen = set()

    def shot(self, g, scene):
        """Save the screen unless an identical picture has been saved already."""
        path = os.path.join(OUT, f"shot-{len(self.shots) + 1:03d}.png")
        g.screenshot(path)
        with open(path, "rb") as f:
            digest = hashlib.sha1(f.read()).hexdigest()
        if digest in self.seen:
            os.remove(path)
            return
        self.seen.add(digest)
        self.shots.append((path, scene))

    def press_through(self, g, scene, until, max_presses=400, every=1, key="A"):
        """Press a key until `until()`; picture before every `every`-th press."""
        for i in range(max_presses):
            if until():
                return
            if i % every == 0:
                self.shot(g, scene)
            if g.callback2() == "CB2_NamingScreen":
                self.shot(g, scene + " (name screen)")
            g.press(key, hold=3, wait=17)
        self.shot(g, scene + " (gave up here)")


def tour():
    t = Tour()

    # 1. Power-on to the bedroom, A only
    g = FireRed()
    for frame in (200, 400, 800, 1200):
        g.frames(frame - g.frame)
        t.shot(g, "power-on and title")
    t.press_through(g, "new game: the Professor's talk", lambda: g.callback2() == "CB2_Overworld", every=4)
    g.frames(120)
    t.shot(g, "bedroom with the arrow")
    g.follow_arrow(lambda: g.location() == (3, 0) and g.free_to_move(), max_actions=400, what="Pallet Town")
    g.frames(40)
    t.shot(g, "Pallet Town with the arrow")
    for step in range(12):                       # a few steps along the arrow, one picture each
        arrow = g.nav_arrow()
        if not g.free_to_move() or not arrow:
            break
        g.step(arrow)
        g.frames(6)
        if step % 3 == 0:
            t.shot(g, "walking with the arrow")
    g.close()

    # 2. The first rival battle, every message
    g = game_at("starter")
    t.shot(g, "Oak's lab with a starter")
    story.start_rival_battle(g)
    t.press_through(g, "first rival battle", lambda: not g.in_battle() and g.free_to_move(), max_presses=500, every=2)
    g.close()

    # 3. A wild battle: every button, then a catch
    g = game_at("route1")
    t.shot(g, "Route 1")
    story.find_wild_battle(g)
    g.wait_action_menu()
    for _ in range(4):
        t.shot(g, "wild battle menu, each button")
        g.press("RIGHT", wait=20)
    g.wait_action_menu()
    g.catch()
    t.press_through(g, "catching", lambda: not g.in_battle() and g.callback2() == "CB2_Overworld", every=2)

    # 4. Field menus
    g.settle()
    g.press("START", wait=40)
    t.shot(g, "Start menu")
    for _ in range(5):
        g.press("DOWN", wait=12)
        t.shot(g, "Start menu, each entry")
    g.press("B", wait=40)
    g.press("START", wait=40)
    g.press("A", wait=120)
    t.shot(g, "party screen from the Start menu")
    g.press("A", wait=40)
    t.shot(g, "party screen, a Pokemon chosen")
    for _ in range(4):
        g.press("B", wait=60)
    g.press("START", wait=40)
    g.press("DOWN", wait=12)
    g.press("A", wait=120)
    t.shot(g, "bag")
    for _ in range(4):
        g.press("B", wait=60)
    g.press("START", wait=40)
    for _ in range(2):
        g.press("DOWN", wait=12)
    g.press("A", wait=60)
    t.press_through(g, "saving", g.free_to_move, max_presses=60)
    g.press("START", wait=40)
    for _ in range(3):
        g.press("DOWN", wait=12)
    g.press("A", wait=90)
    t.shot(g, "options")
    g.press("B", wait=120)
    g.press("B", wait=60)
    g.run_script([0x6E, 20, 8], wait=False)       # a plain yes/no question
    g.frames(30)
    t.shot(g, "yes/no box")
    g.press("B", wait=40)

    # 5. A gym leader: the trainer battle menu, a beaten Pokemon, the party screen in battle
    g.settle()
    g.start_trainer_battle(LEADER_BROCK)
    g.wait_action_menu()
    for _ in range(3):
        t.shot(g, "trainer battle menu, each button")
        g.press("RIGHT", wait=20)
    g.wait_action_menu()
    g.set_battle_hp(0, 1)                         # set-up: the lead is beaten by the next hit
    g.set_battle_hp(1, 300)
    g.attack()
    t.press_through(g, "a beaten Pokemon and the party screen",
                    lambda: g.at_action_menu() or not g.in_battle(), max_presses=200, every=2)
    if g.in_battle():
        g.set_battle_hp(1, 1)
        t.press_through(g, "winning against a leader", lambda: not g.in_battle() and g.free_to_move(),
                        max_presses=600, every=8)

    # 6. Badge confetti
    g.settle()
    g.run_script([0x29, *struct.pack("<H", FLAG_BADGE02_GET)])
    g.frames(60)
    t.shot(g, "badge confetti")
    g.close()
    return t.shots


# --- contact sheets (no image library needed) ---------------------------------------------------
def read_png(path):
    with open(path, "rb") as f:
        data = f.read()
    pos, idat, width, height, colour_type = 8, b"", 0, 0, 2
    while pos < len(data):
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if kind == b"IHDR":
            width, height, _, colour_type = struct.unpack(">IIBB", body[:10])
        elif kind == b"IDAT":
            idat += body
    bpp = {2: 3, 6: 4}[colour_type]
    raw, stride = zlib.decompress(idat), width * bpp
    rows, prev, p = [], bytearray(stride), 0
    for _ in range(height):
        kind, line = raw[p], bytearray(raw[p + 1:p + 1 + stride])
        p += 1 + stride
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if kind == 1:
                line[i] = (line[i] + a) & 255
            elif kind == 2:
                line[i] = (line[i] + b) & 255
            elif kind == 3:
                line[i] = (line[i] + (a + b) // 2) & 255
            elif kind == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append([tuple(line[x * bpp:x * bpp + 3]) for x in range(width)])
        prev = line
    return width, height, rows


def write_sheet(paths, out):
    rows_n = (len(paths) + COLUMNS - 1) // COLUMNS
    width = COLUMNS * 240 * SCALE + (COLUMNS + 1) * GAP
    height = rows_n * 160 * SCALE + (rows_n + 1) * GAP
    image = [[(24, 28, 40)] * width for _ in range(height)]
    for i, path in enumerate(paths):
        w, h, pixels = read_png(path)
        ox = GAP + (i % COLUMNS) * (240 * SCALE + GAP)
        oy = GAP + (i // COLUMNS) * (160 * SCALE + GAP)
        for y in range(h):
            line = [c for c in pixels[y] for _ in range(SCALE)]
            for k in range(SCALE):
                image[oy + y * SCALE + k][ox:ox + w * SCALE] = line

    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)

    raw = b"".join(b"\x00" + bytes(v for c in row for v in c) for row in image)
    with open(out, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def main():
    shots = tour()
    lines = []
    for n in range(0, len(shots), PER_SHEET):
        group = shots[n:n + PER_SHEET]
        sheet = os.path.join(OUT, f"sheet-{n // PER_SHEET + 1:02d}.png")
        write_sheet([p for p, _ in group], sheet)
        lines.append(os.path.relpath(sheet))
        for i, (path, scene) in enumerate(group):
            lines.append(f"  row {i // COLUMNS + 1}, column {i % COLUMNS + 1}: {scene}  ({os.path.basename(path)})")
    with open(os.path.join(OUT, "INDEX.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"{len(shots)} different screens on {len(range(0, len(shots), PER_SHEET))} sheets in {os.path.relpath(OUT)}", file=sys.stderr)


if __name__ == "__main__":
    main()
