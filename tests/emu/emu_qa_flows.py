"""QA (2026-11-26): flows off the arrow's route, on Little Trainer unless a test says otherwise.

Written during the QA play-through (`docs/QA-2026-11-26.md`, IDs QA-nn). Each test drives the
game with ordinary button presses from the "route1" checkpoint. Where a situation would take hours
to reach (a full PC, a trapped Pokemon) it is set up directly, and the test says so.

Tests marked `@known_bug` describe how the game *should* behave by the project's own rules
(docs/ACCESSIBILITY.md) but does not yet: they are open bugs. They count as expected failures only
when the bug check itself fails. When the bug is fixed, unittest reports an "unexpected success":
remove the decorator then. (A set-up that breaks before the bug check is also reported as an
unexpected success, with the real error printed, so it can never pass for the bug.)
"""
import functools
import struct
import sys
import unittest

from . import story
from .checkpoints import game_at

ITEM_POTION, ITEM_POKE_BALL = 13, 4
PIDGEY, DIGLETT, RATTATA, CHANSEY = 16, 50, 19, 113
ITEM_RARE_CANDY = 68
ITEM_SILPH_SCOPE = 359
ITEMMENUACTION_TOSS = 1
BP_ACTION_TOSS = 1                          # berry_pouch.c enum: USE, TOSS, GIVE, EXIT
ITEM_ORAN_BERRY = 139
ABILITY_SHADOW_TAG = 23
MAROWAK = 105
ITEM_TM01 = 289
TWINS_ELI_ANNE = 484                        # a double battle (include/constants/opponents.h)
SPECIAL_START_MAROWAK_BATTLE = 0x156          # StartMarowakBattle in data/specials.inc
ABILITY_ARENA_TRAP = 71
SPECIAL_SHOW_STORAGE_PC = 0x3C              # ShowPokemonStorageSystemPC in data/specials.inc
VAR_LT_DIFFICULTY = 0x4029
LITTLE, JUNIOR, CLASSIC = 0, 1, 2
BUG_CATCHER_RICK = 102                      # an ordinary Route trainer
STATUS2 = 0x50                              # struct BattlePokemon: status2
STATUS2_ESCAPE_PREVENTION = 1 << 26         # Mean Look, Block, Spider Web
OUTCOME_WON, OUTCOME_LOST, OUTCOME_RAN, OUTCOME_CAUGHT = 1, 2, 4, 7
BOXES, PER_BOX, BOX_MON = 14, 30, 80


class KnownBug(AssertionError):
    """Raised only by the check that shows an open bug."""


def known_bug(ref):
    """Mark a test that shows an open bug (see the module docstring)."""
    def decorate(test):
        @functools.wraps(test)
        def run(self):
            try:
                test(self)
            except KnownBug:
                raise
            except Exception as error:      # the set-up broke: make the run fail, and say why
                print(f"\n    {ref}: the set-up failed before the bug check: {error!r}", file=sys.stderr)
        return unittest.expectedFailure(run)
    return decorate


def buttons_reachable(g):
    """The battle buttons the ring can reach, moving with LEFT and RIGHT as a child would."""
    seen = {g.menu_cursor()}
    for key in ("LEFT",) * 4 + ("RIGHT",) * 4:
        g.press(key, wait=8)
        seen.add(g.menu_cursor())
    for _ in range(4):
        g.press("LEFT", wait=8)
    return seen


def bug_check(condition, message):
    if not condition:
        raise KnownBug(message)


# --- reading the save data ------------------------------------------------------------------------
def bag_count(g, item, pocket=0x310, slots=42):
    """How many of an item the bag holds (quantities are stored XOR the save's encryption key)."""
    sb1, sb2 = g.r32(g.sym("gSaveBlock1Ptr")), g.r32(g.sym("gSaveBlock2Ptr"))
    key = g.r32(sb2 + 0xF20) & 0xFFFF
    raw = g.read(sb1 + pocket, 4 * slots)
    return sum(q ^ key for i, q in struct.iter_unpack("<HH", raw) if i == item)


def storage_count(g):
    """How many Pokemon are in the PC boxes (BoxPokemon flags byte 19, bit 1: has a species)."""
    base = g.r32(g.sym("gPokemonStoragePtr")) + 4
    raw = g.read(base, BOXES * PER_BOX * BOX_MON)
    return sum(1 for i in range(BOXES * PER_BOX) if raw[i * BOX_MON + 19] & 2)


def give_mon(g, species, level=5):
    g.run_script([0x79, species & 0xFF, species >> 8, level] + [0] * 11)      # givemon


def open_pc(g):
    g.run_script([0x25, SPECIAL_SHOW_STORAGE_PC, 0x00, 0x27], wait=False)   # special; waitstate
    g.frames(120)


START_BAG, START_SAVE, START_OPTION = 2, 4, 5                       # entry ids in sStartMenuOrder (emu_menus.py)


def open_start_entry(g, entry_id):
    """Open the Start menu and move the cursor to an entry, wherever it is in the list (the list
    grows once the Pokedex is given)."""
    g.press("START", wait=40)
    order = list(g.read(g.sym("sStartMenuOrder"), g.r8(g.sym("sNumStartMenuItems"))))
    target, cursor = order.index(entry_id), g.r8(g.sym("sStartMenuCursorPos"))
    for _ in range(abs(target - cursor)):
        g.press("DOWN" if target > cursor else "UP", wait=12)


def save_game(g):
    """Start menu -> SAVE -> YES, with ordinary presses."""
    open_start_entry(g, START_SAVE)
    g.press("A", wait=60)
    g.advance_text(g.free_to_move, max_presses=200, what="control after saving")


def power_cycle_and_continue(g):
    g.reset()                                            # the cartridge save is kept
    g.advance_text(g.free_to_move, max_presses=400, what="control after CONTINUE")


class QaTestCase(unittest.TestCase):
    def setUp(self):
        self.g = game_at("route1")

    def tearDown(self):
        self.g.close()


class PermanentLoss(QaTestCase):
    """docs/ACCESSIBILITY.md rule 3: nothing is lost for good on Little Trainer."""

    def test_an_item_cannot_be_thrown_away(self):
        """QA-01 (#3, fixed): the bag's item menu has no TOSS on Little Trainer."""
        g = self.g
        actions = self.open_item_menu(ITEM_POTION)
        g.shot("qa-toss")
        self.assertNotIn(ITEMMENUACTION_TOSS, actions, f"no TOSS in the item menu ({actions})")
        self.assertEqual(len(actions), 3, "USE, GIVE, CANCEL")
        for key in ("DOWN", "DOWN", "A", "A", "A", "A"):  # the presses that used to throw it away
            g.press(key, wait=40)
        self.assertEqual(bag_count(g, ITEM_POTION), 1, "the Potion is still in the bag")

    def open_item_menu(self, item):
        """Start -> BAG -> the item's menu (the first item in the Items pocket)."""
        g = self.g
        g.give_item(item, 1)                             # set-up
        open_start_entry(g, START_BAG)
        g.press("A", wait=20)
        g.run_until(lambda: g.callback2() == "CB2_BagMenuRun", max_frames=600, what="the bag")
        g.frames(60)
        g.press("A", wait=40)
        count = g.r8(g.sym("sContextMenuNumItems"))
        return list(g.read(g.r32(g.sym("sContextMenuItemsPtr")), count))

    def test_classic_keeps_the_original_toss(self):
        """The rule is per preset: Classic is the original game."""
        g = self.g
        g.set_var(VAR_LT_DIFFICULTY, CLASSIC)                # set-up
        self.assertIn(ITEMMENUACTION_TOSS, self.open_item_menu(ITEM_POTION))

    def test_no_berry_can_be_thrown_away(self):
        """The Berry Pouch has its own menu, and picking up any berry gives the pouch."""
        g = self.g
        g.give_item(ITEM_ORAN_BERRY, 1)                  # set-up: a berry (the pouch comes with it)
        open_start_entry(g, START_BAG)
        g.press("A", wait=20)
        g.run_until(lambda: g.callback2() == "CB2_BagMenuRun", max_frames=600, what="the bag")
        g.frames(60)
        g.press("RIGHT", wait=45)                        # KEY ITEMS: the Berry Pouch
        g.press("A", wait=40)                            # its menu: OPEN first
        g.press("A", wait=30)
        g.run_until(lambda: "BerryPouch" in g.callback2(), max_frames=600, what="the Berry Pouch")
        g.frames(60)
        g.press("A", wait=40)                            # the Oran Berry's menu
        count = g.r8(g.sym("sContextMenuNumOptions"))
        options = list(g.read(g.r32(g.sym("sContextMenuOptions")), count))
        g.shot("qa-berry-pouch")
        self.assertEqual(count, 3, f"USE, GIVE, EXIT ({options})")
        self.assertNotIn(BP_ACTION_TOSS, options)

    def test_no_pokemon_can_be_released_whatever_is_pressed(self):
        """QA-02 (#4, fixed): the PC's menu for a Pokemon has no RELEASE on Little Trainer. Every
        entry of that menu is tried from the bottom up (STORE, at the top, moves the Pokemon into
        a box), each followed by UP and A (what answered YES before)."""
        g = self.g
        give_mon(g, PIDGEY)                              # set-up: two Pokemon
        self.assertEqual(g.party_count(), 2, "set-up: two Pokemon")
        open_pc(g)
        g.press("DOWN", wait=45)                         # DEPOSIT POKeMON
        g.press("A", wait=45)
        g.frames(60)                                     # (the box screen takes a moment to open)
        for entry in (4, 3, 2, 1, 0):
            g.press("A", wait=45)                        # the starter's menu
            for _ in range(entry):
                g.press("DOWN", wait=30)
            for key in ("A", "UP", "A", "A", "A", "A"):
                g.press(key, hold=3, wait=30)
            for _ in range(3):
                g.press("B", wait=40)
            if g.callback2() != "CB2_PokeStorage":       # left the PC: go back in for the next try
                for _ in range(6):
                    if g.free_to_move():
                        break
                    g.press("B", wait=40)
                open_pc(g)
                g.press("DOWN", wait=45)
                g.press("A", wait=45)
                g.frames(60)
        g.shot("qa-release")
        for _ in range(40):                              # leave the PC: a Pokemon being moved is in
            if g.free_to_move():                         # neither the party nor a box until it lands
                break
            g.press("B", wait=40)
        g.frames(60)
        self.assertTrue(g.free_to_move(), "set-up: back on the field")
        self.assertEqual(g.party_count() + storage_count(g), 2, "both Pokemon are still the player's")


class Evolution(QaTestCase):
    def test_no_evolution_starts_that_the_game_will_stop(self):
        """QA-04 (#6, fixed). Little Trainer lowers the friendship needed to evolve (150, not 220). Chansey and Golbat
        then try to evolve into Blissey and Crobat, which FireRed cancels until the National
        Pokedex, and Little Trainer never reaches the National Pokedex. (Unmodified FireRed does the
        same at friendship 220; the lower threshold makes it common.)"""
        g = self.g
        give_mon(g, CHANSEY, 20)                              # set-up
        g.edit_party_mon(1, friendship=160)                   # set-up: a well-loved Chansey
        g.give_item(ITEM_RARE_CANDY)                          # set-up
        open_start_entry(g, START_BAG)
        g.press("A", wait=20)
        g.run_until(lambda: g.callback2() == "CB2_BagMenuRun", max_frames=600, what="the bag")
        g.frames(60)
        seen = set()
        g.press("A", wait=30)                                 # RARE CANDY
        g.press("A", wait=60)                                 # USE
        g.press("DOWN", wait=20)                              # the Chansey
        for _ in range(200):
            seen.add(g.callback2())
            if g.free_to_move():
                break
            g.press("A", hold=3, wait=17)
        g.shot("qa-chansey-evolution")
        self.assertEqual(g.party()[1].level, 21, "set-up: the candy was used on the Chansey")
        self.assertFalse({c for c in seen if "Evolution" in c}, "no evolution scene that cannot finish")
        self.assertEqual(g.party()[1].species, CHANSEY)


class CatchingWhenFull(QaTestCase):
    def test_with_six_pokemon_the_catch_goes_to_the_pc(self):
        g = self.g
        for _ in range(5):
            give_mon(g, RATTATA)                         # set-up: a full party
        self.assertEqual(g.party_count(), 6)
        story.find_wild_battle(g)
        self.assertTrue(g.wait_action_menu())
        g.set_battle_hp(1, 1)                            # set-up: weak enough that any ball catches
        g.catch()
        g.advance_text(g.free_to_move, max_presses=600, what="control after catching")
        self.assertEqual(g.party_count(), 6)
        self.assertEqual(storage_count(g), 1, "the new Pokemon went to the PC")

    def test_with_the_pc_full_there_is_no_catch_button_and_the_battle_can_still_end(self):
        """QA-07 (fixed): with nowhere to put another Pokemon, CATCH is left out (it used to play
        only a failure sound), and the battle can still be finished."""
        g = self.g
        for _ in range(5):
            give_mon(g, RATTATA)                         # set-up: a full party
        one = g.read(g.sym("gPlayerParty"), BOX_MON)     # set-up: every box slot filled with a copy
        base = g.r32(g.sym("gPokemonStoragePtr")) + 4
        for slot in range(BOXES * PER_BOX):
            for i in range(0, BOX_MON, 4):
                g.w32(base + slot * BOX_MON + i, struct.unpack_from("<I", one, i)[0])
        self.assertEqual(storage_count(g), BOXES * PER_BOX)
        story.find_wild_battle(g)
        self.assertTrue(g.wait_action_menu())
        self.assertNotIn(g.CATCH, buttons_reachable(g), "no CATCH button")
        g.shot("qa-catch-when-full")
        g.run_away()
        g.advance_text(g.free_to_move, max_presses=200, what="control after running")
        self.assertEqual(g.battle_outcome(), OUTCOME_RAN)


class Trapped(QaTestCase):
    def test_run_from_a_pokemon_with_arena_trap(self):
        """QA-05 (fixed): Diglett's Arena Trap stops running away in the original game. Little
        Trainer's rule is that running from a wild Pokemon always works, and now it wins."""
        g = self.g
        g.start_wild_battle(DIGLETT, 5)                  # set-up: a wild Diglett on Route 1
        self.assertTrue(g.wait_action_menu())
        ability = g.r8(g.sym("gBattleMons") + 0x58 + 0x20)
        self.assertEqual(ability, ABILITY_ARENA_TRAP, "set-up: this Diglett has Arena Trap, not Sand Veil")
        g.run_away()
        for _ in range(200):
            if not g.in_battle() or g.at_action_menu():
                break
            g.press("A", hold=3, wait=13)
        g.shot("qa-run-arena-trap")
        self.assertFalse(g.in_battle(), "ran away from the Diglett")
        self.assertEqual(g.battle_outcome(), OUTCOME_RAN)

    def trapped_battle(self):
        """A trainer battle, a second Pokemon on the bench, the lead held by Mean Look (set-up),
        then one turn so that the buttons are drawn again."""
        g = self.g
        give_mon(g, PIDGEY)                              # set-up: someone to change to
        g.start_trainer_battle(BUG_CATCHER_RICK)         # set-up: a trainer battle started by script
        self.assertTrue(g.wait_action_menu(), "set-up: the battle buttons")
        self.assertIn(g.CHANGE, buttons_reachable(g), "set-up: CHANGE is there before the trap")
        flags = g.r32(g.sym("gBattleMons") + STATUS2)
        g.w32(g.sym("gBattleMons") + STATUS2, flags | STATUS2_ESCAPE_PREVENTION)   # set-up: Mean Look
        g.set_battle_hp(1, 300)                          # set-up: the opponent lasts the turn
        g.set_battle_hp(0, g.battle_mon(0)["max_hp"])
        g.attack()
        self.assertTrue(g.wait_action_menu(), "set-up: the next turn's buttons")

    def test_no_change_button_while_trapped(self):
        """QA-03 (#5, fixed): CHANGE used to open a party screen where pressing A went round
        SHIFT -> "can't be switched out!" for ever. Brock's Onix knows Bind."""
        g = self.g
        self.trapped_battle()
        self.assertNotIn(g.CHANGE, buttons_reachable(g), "no CHANGE while held in battle")
        g.shot("qa-change-when-trapped")

    def test_no_change_button_against_a_trapping_ability(self):
        """CanLeaveField's ability branch: an opponent with Shadow Tag (set-up)."""
        g = self.g
        give_mon(g, PIDGEY)                              # set-up: someone to change to
        g.start_trainer_battle(BUG_CATCHER_RICK)
        self.assertTrue(g.wait_action_menu())
        g.w8(g.sym("gBattleMons") + 0x58 + 0x20, ABILITY_SHADOW_TAG)   # set-up: battler 1's ability
        g.set_battle_hp(1, 300)
        g.set_battle_hp(0, g.battle_mon(0)["max_hp"])
        g.attack()
        self.assertTrue(g.wait_action_menu())
        self.assertNotIn(g.CHANGE, buttons_reachable(g))

    def test_change_comes_back_when_free_again(self):
        g = self.g
        self.trapped_battle()
        flags = g.r32(g.sym("gBattleMons") + STATUS2)
        g.w32(g.sym("gBattleMons") + STATUS2, flags & ~STATUS2_ESCAPE_PREVENTION)  # set-up: the trap ends
        g.set_battle_hp(1, 300)
        g.attack()
        self.assertTrue(g.wait_action_menu())
        self.assertIn(g.CHANGE, buttons_reachable(g))


class DoubleBattle(QaTestCase):
    def at_menu(self, battler):
        g = self.g
        return g.in_battle() and g.r32(g.sym("gBattlerControllerFuncs") + 4 * battler) & ~1 == g._choose_action

    def reachable(self, battler):
        """The buttons battler's ring can reach (its own cursor in gActionSelectionCursor)."""
        g = self.g
        cursor = lambda: g.r8(g.sym("gActionSelectionCursor") + battler)
        seen = {cursor()}
        for key in ("LEFT",) * 4 + ("RIGHT",) * 4:
            g.press(key, wait=8)
            seen.add(cursor())
        return seen

    def start_double_battle(self):
        g = self.g
        give_mon(g, PIDGEY)                              # set-up: two to fight, one on the bench
        give_mon(g, PIDGEY)
        buf = g.sym("gStringVar4") + 0x2F0
        g.w8(buf, 0xFF)                                  # set-up: empty texts for the script
        text = list(struct.pack("<I", buf))
        # set-up: trainerbattle TRAINER_BATTLE_DOUBLE, the Twins (a double battle), with texts
        g.run_script([0x5C, 0x04, *struct.pack("<H", TWINS_ELI_ANNE), 0, 0] + text * 3, wait=False)
        g.run_until(g.in_battle, mash="A", step=20, max_frames=1800, what="the double battle")
        g.run_until(lambda: self.at_menu(0), mash="B", step=13, max_frames=3000, what="the left Pokemon's buttons")
        g.frames(10)

    def test_the_second_pokemon_can_change_when_the_bench_is_free(self):
        """The control for the test below: the left Pokemon attacks, so the bench is free and the
        right-hand Pokemon is offered CHANGE as usual."""
        g = self.g
        self.start_double_battle()
        g.press_button(g.ATTACK)
        for _ in range(60):
            if self.at_menu(2):
                break
            g.press("A", hold=3, wait=20)
        self.assertTrue(self.at_menu(2), "set-up: the right Pokemon's turn to choose")
        g.frames(10)
        buttons = self.reachable(2)
        self.assertGreater(len(buttons), 1, "set-up: the ring moves")
        self.assertIn(g.CHANGE, buttons)

    def test_no_change_for_the_second_pokemon_when_the_bench_is_already_taken(self):
        """#8 (fixed): in a double battle, once the left-hand Pokemon has chosen to change to the
        only Pokemon on the bench, the right-hand one must not be offered CHANGE (its party
        screen would have nobody to send out)."""
        g = self.g
        self.start_double_battle()
        self.assertIn(g.CHANGE, self.reachable(0), "set-up: CHANGE for the left Pokemon")
        g.press_button(g.CHANGE)                         # CHANGE -> the party screen
        for _ in range(60):                              # A: the Pokemon on the bench, SHIFT
            if self.at_menu(2):
                break
            g.press("A", hold=3, wait=20)
        self.assertTrue(self.at_menu(2), "set-up: the right Pokemon's turn to choose")
        self.assertEqual(g.r8(g.sym("gChosenActionByBattler")), 2, "set-up: the left Pokemon chose to switch (B_ACTION_SWITCH)")
        g.frames(10)
        g.shot("qa-double-change")
        # Without CHANGE a trainer battle leaves ATTACK alone, so the ring cannot move here: the
        # control test above shows it does move for this Pokemon when CHANGE is there.
        self.assertNotIn(g.CHANGE, self.reachable(2), "no CHANGE: nobody is left to change to")


class YesNoPictures(QaTestCase):
    """QA-08 (fixed): the tick and cross on the PC's and the TM Case's Yes/No boxes. Their usual
    palettes turned the tick black, so the colours on screen are checked, not just the drawing."""

    def colours_beside_yes_no(self):
        """Clearly green and clearly red pixels in the lower right of the screen."""
        pixels = self.g.pixels()
        area = [pixels[y][x] for y in range(60, 130) for x in range(170, 240)]
        green = sum(1 for r, gr, b in area if gr > 150 and r < 120 and b < 120)
        red = sum(1 for r, gr, b in area if r > 180 and gr < 90 and b < 90)
        return green, red

    def test_the_pcs_question_has_a_green_tick_and_a_red_cross(self):
        g = self.g
        give_mon(g, PIDGEY)                              # set-up: someone to deposit
        open_pc(g)
        g.press("DOWN", wait=45)                         # DEPOSIT POKeMON
        g.press("A", wait=45)
        g.frames(60)
        g.press("B", wait=60)                            # "Continue BOX operations?"
        g.frames(20)
        g.shot("qa-yes-no-pc")
        green, red = self.colours_beside_yes_no()
        self.assertGreater(green, 10, "a green tick")
        self.assertGreater(red, 10, "a red cross")

    def test_the_tm_cases_question_has_a_green_tick_and_a_red_cross(self):
        g = self.g
        g.give_item(ITEM_TM01, 1)                        # set-up: a TM to sell
        g.run_script([0x86, *struct.pack("<I", g.sym("ViridianCity_Mart_Items"))], wait=False)   # set-up: a shop
        g.frames(60)
        g.press("DOWN", wait=45)                         # SELL: the bag opens
        g.press("A", wait=45)
        g.frames(90)
        g.press("RIGHT", wait=45)                        # KEY ITEMS: the TM Case
        g.press("A", wait=45)
        g.frames(90)
        g.press("A", wait=45)                            # the TM (only one: no quantity) -> "I can pay ... okay?"
        g.frames(20)
        g.shot("qa-yes-no-tm-case")
        green, red = self.colours_beside_yes_no()
        self.assertGreater(green, 10, "a green tick")
        self.assertGreater(red, 10, "a red cross")


class GhostBattle(QaTestCase):
    def test_no_catch_button_against_the_tower_ghost(self):
        """QA-06 (fixed): the Pokemon Tower Marowak dodges every ball, so CATCH is left out."""
        g = self.g
        g.give_item(ITEM_SILPH_SCOPE)                    # set-up: the ghost can be seen
        g.run_script([0x25, *struct.pack("<H", SPECIAL_START_MAROWAK_BATTLE), 0x27], wait=False)   # set-up: the Tower battle
        g.run_until(g.in_battle, max_frames=900, what="the Marowak battle")
        self.assertTrue(g.wait_action_menu(), "set-up: the battle buttons")
        self.assertEqual(g.battle_mon(1)["species"], MAROWAK, "set-up: the Marowak")
        self.assertNotIn(g.CATCH, buttons_reachable(g), "no CATCH against the ghost")
        self.assertIn(g.RUN, buttons_reachable(g))
        g.shot("qa-ghost-buttons")


class SavingAndModes(QaTestCase):
    def test_a_pokemon_caught_without_saving_is_lost_when_the_power_goes_off(self):
        """D-01: the autosave runs when a story goal is reached, not after a catch. Recorded as
        the game behaves now; the question for Jake is whether a catch should save."""
        g = self.g
        save_game(g)
        story.find_wild_battle(g)
        self.assertTrue(g.wait_action_menu())
        g.set_battle_hp(1, 1)                            # set-up: weak enough that any ball catches
        g.catch()
        g.advance_text(g.free_to_move, max_presses=600, what="control after catching")
        self.assertEqual(g.party_count(), 2)
        power_cycle_and_continue(g)
        self.assertEqual(g.party_count(), 1, "the catch was not saved")

    def test_the_mode_is_saved_with_the_game(self):
        g = self.g
        g.set_var(VAR_LT_DIFFICULTY, JUNIOR)        # set-up (changing it through OPTION is tested in emu_menus)
        save_game(g)
        power_cycle_and_continue(g)
        self.assertEqual(g.var(VAR_LT_DIFFICULTY), JUNIOR)
        g.set_var(VAR_LT_DIFFICULTY, LITTLE)        # set-up: changed and not saved
        power_cycle_and_continue(g)
        self.assertEqual(g.var(VAR_LT_DIFFICULTY), JUNIOR, "an unsaved change is not kept")

    def test_classic_adds_no_free_ball_at_a_wild_battle(self):
        """Switching to Classic turns off the free Poke Ball. Recorded as behaviour, not a bug."""
        g = self.g
        g.set_var(VAR_LT_DIFFICULTY, CLASSIC)                # set-up
        balls = bag_count(g, ITEM_POKE_BALL, pocket=0x430, slots=13)
        story.find_wild_battle(g)
        self.assertTrue(g.wait_action_menu())
        self.assertEqual(bag_count(g, ITEM_POKE_BALL, pocket=0x430, slots=13), balls, "no ball was added on Classic")
        g.choose_action(3)                               # the original menu's RUN
        g.advance_text(g.free_to_move, max_presses=200, what="control after running")


if __name__ == "__main__":
    unittest.main()
