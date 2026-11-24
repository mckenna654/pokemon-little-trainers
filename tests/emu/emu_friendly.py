"""Emulator tests for the things that keep a non-reader moving: no typing, no questions that
need reading, pictures on Yes/No boxes, automatic move learning and the badge celebration."""
import struct
import unittest

from . import story
from .checkpoints import game_at
from .emu_milestone1 import exp_for
from .firered import FireRed

SCRATCH, GROWL, EMBER, LEER, METAL_CLAW = 10, 45, 52, 43, 232
ITEM_RARE_CANDY = 68
FLAG_BADGE01_GET = 0x820
LEADER_BROCK = 414
BUG_CATCHER_DOUG = 103          # three Pokemon: two chances to be asked "will you switch?"
GREEN, RED = 6, 4               # colour numbers of the tick and the cross in the menu palette


def text(g, addr, length=8):
    """A name as the game stores it (its own character set), up to the terminator."""
    raw = g.read(addr, length)
    out = ""
    for b in raw:
        if b == 0xFF:
            break
        out += chr(b - 0xBB + ord("A")) if 0xBB <= b <= 0xD4 else chr(b - 0xD5 + ord("a")) if 0xD5 <= b <= 0xEE else "?"
    return out


class NewGame(unittest.TestCase):
    def test_a_new_game_needs_only_the_a_button(self):
        g = FireRed()
        try:
            named = 0
            was_naming = False
            for presses in range(1500):
                cb = g.callback2()
                if cb == "CB2_Overworld":
                    break
                naming = cb == "CB2_NamingScreen"
                named += naming and not was_naming
                was_naming = naming
                g.press("A", hold=3, wait=17)
            else:
                self.fail("pressing A alone did not start the game")
            g.frames(120)
            player = text(g, g.r32(g.sym("gSaveBlock2Ptr")))
            rival = text(g, g.r32(g.sym("gSaveBlock1Ptr")) + 0x3A4C)
            self.assertEqual(named, 2, "the two name screens are still there for a grown-up to use")
            self.assertTrue(player and set(player) != {"A"}, f"the player got a real name, not typed letters ({player!r})")
            self.assertTrue(rival and set(rival) != {"A"}, f"the rival got a real name ({rival!r})")
            self.assertTrue(g.free_to_move())
            self.presses = presses
        finally:
            g.close()


class NoReadingNeeded(unittest.TestCase):
    def setUp(self):
        self.g = game_at("route1")

    def tearDown(self):
        self.g.close()

    def mash_a_through_battle(self):
        """Press A until back on the field; report every screen (main callback) seen on the way."""
        g = self.g
        seen = set()
        for _ in range(3000):
            if not g.in_battle() and g.callback2() == "CB2_Overworld":
                break
            seen.add(g.callback2())
            g.press("A", hold=3, wait=13)
        else:
            self.fail("the battle did not end")
        return seen

    def test_catching_a_pokemon_asks_for_no_nickname(self):
        g = self.g
        story.find_wild_battle(g)
        g.wait_action_menu()
        g.catch()
        seen = self.mash_a_through_battle()
        self.assertEqual(g.party_count(), 2, "it was caught")
        self.assertNotIn("CB2_NamingScreen", seen)

    def test_a_gift_pokemon_asks_for_no_nickname(self):
        g = self.g
        question = g.sym("Text_GiveNicknameToThisMon")
        g.w16(g.sym("gSpecialVar_Result"), 77)
        # loadword 0, <text>; callstd MSGBOX_YESNO
        g.run_script([0x0F, 0x00, *struct.pack("<I", question), 0x09, 0x05], max_frames=300)
        self.assertEqual(g.r16(g.sym("gSpecialVar_Result")), 0, "answered 'no' without anyone pressing a button")

    def test_other_questions_are_still_asked_with_a_tick_and_a_cross(self):
        g = self.g
        g.w16(g.sym("gSpecialVar_Result"), 77)
        g.run_script([0x6E, 20, 8], wait=False)       # yesnobox
        g.frames(30)
        self.assertFalse(g.free_to_move(), "the question waits for an answer")
        window = g.sym("gWindows") + 12 * g.r8(g.sym("sYesNoWindowId"))
        width = g.r8(window + 3)
        tiles = g.r32(window + 8)

        def colours(x0, y0, x1, y1):
            found = set()
            for y in range(y0, y1):
                for x in range(x0, x1):
                    byte = g.r8(tiles + ((y // 8) * width + x // 8) * 32 + (y % 8) * 4 + (x % 8) // 2)
                    found.add(byte >> 4 if x % 2 else byte & 0xF)
            return found

        self.assertIn(GREEN, colours(33, 3, 45, 15), "a green tick beside YES")
        self.assertIn(RED, colours(33, 17, 45, 29), "a red cross beside NO")
        self.assertNotIn(RED, colours(33, 3, 45, 15))
        g.shot("friendly-yes-no")
        g.press("A", wait=40)
        self.assertEqual(g.r16(g.sym("gSpecialVar_Result")), 1, "A still answers yes")

    def test_trainers_never_stop_to_ask_about_switching(self):
        g = self.g
        g.edit_party_mon(0, exp=exp_for(30), level=30)
        g.start_trainer_battle(BUG_CATCHER_DOUG)
        seen = self.mash_a_through_battle()
        self.assertFalse({s for s in seen if "PartyMenu" in s}, "the party screen never opened")

    def test_a_tired_pokemon_is_replaced_by_pressing_a(self):
        """When the player's Pokemon is beaten, the party screen opens. Pressing A there must
        send out the next one (the cursor starts on a Pokemon that can battle, not on the tired
        one at the top)."""
        g = self.g
        story.find_wild_battle(g)
        g.wait_action_menu()
        g.catch()
        self.mash_a_through_battle()
        self.assertEqual(g.party_count(), 2, "set-up: a second Pokemon on the bench")
        g.start_trainer_battle(LEADER_BROCK)          # (his Pokemon attack every turn)
        g.wait_action_menu()
        lead = g.battle_mon(0)["species"]
        turns = 0
        def press_a_until_the_battle_menu():
            for _ in range(600):
                if not g.in_battle():
                    return False
                if g.at_action_menu():
                    g.frames(4)
                    return True
                g.press("A", hold=3, wait=13)
            self.fail(f"pressing A did not get back to the battle menu (screen: {g.callback2()})")

        while press_a_until_the_battle_menu():
            if g.battle_mon(0)["species"] != lead:
                break
            turns += 1
            self.assertLess(turns, 30, "the lead Pokemon was never beaten")
            g.set_battle_hp(0, 1)                     # set-up: the next hit beats the lead...
            g.set_battle_hp(1, 300)                   # ...and the opponent outlasts it
            g.attack()
        self.assertTrue(g.in_battle(), "still in the battle")
        self.assertNotEqual(g.battle_mon(0)["species"], lead, "pressing A sent out the second Pokemon")
        g.set_battle_hp(1, 1)
        self.mash_a_through_battle()

    def test_a_rare_candy_teaches_the_new_move_without_questions(self):
        g = self.g
        g.edit_party_mon(0, moves=[SCRATCH, GROWL, EMBER, LEER], exp=exp_for(12), level=12)   # Metal Claw at 13
        g.give_item(ITEM_RARE_CANDY)
        g.press("START", wait=40)
        g.press("DOWN", wait=15)                      # POKEMON -> BAG
        g.press("A", wait=20)
        g.run_until(lambda: g.callback2() == "CB2_BagMenuRun", max_frames=600, what="bag to open")
        g.frames(60)
        seen = set()
        for _ in range(400):                          # item, USE, the Pokemon, then every message
            seen.add(g.callback2())
            if g.party()[0].level == 13 and METAL_CLAW in g.party()[0].moves:
                break
            g.press("A", hold=3, wait=27)
        mon = g.party()[0]
        self.assertEqual(mon.level, 13)
        self.assertIn(METAL_CLAW, mon.moves, "the new move replaced a weak one")
        self.assertIn(EMBER, mon.moves, "the best move was kept")
        self.assertFalse({s for s in seen if "Summary" in s}, "the 'which move should be forgotten' screen never opened")


class BadgeCelebration(unittest.TestCase):
    def test_confetti_falls_when_a_badge_is_earned(self):
        g = game_at("route1")
        try:
            template = g.sym("sConfettiTemplate")

            def confetti():
                base = g.sym("gSprites")
                return sum(1 for i in range(64)
                           if g.r8(base + i * 0x44 + 0x3E) & 1 and g.r32(base + i * 0x44 + 0x14) == template)

            g.frames(30)
            self.assertEqual(confetti(), 0)
            g.run_script([0x29, *struct.pack("<H", FLAG_BADGE01_GET)])     # setflag
            g.frames(60)
            self.assertGreaterEqual(confetti(), 8, "pieces of confetti on screen")
            g.shot("friendly-badge-confetti")
            g.frames(600)
            self.assertEqual(confetti(), 0, "and it stops by itself")
            self.assertTrue(g.free_to_move())
        finally:
            g.close()


if __name__ == "__main__":
    unittest.main()
