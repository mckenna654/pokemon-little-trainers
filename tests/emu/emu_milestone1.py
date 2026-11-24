"""Emulator tests for Milestone 1 (simplified gameplay), Little Trainer preset.

Each test starts from the "route1" checkpoint: Charmander, rival beaten, standing on Route 1 with
an empty bag. Battles are played with real menu input. Where a rare situation is needed (a full
move list, a nearly fainted Pokemon), the party is edited in RAM as set-up; the behaviour under
test is always produced by the game itself.
"""
import unittest

from . import story
from .checkpoints import game_at
from .firered import PLAYERS_HOUSE_1F

WON, LOST, CAUGHT = 1, 2, 7
SCRATCH, GROWL, LEER, TAIL_WHIP, EMBER, METAL_CLAW, SMOKESCREEN = 10, 45, 43, 39, 52, 232, 108
SPLASH = 150
STAT_ATK, STAT_DEF, STAT_ACC = 1, 2, 6
STAGE = [(10, 40), (10, 35), (10, 30), (10, 25), (10, 20), (10, 15), (10, 10),
         (15, 10), (20, 10), (25, 10), (30, 10), (35, 10), (40, 10)]


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

# Medium-slow growth (Charmander): total experience needed to reach a level.
def exp_for(level):
    return (6 * level ** 3) // 5 - 15 * level ** 2 + 100 * level - 140


class Milestone1(unittest.TestCase):
    def setUp(self):
        self.g = game_at("route1")

    def tearDown(self):
        self.g.close()

    def fight(self, slot=0, on_turn=None):
        """Use one move every turn until the battle ends. Returns the outcome."""
        g = self.g
        while g.wait_action_menu():
            if on_turn:
                on_turn()
            g.use_move(slot)
        g.advance_text(g.free_to_move, what="control after battle")
        return g.battle_outcome()

    # --- catching -------------------------------------------------------------------------
    def test_catch_with_empty_bag_at_full_health_and_ball_is_not_used_up(self):
        g = self.g
        self.assertEqual(g.ball_count(), 0, "set-up: the bag starts with no Poke Balls")
        for expected_party in (2, 3):
            story.find_wild_battle(g)
            self.assertTrue(g.wait_action_menu())
            self.assertEqual(g.ball_count(), 1, "a Poke Ball is always available in a wild battle")
            enemy = g.battle_mon(1)
            self.assertEqual(enemy["hp"], enemy["max_hp"], "catching must work at full health")
            g.throw_ball()
            g.advance_text(g.free_to_move, what="control after catching")
            self.assertEqual(g.battle_outcome(), CAUGHT)
            self.assertEqual(g.party_count(), expected_party)
            self.assertEqual(g.ball_count(), 1, "the ball was not used up")
        g.shot("m1-after-two-catches")

    # --- healing --------------------------------------------------------------------------
    def test_party_is_fully_healed_after_battle(self):
        g = self.g
        story.find_wild_battle(g)
        lowest = [999]

        def watch():
            lowest[0] = min(lowest[0], g.battle_mon(0)["hp"])

        # Growl (slot 1) does no damage, so the wild Pokemon gets several turns to hurt us first.
        for _ in range(3):
            self.assertTrue(g.wait_action_menu())
            watch()
            g.use_move(1)
        self.assertEqual(self.fight(0, on_turn=watch), WON)
        mon = g.party()[0]
        self.assertLess(lowest[0], mon.max_hp, "set-up: the Pokemon took damage during the battle")
        self.assertEqual(mon.hp, mon.max_hp)
        self.assertEqual(mon.status, 0)

    # --- PP and accuracy ------------------------------------------------------------------
    def test_moves_do_not_use_pp(self):
        g = self.g
        story.find_wild_battle(g)
        self.assertTrue(g.wait_action_menu())
        before = g.battle_mon(0)["pp"]
        g.use_move(1)                    # Growl
        self.assertTrue(g.wait_action_menu())
        g.use_move(0)                    # Scratch
        if g.wait_action_menu():
            self.assertEqual(g.battle_mon(0)["pp"], before)
        else:
            self.assertEqual(g.party()[0].pp, before)

    def test_damaging_moves_never_miss_even_at_minimum_accuracy(self):
        g = self.g
        hits = 0
        for _ in range(4):
            story.find_wild_battle(g)
            while g.wait_action_menu():
                # set-up: accuracy stage -6 (vanilla: about 1 hit in 3)
                g.w8(g.sym("gBattleMons") + 0x18 + STAT_ACC, 0)
                enemy_before = g.battle_mon(1)["hp"]
                g.use_move(0)
                still_fighting = g.wait_action_menu()
                enemy_after = g.battle_mon(1)["hp"] if still_fighting else 0
                self.assertLess(enemy_after, enemy_before, "Scratch missed")
                hits += 1
                if not still_fighting:
                    break
            g.advance_text(g.free_to_move, what="control after battle")
        self.assertGreaterEqual(hits, 6, "enough attacks to make luck implausible")

    # --- damage scaling -------------------------------------------------------------------
    def battler_stats(self, battler):
        g = self.g
        base = g.sym("gBattleMons") + 0x58 * battler
        stages = g.read(base + 0x18, 8)
        return {"level": g.r8(base + 0x2A), "attack": staged(g.r16(base + 2), stages[STAT_ATK]),
                "defense": staged(g.r16(base + 4), stages[STAT_DEF]), "hp": g.r16(base + 0x28)}

    def test_player_hits_harder_and_wild_pokemon_hit_softer(self):
        g = self.g
        g.edit_party_mon(0, moves=[SCRATCH, SPLASH, 0, 0])      # set-up: Splash lets a turn pass harmlessly
        story.find_wild_battle(g)

        # Opponent's Tackle (35 power, same-type bonus for Pidgey and Rattata), scaled to 60%, no criticals.
        taken = 0
        for _ in range(6):
            self.assertTrue(g.wait_action_menu())
            me, foe = self.battler_stats(0), self.battler_stats(1)
            g.use_move(1)
            self.assertTrue(g.wait_action_menu())
            taken = me["hp"] - self.battler_stats(0)["hp"]
            if taken:
                break
        self.assertGreater(taken, 0, "set-up: the wild Pokemon attacked")
        allowed = damage_rolls(foe["level"], foe["attack"], me["defense"], 35, 60, stab=True)
        original = damage_rolls(foe["level"], foe["attack"], me["defense"], 35, 100, stab=True)
        self.assertIn(taken, allowed)
        self.assertLess(max(allowed), min(original), "set-up: scaled and original damage do not overlap")

        # Player's Scratch (40 power), scaled to 150%.
        me, foe = self.battler_stats(0), self.battler_stats(1)
        g.use_move(0)
        still_fighting = g.wait_action_menu()
        dealt = foe["hp"] - (self.battler_stats(1)["hp"] if still_fighting else 0)
        allowed = (damage_rolls(me["level"], me["attack"], foe["defense"], 40, 150)
                   | damage_rolls(me["level"], me["attack"], foe["defense"], 40, 150, crit=True))
        original = damage_rolls(me["level"], me["attack"], foe["defense"], 40, 100)
        if dealt < foe["hp"]:
            self.assertIn(dealt, allowed)
        self.assertGreater(min(allowed), max(original), "boosted damage is above anything the original allows")
        self.assertGreaterEqual(dealt, min(min(allowed), foe["hp"]))

    # --- experience -----------------------------------------------------------------------
    def test_boosted_experience_and_bench_share(self):
        g = self.g
        story.find_wild_battle(g)                    # catch a second Pokemon for the bench
        self.assertTrue(g.wait_action_menu())
        g.throw_ball()
        g.advance_text(g.free_to_move, what="control after catching")
        self.assertEqual(g.party_count(), 2)
        lead_before, bench_before = [m.exp for m in g.party()]

        story.find_wild_battle(g)
        self.assertTrue(g.wait_action_menu())
        enemy = g.battle_mon(1)
        self.assertEqual(self.fight(0), WON)
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
        self.assertEqual(self.fight(0), WON)
        mon = g.party()[0]
        self.assertEqual(mon.level, to_level)
        return mon

    def test_full_move_list_swaps_in_a_better_attack_without_asking(self):
        mon = self.level_up_with_moves([SCRATCH, GROWL, LEER, TAIL_WHIP], 13)   # Metal Claw at 13
        self.assertEqual(mon.moves, [SCRATCH, METAL_CLAW, LEER, TAIL_WHIP],
                         "a status move was replaced; the attack the child uses was kept")

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
        g.w16(g.sym("gBattleMons") + 0x28, 1)        # set-up: one hit from fainting
        while g.wait_action_menu():
            g.use_move(1)                            # Growl: never defeats the wild Pokemon
        g.advance_text(g.free_to_move, max_presses=900, what="control after losing")
        self.assertEqual(g.battle_outcome(), LOST)
        self.assertEqual(g.money(), money, "no money was taken")
        self.assertEqual(g.location(), PLAYERS_HOUSE_1F, "sent home to rest")
        mon = g.party()[0]
        self.assertEqual(mon.hp, mon.max_hp)
        g.shot("m1-after-losing")


if __name__ == "__main__":
    unittest.main()
