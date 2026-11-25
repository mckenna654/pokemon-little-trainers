"""QA (2026-11-26): flows off the arrow's route, on Little Trainer unless a test says otherwise.

Written during the QA play-through (`docs/QA-2026-11-26.md`, IDs QA-nn). Each test drives the
game with ordinary button presses from the "route1" checkpoint. Where a situation would take hours
to reach (a full PC, a trapped Pokemon) it is set up directly, and the test says so.

Tests marked `expectedFailure` describe how the game *should* behave by the project's own rules
(docs/ACCESSIBILITY.md) but does not yet: they are open bugs. When one is fixed, unittest reports
an "unexpected success": remove the decorator then.
"""
import struct
import unittest

from . import story
from .checkpoints import game_at

ITEM_POTION, ITEM_POKE_BALL = 13, 4
PIDGEY, DIGLETT, RATTATA, CHANSEY = 16, 50, 19, 113
ITEM_RARE_CANDY = 68
SPECIAL_SHOW_STORAGE_PC = 0x3C              # ShowPokemonStorageSystemPC in data/specials.inc
VAR_LT_DIFFICULTY = 0x4029
LITTLE, JUNIOR, CLASSIC = 0, 1, 2
BUG_CATCHER_RICK = 102                      # an ordinary Route trainer
STATUS2 = 0x50                              # struct BattlePokemon: status2
STATUS2_ESCAPE_PREVENTION = 1 << 26         # Mean Look, Block, Spider Web
OUTCOME_WON, OUTCOME_LOST, OUTCOME_RAN, OUTCOME_CAUGHT = 1, 2, 4, 7
BOXES, PER_BOX, BOX_MON = 14, 30, 80


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

    @unittest.expectedFailure       # QA-01: the bag's TOSS throws items away for good
    def test_an_item_cannot_be_thrown_away(self):
        g = self.g
        g.give_item(ITEM_POTION, 1)
        g.press("START", wait=40)
        cursor = g.r8(g.sym("sStartMenuCursorPos"))
        for _ in range(abs(1 - cursor)):
            g.press("DOWN" if cursor < 1 else "UP", wait=12)
        g.press("A", wait=20)
        g.run_until(lambda: g.callback2() == "CB2_BagMenuRun", max_frames=600, what="the bag")
        g.frames(60)
        for key in ("A", "DOWN", "DOWN", "A", "A", "A", "A"):   # POTION, TOSS, (1 of 1), YES (already chosen)
            g.press(key, wait=40)
        g.shot("qa-toss")
        self.assertEqual(bag_count(g, ITEM_POTION), 1, "the Potion is still in the bag")

    @unittest.expectedFailure       # QA-02: the PC's RELEASE lets the starter go for good
    def test_a_pokemon_cannot_be_released(self):
        g = self.g
        give_mon(g, PIDGEY)
        self.assertEqual(g.party_count(), 2)
        open_pc(g)
        g.press("DOWN", wait=45)                         # DEPOSIT POKeMON
        g.press("A", wait=45)
        g.frames(60)                                     # (the box screen takes a moment to open)
        # the starter, RELEASE, YES (the cursor starts on NO), then the messages
        for key in ("A", "DOWN", "DOWN", "DOWN", "A", "UP", "A", "A", "A", "A", "A", "B", "B"):
            g.press(key, wait=45)
        g.shot("qa-release")
        self.assertEqual(g.party_count() + storage_count(g), 2, "both Pokemon are still the player's")

    def test_mashing_a_in_the_pc_lets_nobody_go(self):
        """The release question starts on NO, so pressing A alone never releases anyone."""
        g = self.g
        give_mon(g, PIDGEY)
        open_pc(g)
        for _ in range(60):
            g.press("A", hold=3, wait=20)
        for _ in range(20):
            g.press("B", wait=30)
        self.assertEqual(g.party_count() + storage_count(g), 2)


class Evolution(QaTestCase):
    @unittest.expectedFailure       # QA-04: "CHANSEY is evolving!" then it stops, after every level-up
    def test_no_evolution_starts_that_the_game_will_stop(self):
        """Little Trainer lowers the friendship needed to evolve (150, not 220). Chansey and Golbat
        then try to evolve into Blissey and Crobat, which FireRed cancels until the National
        Pokedex, and Little Trainer never reaches the National Pokedex."""
        g = self.g
        give_mon(g, CHANSEY, 20)
        g.edit_party_mon(1, friendship=160)                   # set-up: a well-loved Chansey
        g.give_item(ITEM_RARE_CANDY)
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
        self.assertEqual(g.party()[1].species, CHANSEY)
        self.assertFalse({c for c in seen if "Evolution" in c}, "no evolution scene that cannot finish")


class CatchingWhenFull(QaTestCase):
    def test_with_six_pokemon_the_catch_goes_to_the_pc(self):
        g = self.g
        for _ in range(5):
            give_mon(g, RATTATA)
        self.assertEqual(g.party_count(), 6)
        story.find_wild_battle(g)
        self.assertTrue(g.wait_action_menu())
        g.set_battle_hp(1, 1)                            # set-up: weak enough that any ball catches
        g.catch()
        g.advance_text(g.free_to_move, max_presses=600, what="control after catching")
        self.assertEqual(g.party_count(), 6)
        self.assertEqual(storage_count(g), 1, "the new Pokemon went to the PC")

    def test_with_the_pc_full_catch_is_refused_and_the_battle_can_still_end(self):
        """QA-05: with nowhere to put another Pokemon, CATCH only plays a failure sound. Nothing
        on screen says why. This checks it is not a trap: the battle can still be finished."""
        g = self.g
        for _ in range(5):
            give_mon(g, RATTATA)
        one = g.read(g.sym("gPlayerParty"), BOX_MON)     # set-up: every box slot filled with a copy
        base = g.r32(g.sym("gPokemonStoragePtr")) + 4
        for slot in range(BOXES * PER_BOX):
            for i in range(0, BOX_MON, 4):
                g.w32(base + slot * BOX_MON + i, struct.unpack_from("<I", one, i)[0])
        self.assertEqual(storage_count(g), BOXES * PER_BOX)
        story.find_wild_battle(g)
        self.assertTrue(g.wait_action_menu())
        g.press_button(g.CATCH)
        g.frames(40)
        self.assertTrue(g.at_action_menu(), "the buttons are still there: the ball was not thrown")
        for _ in range(10):                               # a child pressing it again and again
            g.press("A", wait=20)
        self.assertTrue(g.in_battle() and g.at_action_menu())
        g.shot("qa-catch-when-full")
        g.run_away()
        g.advance_text(g.free_to_move, max_presses=200, what="control after running")
        self.assertEqual(g.battle_outcome(), OUTCOME_RAN)


class Trapped(QaTestCase):
    def test_run_from_a_pokemon_with_arena_trap(self):
        """Diglett's Arena Trap stops running away in the original game. Little Trainer promises
        that running always works; this records which wins and that nothing gets stuck."""
        g = self.g
        g.start_wild_battle(DIGLETT, 5)
        self.assertTrue(g.wait_action_menu())
        g.run_away()
        for _ in range(200):
            if not g.in_battle() or g.at_action_menu():
                break
            g.press("A", hold=3, wait=13)
        g.shot("qa-run-arena-trap")
        self.assertTrue(not g.in_battle() or g.at_action_menu(), "the game came back to the player")
        # QA-06: Arena Trap still wins on Little Trainer, although the README says running always
        # works. Recorded as the game behaves now.
        self.assertTrue(g.in_battle(), "Arena Trap stopped the run")

    def trapped_change(self):
        """A trainer battle, a second Pokemon on the bench, the lead held by Mean Look (set-up),
        then CHANGE."""
        g = self.g
        give_mon(g, PIDGEY)
        g.start_trainer_battle(BUG_CATCHER_RICK)
        self.assertTrue(g.wait_action_menu())
        flags = g.r32(g.sym("gBattleMons") + STATUS2)
        g.w32(g.sym("gBattleMons") + STATUS2, flags | STATUS2_ESCAPE_PREVENTION)
        self.lead = g.battle_mon(0)["species"]
        g.press_button(g.CATCH)                          # CHANGE in a trainer battle

    @unittest.expectedFailure       # QA-04: A alone goes round SHIFT -> "can't be switched out" for ever
    def test_change_while_trapped_comes_back_with_a_alone(self):
        """An A-masher must end up back at the buttons. Brock's Onix knows Bind, so this can
        happen at the first gym."""
        g = self.g
        self.trapped_change()
        for _ in range(150):
            if g.at_action_menu():
                break
            g.press("A", hold=3, wait=13)
        g.shot("qa-change-when-trapped")
        self.assertTrue(g.at_action_menu(), f"back at the buttons (stuck on {g.callback2()})")

    def test_change_while_trapped_b_gets_back_and_the_pokemon_stays_in(self):
        g = self.g
        self.trapped_change()
        for _ in range(5):
            g.press("A", hold=3, wait=30)
        for _ in range(10):
            if g.at_action_menu():
                break
            g.press("B", hold=3, wait=30)
        self.assertTrue(g.at_action_menu(), "B gets back to the buttons")
        self.assertEqual(g.battle_mon(0)["species"], self.lead)


class SavingAndModes(QaTestCase):
    def test_a_pokemon_caught_without_saving_is_lost_when_the_power_goes_off(self):
        """QA-07: the autosave runs when a story goal is reached, not after a catch. Recorded as
        the game behaves now; the question for Jake is whether a catch should save."""
        g = self.g
        save_game(g)
        story.find_wild_battle(g)
        self.assertTrue(g.wait_action_menu())
        g.set_battle_hp(1, 1)
        g.catch()
        g.advance_text(g.free_to_move, max_presses=600, what="control after catching")
        self.assertEqual(g.party_count(), 2)
        power_cycle_and_continue(g)
        self.assertEqual(g.party_count(), 1, "the catch was not saved")

    def test_the_mode_is_saved_with_the_game(self):
        g = self.g
        g.set_var(VAR_LT_DIFFICULTY, JUNIOR)        # (changing it through OPTION is tested in emu_menus)
        save_game(g)
        power_cycle_and_continue(g)
        self.assertEqual(g.var(VAR_LT_DIFFICULTY), JUNIOR)
        g.set_var(VAR_LT_DIFFICULTY, LITTLE)
        power_cycle_and_continue(g)
        self.assertEqual(g.var(VAR_LT_DIFFICULTY), JUNIOR, "an unsaved change is not kept")

    def test_a_save_made_on_classic_has_no_free_ball_until_a_ball_is_bought(self):
        """Switching to Classic turns off the free Poke Ball. Recorded as behaviour, not a bug."""
        g = self.g
        g.set_var(VAR_LT_DIFFICULTY, CLASSIC)
        balls = bag_count(g, ITEM_POKE_BALL, pocket=0x430, slots=13)
        story.find_wild_battle(g)
        self.assertTrue(g.wait_action_menu())
        self.assertEqual(bag_count(g, ITEM_POKE_BALL, pocket=0x430, slots=13), balls, "no ball was added on Classic")
        g.choose_action(3)                               # the original menu's RUN
        g.advance_text(g.free_to_move, max_presses=200, what="control after running")


if __name__ == "__main__":
    unittest.main()
