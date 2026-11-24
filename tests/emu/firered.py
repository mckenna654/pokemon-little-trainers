"""FireRed-specific helpers on top of the generic GBA driver: reading game state from RAM and
scripted play (new game, walking, battles). Used by the emulator tests (tests/emu/emu_*.py).

Everything here observes the real game through documented RAM structures (struct Pokemon,
SaveBlock1, gMain); nothing is patched into the ROM for testing.
"""
import os
import struct

from .gba import GBA, ROOT, EmulatorError
from .maps import MapInfo

ROM = os.path.join(ROOT, "builds", "Pokemon - Little Trainers.gba")
SYM = os.path.join(ROOT, "builds", "Pokemon - Little Trainers.sym")
BASELINE_ROM = os.path.join(ROOT, "builds", "baseline-firered-rev1.gba")
BASELINE_SYM = os.path.join(ROOT, "builds", "baseline-firered-rev1.sym")
SHOTS = os.path.join(ROOT, "builds", "screenshots")

# (mapGroup, mapNum) from include/constants/map_groups.h
PALLET_TOWN = (3, 0)
VIRIDIAN_CITY = (3, 1)
ROUTE1 = (3, 19)
PLAYERS_HOUSE_1F = (4, 0)
PLAYERS_HOUSE_2F = (4, 1)
OAKS_LAB = (4, 3)

# Order of the four 12-byte substructs (Growth, Attacks, EVs, Misc) for personality % 24.
SUBSTRUCT_ORDER = ["GAEM", "GAME", "GEAM", "GEMA", "GMAE", "GMEA", "AGEM", "AGME", "AEGM", "AEMG", "AMGE", "AMEG",
                   "EGAM", "EGMA", "EAGM", "EAMG", "EMGA", "EMAG", "MGAE", "MGEA", "MAGE", "MAEG", "MEGA", "MEAG"]


class Mon:
    """A decoded struct Pokemon (100 bytes)."""

    def __init__(self, raw):
        self.personality, self.ot_id = struct.unpack_from("<II", raw, 0)
        key = self.personality ^ self.ot_id
        words = struct.unpack_from("<12I", raw, 32)
        data = struct.pack("<12I", *[w ^ key for w in words])
        order = SUBSTRUCT_ORDER[self.personality % 24]
        sub = {name: data[i * 12:(i + 1) * 12] for i, name in enumerate(order)}
        self.species, self.item, self.exp = struct.unpack_from("<HHI", sub["G"], 0)
        self.friendship = sub["G"][9]
        self.moves = list(struct.unpack_from("<4H", sub["A"], 0))
        self.pp = list(sub["A"][8:12])
        self.status, self.level = struct.unpack_from("<IB", raw, 80)
        self.hp, self.max_hp = struct.unpack_from("<HH", raw, 86)

    def __repr__(self):
        return f"<Mon species={self.species} lv={self.level} hp={self.hp}/{self.max_hp} status={self.status} moves={self.moves} pp={self.pp}>"


class FireRed(GBA):
    def __init__(self, rom=ROM, sym=SYM, save=None):
        super().__init__(rom, sym, save)
        self._cb_names = {addr & ~1: name for name, addr in self.symbols.items()
                          if name.startswith(("CB2_", "BattleMainCB2", "MainCB2"))}

    # --- state ----------------------------------------------------------------------------
    def callback2(self):
        addr = self.r32(self.sym("gMain") + 4) & ~1
        return self._cb_names.get(addr, hex(addr))

    def in_overworld(self):
        return self.callback2() == "CB2_Overworld"

    def in_battle(self):
        return bool(self.r8(self.sym("gMain") + 0x439) & 2)

    def location(self):
        sb1 = self.r32(self.sym("gSaveBlock1Ptr"))
        return (self.r8(sb1 + 4), self.r8(sb1 + 5))

    def position(self):
        sb1 = self.r32(self.sym("gSaveBlock1Ptr"))
        return (self.r16(sb1), self.r16(sb1 + 2))

    def party_count(self):
        return self.r8(self.sym("gPlayerPartyCount"))

    def party(self):
        base = self.sym("gPlayerParty")
        return [Mon(self.read(base + 100 * i, 100)) for i in range(self.party_count())]

    def enemy(self, index=0):
        return Mon(self.read(self.sym("gEnemyParty") + 100 * index, 100))

    def battle_outcome(self):
        return self.r8(self.sym("gBattleOutcome"))

    def money(self):
        sb1 = self.r32(self.sym("gSaveBlock1Ptr"))
        sb2 = self.r32(self.sym("gSaveBlock2Ptr"))
        key = self.r32(sb2 + 0xF20)
        return self.r32(sb1 + 0x290) ^ key

    def var(self, var_id):
        """Read a saved script variable (VAR_* constant, 0x4000+)."""
        sb1 = self.r32(self.sym("gSaveBlock1Ptr"))
        return self.r16(sb1 + 0x1000 + 2 * (var_id - 0x4000))

    def flag(self, flag_id):
        sb1 = self.r32(self.sym("gSaveBlock1Ptr"))
        return bool(self.r8(sb1 + 0xEE0 + flag_id // 8) & (1 << (flag_id % 8)))

    def free_to_move(self):
        """True when the player has control in the overworld (no script, menu or battle)."""
        return self.in_overworld() and self.r8(self.sym("sLockFieldControls")) == 0

    def npc_tiles(self):
        """Tiles currently occupied by other overworld objects (live, from gObjectEvents)."""
        base, tiles = self.sym("gObjectEvents"), set()
        for i in range(1, 16):
            raw = self.read(base + i * 0x24, 0x18)
            if raw[0] & 1:
                x, y = struct.unpack_from("<hh", raw, 0x10)
                tiles.add((x - 7, y - 7))
        return tiles

    def shot(self, name):
        self.screenshot(os.path.join(SHOTS, name + ".png"))

    # --- scripted play --------------------------------------------------------------------
    def start_new_game(self):
        """Power-on to standing in the player's bedroom, accepting default names."""
        def step():
            cb = self.callback2()
            if cb == "CB2_NamingScreen":
                self.press("START", wait=20)   # jump to OK; an empty name gets the default
                self.press("A", wait=40)
            else:
                self.press("A", hold=3, wait=17)
            return cb == "CB2_Overworld"
        for _ in range(1200):
            if step():
                break
        else:
            raise EmulatorError("new game did not reach the overworld")
        self.frames(120)
        if self.location() != PLAYERS_HOUSE_2F:
            raise EmulatorError(f"unexpected start location {self.location()}")

    def advance_text(self, until, max_presses=600, what="condition"):
        """Tap A through dialogue, cut-scenes and menus until `until()` is true.
        Naming screens are confirmed with the default name."""
        for _ in range(max_presses):
            if until():
                return
            if self.callback2() == "CB2_NamingScreen":
                self.press("START", wait=20)
                self.press("A", wait=40)
            else:
                self.press("A", hold=3, wait=17)
        raise EmulatorError(f"gave up waiting for {what} (callback {self.callback2()}, map {self.location()}, pos {self.position()})")

    def go_to(self, x, y, avoid=()):
        """Path-find to a tile on the current map using the game's collision data. Returns when
        the tile is reached, the map changes (door/edge), or a script takes control."""
        for _ in range(8):
            where = self.location()
            if self.position() == (x, y):
                return
            route = MapInfo(where).path(self.position(), (x, y), set(avoid) | self.npc_tiles(), static_objects=False)
            if route is None:
                raise EmulatorError(f"no route from {self.position()} to ({x},{y}) on map {where}")
            for direction in route:
                if not self.step(direction):
                    break
                if self.location() != where:
                    self.frames(40)
                    return
            if not self.free_to_move():
                return
        if self.position() != (x, y):
            raise EmulatorError(f"could not reach ({x},{y}); at {self.position()} on map {self.location()}")

    def take_warp(self, x, y):
        """Walk to a warp tile (door, stairs, exit mat) and go through it."""
        where = self.location()
        self.go_to(x, y)
        # Doors warp on entry; stairs and exit mats need a push in their direction.
        for direction in ("DOWN", "RIGHT", "LEFT", "UP"):
            if self.location() != where:
                break
            if self.position() != (x, y):
                self.go_to(x, y)       # an earlier push walked us off the tile
                if self.location() != where:
                    break
            self.hold(direction)
            self.frames(24)
            self.hold()
            self.frames(8)
        if self.location() == where:
            raise EmulatorError(f"warp at ({x},{y}) on map {where} did not trigger")
        self.run_until(self.free_to_move, max_frames=600, what="control after warp")
        self.frames(10)

    def step(self, direction, count=1):
        """Take `count` single-tile steps. Returns False as soon as a step is blocked."""
        for _ in range(count):
            before, where = self.position(), self.location()
            self.hold(direction)
            moved = False
            for _ in range(24):            # first frames may be a turn-on-the-spot
                self.frames(2)
                if self.position() != before or self.location() != where:
                    moved = True
                    break
            self.hold()
            self.frames(18)                # let the step animation finish
            if not moved:
                return False
        return True
