"""Emulator tests for Milestone 1 (simplified gameplay), Little Trainer preset.

Each test starts from the "route1" checkpoint: Charmander, rival beaten, standing on Route 1 with
an empty bag. Battles are played through the real menus. Where a rare situation is needed (a
long battle, a full move list, a nearly fainted Pokemon), RAM is edited as set-up; the behaviour
under test is always produced by the game itself.
"""
import unittest

from . import story
from .checkpoints import game_at
from .firered import PLAYERS_HOUSE_1F

WON, LOST, RAN, CAUGHT = 1, 2, 4, 7
TACKLE, SCRATCH, GROWL, LEER, TAIL_WHIP, EMBER, METAL_CLAW, SMOKESCREEN = 33, 10, 45, 43, 39, 52, 232, 108
STAT_ATK, STAT_DEF, STAT_ACC = 1, 2, 6
STAGE = [(10, 40), (10, 35), (10, 30), (10, 25), (10, 20), (10, 15), (10, 10),
         (15, 10), (20, 10), (25, 10), (30, 10), (35, 10), (40, 10)]
TOUGH = 300     # HP given to a wild Pokemon when a test needs the battle to last


def exp_for(level):
    """Medium-slow growth (Charmander): total experience needed to reach a level."""
    return (6 * level ** 3) // 5 - 15 * level ** 2 + 100 * level - 140


def staged(value, stage):
    num, den = STAGE[stage]
    return value * num // den


def damage_rolls(level, attack, defense, power, percent, stab=False, crit=False):
    """Every damage value the engine can produce for one hit (the 16 random rolls), using the
    Gen 3 formula from CalculateBaseDamage plus the Little Trainers percentage scaling."""
    base = attack * power * (2 * level // 5 + 2) // defense // 50 + 2
    if crit:
        base *= 2
    base = max(1, base * percent // 100)
    if stab:
        base = base * 15 // 10
    return {max(1, base * roll // 100) for roll in range(85, 101)}


class BattleTestCase(unittest.TestCase):
    def setUp(self):
        self.g = game_at("route1")

    def tearDown(self):
        self.g.close()

    def fight(self):
        """Press ATTACK every turn until the battle ends. Returns the outcome."""
        g = self.g
        while g.wait_action_menu():
            g.attack()
        g.advance_text(g.free_to_move, what="control after battle")
        return g.battle_outcome()

    def battler_stats(self, battler):
        g = self.g
        base = g.sym("gBattleMons") + 0x58 * battler
        stages = g.read(base + 0x18, 8)
        return {"level": g.r8(base + 0x2A), "attack": staged(g.r16(base + 2), stages[STAT_ATK]),
                "defense": staged(g.r16(base + 4), stages[STAT_DEF]), "hp": g.r16(base + 0x28)}


class Milestone1(BattleTestCase):
    # --- healing --------------------------------------------------------------------------
    def test_party_is_fully_healed_after_battle(self):
        g = self.g
        story.find_wild_battle(g)
        self.assertTrue(g.wait_action_menu())
        g.set_battle_hp(1, TOUGH)                     # set-up: the wild Pokemon survives a few turns
        lowest = 999
        for _ in range(4):
            g.attack()
            self.assertTrue(g.wait_action_menu())
            lowest = min(lowest, g.battle_mon(0)["hp"])
        g.set_battle_hp(1, 1)
        self.assertEqual(self.fight(), WON)
        mon = g.party()[0]
        self.assertLess(lowest, mon.max_hp, "set-up: the Pokemon took damage during the battle")
        self.assertEqual(mon.hp, mon.max_hp)
        self.assertEqual(mon.status, 0)

    # --- PP and accuracy ------------------------------------------------------------------
    def test_moves_do_not_use_pp(self):
        g = self.g
        story.find_wild_battle(g)
        self.assertTrue(g.wait_action_menu())
        g.set_battle_hp(1, TOUGH)
        before = g.battle_mon(0)["pp"]
        for _ in range(3):
            g.attack()
            self.assertTrue(g.wait_action_menu())
        self.assertEqual(g.battle_mon(0)["pp"], before)

    def test_damaging_moves_never_miss_even_at_minimum_accuracy(self):
        g = self.g
        story.find_wild_battle(g)
        self.assertTrue(g.wait_action_menu())
        g.set_battle_hp(1, TOUGH)
        for _ in range(8):
            g.w8(g.sym("gBattleMons") + 0x18 + STAT_ACC, 0)   # set-up: accuracy -6 (vanilla: 1 hit in 3)
            before = g.battle_mon(1)["hp"]
            g.attack()
            self.assertTrue(g.wait_action_menu())
            self.assertLess(g.battle_mon(1)["hp"], before, "the attack missed")

    # --- damage scaling -------------------------------------------------------------------
    def test_player_hits_harder_and_wild_pokemon_hit_softer(self):
        g = self.g
        g.edit_party_mon(0, moves=[SCRATCH, GROWL, 0, 0])     # set-up: ATTACK is Scratch (40 power)
        story.find_wild_battle(g)
        self.assertTrue(g.wait_action_menu())
        g.set_battle_hp(1, TOUGH)
        checked_taken = False
        for _ in range(6):
            me, foe = self.battler_stats(0), self.battler_stats(1)
            g.attack()
            self.assertTrue(g.wait_action_menu())
            dealt = foe["hp"] - self.battler_stats(1)["hp"]
            taken = me["hp"] - self.battler_stats(0)["hp"]

            allowed = (damage_rolls(me["level"], me["attack"], foe["defense"], 40, 150)
                       | damage_rolls(me["level"], me["attack"], foe["defense"], 40, 150, crit=True))
            original = damage_rolls(me["level"], me["attack"], foe["defense"], 40, 100)
            self.assertIn(dealt, allowed)
            self.assertGreater(min(allowed), max(original), "boosted damage is above anything the original allows")

            if taken:   # the opponent used Tackle (35 power, same-type bonus for Pidgey and Rattata)
                allowed = damage_rolls(foe["level"], foe["attack"], me["defense"], 35, 60, stab=True)
                original = damage_rolls(foe["level"], foe["attack"], me["defense"], 35, 100, stab=True)
                self.assertIn(taken, allowed, "scaled to 60%, and never a critical hit")
                self.assertLess(max(allowed), min(original), "set-up: scaled and original ranges do not overlap")
                checked_taken = True
                break
        self.assertTrue(checked_taken, "set-up: the wild Pokemon attacked at least once")

    # --- experience -----------------------------------------------------------------------
    def test_boosted_experience_and_bench_share(self):
        g = self.g
        story.find_wild_battle(g)                    # catch a second Pokemon for the bench
        self.assertTrue(g.wait_action_menu())
        g.catch()
        g.advance_text(g.free_to_move, what="control after catching")
        self.assertEqual(g.party_count(), 2)
        lead_before, bench_before = [m.exp for m in g.party()]

        story.find_wild_battle(g)
        self.assertTrue(g.wait_action_menu())
        enemy = g.battle_mon(1)
        self.assertEqual(self.fight(), WON)
        lead_after, bench_after = [m.exp for m in g.party()]

        yield_ = {16: 55, 19: 57}[enemy["species"]]  # Pidgey, Rattata base experience
        base = yield_ * enemy["level"] // 7
        self.assertEqual(lead_after - lead_before, base * 250 // 100, "battler gets x2.5")
        self.assertEqual(bench_after - bench_before, max(1, base * 50 // 100) * 250 // 100,
                         "benched Pokemon gets half of that, also boosted")

    # --- move learning --------------------------------------------------------------------
    def level_up_with_moves(self, moves, to_level):
        g = self.g
        g.edit_party_mon(0, moves=moves, exp=exp_for(to_level) - 1, level=to_level - 1)
        story.find_wild_battle(g)
        self.assertEqual(self.fight(), WON)
        mon = g.party()[0]
        self.assertEqual(mon.level, to_level)
        return mon

    def test_full_move_list_swaps_in_a_better_attack_without_asking(self):
        mon = self.level_up_with_moves([SCRATCH, GROWL, LEER, TAIL_WHIP], 13)   # Metal Claw at 13
        self.assertEqual(mon.moves, [SCRATCH, METAL_CLAW, LEER, TAIL_WHIP],
                         "a status move was replaced; the existing attack was kept")

    def test_full_move_list_skips_a_move_that_does_no_damage(self):
        mon = self.level_up_with_moves([SCRATCH, EMBER, METAL_CLAW, GROWL], 19)  # Smokescreen at 19
        self.assertEqual(mon.moves, [SCRATCH, EMBER, METAL_CLAW, GROWL])

    # --- losing ---------------------------------------------------------------------------
    def test_losing_costs_nothing_and_party_is_restored(self):
        g = self.g
        money = g.money()
        story.find_wild_battle(g)
        self.assertTrue(g.wait_action_menu())
        g.edit_party_mon(0, hp=1)
        g.set_battle_hp(0, 1)                        # set-up: one hit from being too tired
        g.set_battle_hp(1, TOUGH)
        while g.wait_action_menu():
            g.set_battle_hp(1, TOUGH)
            g.attack()
        g.advance_text(g.free_to_move, max_presses=900, what="control after losing")
        self.assertEqual(g.battle_outcome(), LOST)
        self.assertEqual(g.money(), money, "no money was taken")
        self.assertEqual(g.location(), PLAYERS_HOUSE_1F, "sent home to rest")
        mon = g.party()[0]
        self.assertEqual(mon.hp, mon.max_hp)
        g.shot("m1-after-losing")


if __name__ == "__main__":
    unittest.main()
