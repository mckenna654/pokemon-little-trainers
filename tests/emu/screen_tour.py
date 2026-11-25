"""Screen tour: play through the screens a child sees and save a picture of every different one.

Automated tests read the game's memory; they do not look at the screen. This tool is for looking.
It walks the opening of the game, the first rival battle, a wild battle and a catch, the menus and
a few special moments, pressing A like a child, and writes numbered contact sheets for a reviewer
(a person, or an agent using the `playtest` skill) to inspect one by one.

    python3 -m tests.emu.screen_tour            # -> builds/screenshots/tour/sheet-01.png ...

To compare two builds, tour each into its own folder: set LT_TOUR_OUT, and LT_TEST_ROM / LT_TEST_SYM
for the other build. Two tours of builds that differ only in pictures show the same moments, so
every tile that differs is a picture that changed.

Nothing here asserts anything. Add a scene whenever a new kind of screen is added to the game.
"""
import hashlib
import os
import struct
import sys
import tempfile
import zlib

from . import story
from .checkpoints import game_at
from .firered import FireRed, SHOTS
from .gba import read_png

OUT = os.environ.get("LT_TOUR_OUT") or os.path.join(SHOTS, "tour")     # (LT_TOUR_OUT: a second tour beside the first)
LEADER_BROCK = 414
ONIX = 95
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


def open_start_menu(g, entry=0):
    """Open the Start menu with the cursor on an entry (0 = the top one). The menu remembers
    where the cursor was left, so it is moved from wherever it is."""
    for _ in range(6):
        g.press("START", wait=40)
        if not g.free_to_move():
            break
        g.frames(30)                                # still fading in from a battle: try again
    else:
        raise RuntimeError("the Start menu did not open")
    cursor = g.r8(g.sym("sStartMenuCursorPos"))
    for _ in range(abs(entry - cursor)):
        g.press("DOWN" if entry > cursor else "UP", wait=12)


def close_menus(g):
    for _ in range(8):
        if g.free_to_move():
            return
        g.press("B", wait=60)
    raise RuntimeError("could not get back to the field")


def throw_balls(t, g, scene):
    """Press CATCH until a ball catches, with a picture every other press of A in between."""
    for _ in range(40):
        g.press_button(g.CATCH)
        t.press_through(g, scene, lambda: g.at_action_menu() or (not g.in_battle() and g.callback2() == "CB2_Overworld"), every=2)
        if not g.in_battle():
            return
    t.shot(g, scene + " (gave up here)")


def wait_for_a_miss(g):
    """Leave the game at a moment from which the next ball thrown will miss, so the tour always
    shows what a miss looks like. Luck depends on the moment the button is pressed: each try
    starts from the same saved moment a few frames later and presses exactly as throw_balls does."""
    state = os.path.join(tempfile.mkdtemp(prefix="lt-tour-"), "before-the-throw.ss")
    g.save_state(state)
    try:
        for delay in range(2, 122, 3):
            g.load_state(state)
            g.frames(delay)
            g.press_button(g.CATCH)
            for _ in range(400):
                if g.at_action_menu() or not g.in_battle():
                    break
                g.press("A", hold=3, wait=17)
            if g.in_battle():                           # it broke free and the buttons are back
                g.load_state(state)
                g.frames(delay)
                return
        raise RuntimeError("forty balls and the hard-to-catch Pokemon never broke free")
    finally:
        os.remove(state)
        os.rmdir(os.path.dirname(state))


def tour():
    t = Tour()

    # 1. Power-on to the bedroom, A only
    g = FireRed()
    for frame in (200, 400, 800, 1200):
        g.frames(frame - g.frame)
        t.shot(g, "power-on and the opening film")
    while g.callback2() != "CB2_TitleScreenRun":
        g.frames(10)
    g.frames(240)                                # the title fades in
    for _ in range(4):                           # PRESS START blinks and the flames move: four looks
        g.frames(77)
        t.shot(g, "title screen")
    while g.callback2() == "CB2_TitleScreenRun":      # leave the title, so the next scene is not a picture of it
        g.press("A", hold=3, wait=17)
    t.press_through(g, "new game: from the title screen through the Professor's talk",
                    lambda: g.callback2() == "CB2_Overworld", every=4)
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
    t.press_through(g, "first rival battle", lambda: not g.in_battle(), max_presses=500, every=2)
    t.press_through(g, "after the first rival battle (the rival leaves, the game saves itself)", g.free_to_move, max_presses=200, every=2)
    g.close()

    # 3. A wild battle: every button, then a catch
    g = game_at("route1")
    t.shot(g, "Route 1")
    g.follow_arrow(lambda: g.free_to_move() and "-" in (g.nav_arrow_shown() or ""), max_actions=300, what="a diagonal arrow")
    g.frames(10)
    t.shot(g, "Route 1: the arrow pointing diagonally (either of its two directions is a good step)")
    story.find_wild_battle(g)
    g.wait_action_menu()
    g.frames(20)
    t.shot(g, "wild battle menu as it opens (the ring starts on the suggested attack)")
    for _ in range(4):
        g.press("LEFT", wait=8)
    for _ in range(4):
        g.frames(20)
        t.shot(g, "wild battle menu, each button from the left")
        g.press("RIGHT", wait=8)
    throw_balls(t, g, "catching a common Pokemon")

    # A Pokemon that is hard to catch (set-up: an Onix is made to appear here on Route 1)
    g.settle()
    g.frames(60)
    g.start_wild_battle(ONIX, 5)
    g.wait_action_menu()
    wait_for_a_miss(g)
    throw_balls(t, g, "a hard-to-catch Pokemon (set-up: Onix): a ball it breaks out of, then throws until one catches")

    # 4. Field menus
    g.settle()
    g.frames(90)
    open_start_menu(g)
    entries = g.r8(g.sym("sNumStartMenuItems"))
    for _ in range(entries):
        t.shot(g, "Start menu, each entry")
        g.press("DOWN", wait=12)
    close_menus(g)
    open_start_menu(g, 0)
    g.press("A", wait=120)
    t.shot(g, "party screen from the Start menu")
    g.press("A", wait=40)
    t.shot(g, "party screen, a Pokemon chosen")
    close_menus(g)
    open_start_menu(g, 1)
    g.press("A", wait=120)
    t.shot(g, "bag")
    close_menus(g)
    open_start_menu(g, 2)
    g.press("A", wait=60)
    t.press_through(g, "saving", g.free_to_move, max_presses=60)
    open_start_menu(g, 3)
    g.press("A", wait=90)
    t.shot(g, "options")
    close_menus(g)
    g.run_script([0x6E, 20, 8], wait=False)       # a plain yes/no question (no question text: set-up)
    g.frames(30)
    t.shot(g, "yes/no box (shown by itself, without its question)")
    g.press("B", wait=40)

    # 5. A gym leader: the trainer battle menu, a beaten Pokemon, the party screen in battle.
    # (Set-up: the battle is started on Route 1, and HP is written to memory to force a beaten
    # Pokemon and then a win, so the hearts jump instead of draining.)
    g.settle()
    g.start_trainer_battle(LEADER_BROCK)
    g.wait_action_menu()
    for _ in range(4):
        g.press("LEFT", wait=8)
    for _ in range(3):
        g.frames(20)
        t.shot(g, "trainer battle menu, each button from the left")
        g.press("RIGHT", wait=8)
    for _ in range(4):
        g.press("LEFT", wait=8)
    lead = g.battle_mon(0)["species"]
    for _ in range(10):                           # (the leader's Pokemon does not attack every turn)
        g.set_battle_hp(0, 1)                     # the lead is beaten by the next hit
        g.set_battle_hp(1, 300)
        g.attack()
        t.press_through(g, "the turns up to a beaten Pokemon, then the party screen",
                        lambda: g.at_action_menu() or not g.in_battle(), max_presses=200, every=2)
        if not g.in_battle() or g.battle_mon(0)["species"] != lead:
            break
    else:
        t.shot(g, "the turns up to a beaten Pokemon, then the party screen (gave up here: the lead was never beaten)")
    for press in range(900):
        if not g.in_battle() and g.free_to_move():
            break
        if g.at_action_menu():
            g.set_battle_hp(0, g.battle_mon(0)["max_hp"])
            g.set_battle_hp(1, 1)
        if press % 6 == 0:
            t.shot(g, "winning against a leader")
        g.press("A", hold=3, wait=17)
    else:
        t.shot(g, "winning against a leader (gave up here)")

    # 6. Badge confetti (set-up: the badge is handed over by a test script, here on Route 1)
    g.settle()
    g.run_script([0x29, *struct.pack("<H", FLAG_BADGE02_GET)])
    for _ in range(3):
        g.frames(40)
        t.shot(g, "badge confetti (forced, away from the gym)")
    g.close()
    return t.shots


# --- contact sheets (no image library needed) ---------------------------------------------------
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
