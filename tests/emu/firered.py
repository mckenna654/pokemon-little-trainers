"""FireRed-specific helpers on top of the generic GBA driver: reading game state from RAM and
scripted play (new game, walking, battles). Used by the emulator tests (tests/emu/emu_*.py).

Everything here observes the real game through documented RAM structures (struct Pokemon,
SaveBlock1, gMain); nothing is patched into the ROM for testing.
"""
import os
import struct

from .gba import GBA, ROOT, EmulatorError
from .maps import MapInfo

# (LT_TEST_ROM / LT_TEST_SYM: play a copy of the build, so the project can be rebuilt during a long run)
ROM = os.environ.get("LT_TEST_ROM") or os.path.join(ROOT, "builds", "Pokemon - Little Trainers.gba")
SYM = os.environ.get("LT_TEST_SYM") or os.path.join(ROOT, "builds", "Pokemon - Little Trainers.sym")
BASELINE_ROM = os.path.join(ROOT, "builds", "baseline-firered-rev1.gba")
BASELINE_SYM = os.path.join(ROOT, "builds", "baseline-firered-rev1.sym")
if os.environ.get("LT_TEST_BASELINE") == "1":
    # Run the same tests against unmodified FireRed, to prove they fail without our changes.
    ROM, SYM = BASELINE_ROM, BASELINE_SYM
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


B_OUTCOME_CAUGHT = 7

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

    @staticmethod
    def patch(raw, moves=None, exp=None, level=None, hp=None, species=None):
        """Return a copy of a 100-byte struct Pokemon with some fields changed and the
        checksum and encryption redone, exactly as the game stores it."""
        raw = bytearray(raw)
        personality, ot_id = struct.unpack_from("<II", raw, 0)
        key = personality ^ ot_id
        data = bytearray(struct.pack("<12I", *[w ^ key for w in struct.unpack_from("<12I", raw, 32)]))
        order = SUBSTRUCT_ORDER[personality % 24]
        growth, attacks = order.index("G") * 12, order.index("A") * 12
        if exp is not None:
            struct.pack_into("<I", data, growth + 4, exp)
        if species is not None:
            struct.pack_into("<H", data, growth, species)
        if moves is not None:
            struct.pack_into("<4H", data, attacks, *moves)
        struct.pack_into("<H", raw, 28, sum(struct.unpack_from("<24H", data, 0)) & 0xFFFF)
        struct.pack_into("<12I", raw, 32, *[w ^ key for w in struct.unpack_from("<12I", data, 0)])
        if level is not None:
            raw[84] = level
        if hp is not None:
            struct.pack_into("<H", raw, 86, hp)
        return bytes(raw)

    def __repr__(self):
        return f"<Mon species={self.species} lv={self.level} hp={self.hp}/{self.max_hp} status={self.status} moves={self.moves} pp={self.pp}>"


class FireRed(GBA):
    def __init__(self, rom=ROM, sym=SYM, save=None):
        super().__init__(rom, sym, save)
        self._cb_names = {addr & ~1: name for name, addrs in self.symbols.items() for addr in addrs
                          if name.startswith(("CB2_", "BattleMainCB2", "MainCB2"))}
        self._choose_action = self.sym("HandleInputChooseAction", near="SetControllerToPlayer") & ~1
        self._choose_move = self.sym("HandleInputChooseMove") & ~1

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

    def edit_party_mon(self, index, **changes):
        """Test set-up only: rewrite a party Pokemon in RAM (moves, exp, level, hp)."""
        addr = self.sym("gPlayerParty") + 100 * index
        patched = Mon.patch(self.read(addr, 100), **changes)
        for i in range(0, 100, 4):
            self.w32(addr + i, struct.unpack_from("<I", patched, i)[0])

    # --- test set-up through the game's own script engine -------------------------------------
    # Late-game situations (a gym leader, a cuttable tree, a badge) would take hours of button
    # presses to reach. Instead a few bytes of ordinary event script are placed in RAM and the
    # game's script engine is pointed at them, exactly as if an NPC had started that script.
    # Nothing is added to the ROM, and the behaviour being tested still comes from the game.
    def settle(self):
        """Let anything the game starts by itself (an autosave after a story goal) finish."""
        self.frames(20)
        if not self.free_to_move():
            self.advance_text(self.free_to_move, max_presses=80, what="the game to settle")
            self.frames(20)

    def run_script(self, bytecode, wait=True, max_frames=1800):
        self.settle()
        if not self.free_to_move():
            raise EmulatorError("run_script needs the player standing free in the overworld")
        buf = self.sym("gStringVar4") + 0x200                 # scratch space in a text buffer
        data = bytes(bytecode) + bytes([0x6B, 0x02])          # releaseall, end
        for i, b in enumerate(data):
            self.w8(buf + i, b)
        ctx = self.sym("sGlobalScriptContext")
        self.w8(ctx + 0, 0)                                   # stackDepth
        self.w8(ctx + 1, 1)                                   # mode: bytecode
        self.w32(ctx + 4, 0)                                  # nativePtr
        self.w32(ctx + 8, buf)                                # scriptPtr
        self.w32(ctx + 92, self.sym("gScriptCmdTable"))
        self.w32(ctx + 96, self.sym("gScriptCmdTableEnd"))
        self.w8(self.sym("sLockFieldControls"), 1)
        self.w8(self.sym("sGlobalScriptContextStatus"), 0)    # running
        self.frames(4)
        if wait:
            self.run_until(self.free_to_move, max_frames=max_frames, what="script to finish")
            self.settle()

    @staticmethod
    def _u16(v):
        return [v & 0xFF, (v >> 8) & 0xFF]

    def set_flag(self, flag_id):
        self.run_script([0x29] + self._u16(flag_id))

    def set_var(self, var_id, value):
        self.run_script([0x16] + self._u16(var_id) + self._u16(value))

    def give_item(self, item_id, quantity=1):
        self.run_script([0x44] + self._u16(item_id) + self._u16(quantity))

    def give_badges(self, count):
        script = []
        for i in range(count):
            script += [0x29] + self._u16(0x820 + i)           # FLAG_BADGE01_GET + i
        self.run_script(script)

    def teleport(self, location, x, y):
        """Warp to a map tile, like walking through a door that leads there."""
        group, num = location
        self.run_script([0x39, group, num, 0xFF] + self._u16(x) + self._u16(y) + [0x27], max_frames=2400)
        if self.location() != tuple(location):
            raise EmulatorError(f"teleport to {location} ended on {self.location()}")

    def start_trainer_battle(self, trainer_id):
        """Start a battle against a trainer by ID (no walking into their line of sight)."""
        buf = self.sym("gStringVar4") + 0x2F0
        self.w8(buf, 0xFF)                                    # empty defeat text
        ptr = [buf & 0xFF, (buf >> 8) & 0xFF, (buf >> 16) & 0xFF, (buf >> 24) & 0xFF]
        self.run_script([0x5C, 0x03] + self._u16(trainer_id) + [0, 0] + ptr, wait=False)
        self.run_until(self.in_battle, max_frames=900, what="trainer battle to start")

    def start_wild_battle(self, species, level):
        """Meet a chosen wild Pokemon where the player stands (test set-up: setwildbattle, dowildbattle)."""
        self.run_script([0xB6] + self._u16(species) + [level, 0, 0, 0xB7], wait=False)
        self.run_until(self.in_battle, max_frames=900, what="wild battle to start")

    # --- navigation arrow -------------------------------------------------------------------
    NAV_DIRS = {1: "DOWN", 2: "UP", 3: "LEFT", 4: "RIGHT"}

    def nav_goal(self):
        """Index of the story goal the arrow is currently built for (255 = none)."""
        return self.r8(self.sym("sBuiltGoal"))

    def nav_value(self):
        """Raw path-field value under the player: 1-4 a direction, 5 at the goal, 0 no path."""
        field = self.r32(self.sym("sField"))
        if field == 0:
            return 0
        width = self.r32(self.sym("VMap"))
        x, y = self.position()
        return self.r8(field + (y + 7) * width + (x + 7))

    def _arrow_anim(self):
        """Which picture the arrow sprite is showing (0-3 straight, 4-7 diagonal), or None if hidden."""
        sprite_id = self.r8(self.sym("sArrowSpriteId"))
        if sprite_id >= 64:
            return None
        sprite = self.sym("gSprites") + 0x44 * sprite_id
        flags = self.r8(sprite + 0x3E)
        if not flags & 1 or flags & 4:                      # not in use, or invisible
            return None
        return self.r8(sprite + 0x2A)

    def nav_arrow_shown(self):
        """The arrow exactly as the player sees it: "UP", "DOWN", "LEFT", "RIGHT", one of the four
        diagonals ("UP-RIGHT" and so on), or None if it is hidden. Read from the sprite itself."""
        anim = self._arrow_anim()
        if anim is None:
            return None
        return ("DOWN", "UP", "LEFT", "RIGHT", "UP-RIGHT", "UP-LEFT", "DOWN-RIGHT", "DOWN-LEFT")[anim & 7]

    def nav_arrow(self):
        """The next step of the path the arrow is showing, or None if the arrow is hidden. For a
        straight arrow this is where it points; a diagonal arrow points between this direction
        and nav_arrow_second()."""
        shown = self.nav_arrow_shown()
        if shown is None:
            return None
        if "-" not in shown:
            return shown
        return self.NAV_DIRS.get(self.r8(self.sym("sShownDir")))

    def nav_arrow_second(self):
        """The other direction of a diagonal arrow (just as good as nav_arrow()), else None."""
        shown = self.nav_arrow_shown()
        if shown is None or "-" not in shown:
            return None
        return self.NAV_DIRS.get(self.r8(self.sym("sShownDir2")))

    def follow_arrow(self, until, max_actions=4000, on_battle=None, what="goal"):
        """Play using only what a child would see: walk where the arrow points, and press A when
        it is hidden, when something is in the way, and in battles (the battle cursor starts on
        the recommended attack and stays where it is left)."""
        stuck = 0
        for _ in range(max_actions):
            if until():
                return
            if self.in_battle():
                if on_battle:
                    on_battle()
                else:
                    # Mash A like a child would: it advances text and presses whichever battle
                    # button the cursor is on (also in the Safari Zone, where A throws a ball).
                    for _ in range(4000):
                        if not self.in_battle():
                            break
                        if self.callback2() == "CB2_NamingScreen":
                            self.press("START", wait=20)
                            self.press("A", wait=40)
                        else:
                            self.press("A", hold=3, wait=13)
                continue
            if not self.free_to_move():
                if self.callback2() == "CB2_NamingScreen":
                    self.press("START", wait=20)
                    self.press("A", wait=40)
                else:
                    self.press("A", hold=3, wait=17)
                continue
            self.frames(3)                                  # let the arrow settle after a step
            arrow = self.nav_arrow()
            if arrow and self.step(arrow):
                stuck = 0
            else:
                self.press("A", hold=3, wait=17)            # no arrow, or a person/sign/door in the way
                stuck += 1
            if stuck > 80:
                raise EmulatorError(f"following the arrow got stuck at {self.position()} on map {self.location()} "
                                    f"(goal {self.nav_goal()}, arrow {self.nav_arrow()}, field {self.nav_value()})")
        raise EmulatorError(f"did not reach {what} by following the arrow; at {self.position()} on map {self.location()}")

    def is_surfing(self):
        return bool(self.r8(self.sym("gPlayerAvatar")) & 0x08)        # PLAYER_AVATAR_FLAG_SURFING

    def face(self, direction):
        """Turn on the spot (a short tap turns without stepping)."""
        self.hold(direction)
        self.frames(4)
        self.hold()
        self.frames(16)

    def enemy_party(self):
        mons = [Mon(self.read(self.sym("gEnemyParty") + 100 * i, 100)) for i in range(6)]
        return [m for m in mons if m.species != 0]

    def ball_count(self):
        """Quantity in the first slot of the Poke Balls pocket (0 if empty)."""
        sb1 = self.r32(self.sym("gSaveBlock1Ptr"))
        sb2 = self.r32(self.sym("gSaveBlock2Ptr"))
        item = self.r16(sb1 + 0x430)
        return (self.r16(sb1 + 0x432) ^ (self.r32(sb2 + 0xF20) & 0xFFFF)) if item else 0

    # --- battle ---------------------------------------------------------------------------
    def battle_mon(self, battler=0):
        """Live in-battle values for a battler (0 = player's, 1 = opponent's)."""
        raw = self.read(self.sym("gBattleMons") + 0x58 * battler, 0x58)
        return {"species": struct.unpack_from("<H", raw, 0)[0], "moves": list(struct.unpack_from("<4H", raw, 0x0C)),
                "pp": list(raw[0x24:0x28]), "hp": struct.unpack_from("<H", raw, 0x28)[0],
                "level": raw[0x2A], "max_hp": struct.unpack_from("<H", raw, 0x2C)[0]}

    def _controller(self):
        return self.r32(self.sym("gBattlerControllerFuncs")) & ~1

    def at_action_menu(self):
        return self.in_battle() and self._controller() == self._choose_action

    def at_move_menu(self):
        return self.in_battle() and self._controller() == self._choose_move

    def wait_action_menu(self, max_presses=400):
        """Tap B through battle text until FIGHT/BAG/POKeMON/RUN is waiting for input.
        Returns False if the battle ended first."""
        for _ in range(max_presses):
            if not self.in_battle():
                return False
            if self.at_action_menu():
                self.frames(4)
                return True
            callback = self.callback2()
            if callback == "CB2_NamingScreen":
                self.press("START", wait=20)
                self.press("A", wait=40)
            else:
                self.press("B", hold=3, wait=13)
        raise EmulatorError(f"battle menu never appeared (callback {self.callback2()})")

    def _move_cursor(self, addr, target):
        for _ in range(4):
            cur = self.r8(addr)
            if cur == target:
                return
            if (cur ^ target) & 1:
                self.press("RIGHT" if target & 1 else "LEFT", wait=8)
            elif (cur ^ target) & 2:
                self.press("DOWN" if target & 2 else "UP", wait=8)
        raise EmulatorError("menu cursor did not move")

    def choose_action(self, index):
        """0 FIGHT, 1 BAG, 2 POKeMON, 3 RUN."""
        self._move_cursor(self.sym("gActionSelectionCursor"), index)
        self.press("A", wait=20)

    # Little Trainer picture menu: buttons left to right, one press per action
    ATTACK, SPECIAL, CATCH, CHANGE, RUN = 0, 1, 2, 2, 3

    def menu_cursor(self):
        return self.r8(self.sym("gActionSelectionCursor"))

    def press_button(self, index):
        """Move the ring to a button with LEFT/RIGHT and press A."""
        for _ in range(4):
            cur = self.menu_cursor()
            if cur == index:
                break
            self.press("RIGHT" if cur < index else "LEFT", wait=8)
        if self.menu_cursor() != index:
            raise EmulatorError(f"could not move the menu cursor to button {index}")
        self.press("A", wait=20)

    def attack(self):
        self.press_button(self.ATTACK)

    def special(self):
        self.press_button(self.SPECIAL)

    def throw_ball(self):
        """One press of CATCH. True if the ball caught the Pokemon; False if it broke free and the
        battle menu is back. (On Little Trainer about seven throws in ten catch.)"""
        self.press_button(self.CATCH)
        return self._ball_thrown()

    def _ball_thrown(self):
        self.run_until(lambda: self.battle_outcome() == B_OUTCOME_CAUGHT or self.at_action_menu() or not self.in_battle(),
                       mash="B", step=10, max_frames=3600, what="the ball to catch, or the Pokemon to break free")
        if self.battle_outcome() == B_OUTCOME_CAUGHT:
            return True
        self.frames(4)
        return False

    def catch(self, max_throws=40):
        """Throw balls until one catches. Returns how many it took."""
        for throws in range(1, max_throws + 1):
            if self.throw_ball():
                return throws
            if not self.in_battle():
                raise EmulatorError("the battle ended without a catch")
        raise EmulatorError(f"{max_throws} balls and nothing caught")

    def run_away(self):
        self.press_button(self.RUN)

    def set_battle_hp(self, battler, hp):
        """Test set-up only: overwrite a battler's current HP in RAM."""
        self.w16(self.sym("gBattleMons") + 0x58 * battler + 0x28, hp)

    def last_move(self, battler=0):
        return self.r16(self.sym("gLastMoves") + 2 * battler)

    def chosen_move(self, battler=0):
        """The move a battler picked this turn (set even if the move then fails)."""
        return self.r16(self.sym("gChosenMoveByBattler") + 2 * battler)

    def use_move(self, slot=0):
        self.choose_action(0)
        self.run_until(self.at_move_menu, max_frames=300, what="move menu")
        self._move_cursor(self.sym("gMoveSelectionCursor"), slot)
        self.press("A", wait=20)

    def throw_ball_from_bag(self):
        """The original menus (Junior, Classic): BAG -> Poke Balls pocket -> first ball -> USE.
        True if the ball caught the Pokemon; False if it broke free and the menu is back."""
        self.choose_action(1)
        self.run_until(lambda: self.callback2() == "CB2_BagMenuRun", max_frames=600, what="bag to open")
        self.frames(60)
        pocket = self.sym("gBagMenuState") + 6
        for _ in range(4):
            if self.r16(pocket) == 2:
                break
            self.press("RIGHT", wait=45)
        if self.r16(pocket) != 2:
            raise EmulatorError("could not reach the Poke Balls pocket")
        self.press("A", wait=30)     # pick the first item
        self.press("A", wait=30)     # USE
        self.run_until(lambda: self.callback2() != "CB2_BagMenuRun", max_frames=600, what="bag to close")
        self.frames(30)
        return self._ball_thrown()

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
