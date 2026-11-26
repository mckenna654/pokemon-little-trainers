"""Little Trainer's gentler type matchups (gentleTypes), applied once to the overall matchup: the
player's "not very effective" hits are raised by half (1/2 -> 3/4) and the opponent's "super
effective" hits are cut by a quarter (x2 -> x1.5). The same for every Pokemon and type; mixed
matchups and the other direction are unchanged; Classic keeps the original numbers.

Each test sets the types of both Pokemon, plays turns until both sides have landed a hit, and
checks the exact damage against every value the engine can roll."""
import unittest

from . import story
from .checkpoints import game_at
from .emu_milestone1 import EMBER, SCRATCH, TOUGH

VAR_LT_DIFFICULTY, CLASSIC = 0x4029, 2
TYPE_NORMAL, TYPE_ROCK, TYPE_STEEL, TYPE_WATER, TYPE_GRASS = 0, 5, 8, 11, 12
BATTLE_MON_SIZE = 0x58
SQUIRTLE = 7
HALF, DOUBLE = (5, 10), (20, 10)          # one type chart step, as ModulateDmgByType applies it


def rolls(level, attack, defense, power, percent, steps, gentle=None, crits=False):
    """Every damage value for one hit: the Little Trainers percentage, then each type chart step
    (minimum 1), then the gentle step if any, then the random roll, as Cmd_typecalc and
    adjustnormaldamage do. damage_rolls in emu_milestone1.py, with the type steps added."""
    out = set()
    for crit in ((False, True) if crits else (False,)):
        base = attack * power * (2 * level // 5 + 2) // defense // 50 + 2
        if crit:
            base *= 2
        base = max(1, base * percent // 100)
        for num, den in steps:
            base = max(1, base * num // den)
        if gentle:
            base = max(1, base * gentle[0] // gentle[1])
        out |= {max(1, base * roll // 100) for roll in range(85, 101)}
    return out


class TypeMatchups(unittest.TestCase):
    def setUp(self):
        self.g = game_at("route1")

    def tearDown(self):
        self.g.close()

    def mon(self, battler):
        return self.g.sym("gBattleMons") + BATTLE_MON_SIZE * battler

    def exchange(self, my_move, my_types, foe_move, foe_types, classic=False):
        """A wild battle where the player only knows my_move and the foe only my foe_move, with
        the given types (neither side's move matches its own types: no same-type bonus). Returns
        the damage of one landed hit each way and the stats to work out what it should be."""
        g = self.g
        if classic:
            g.set_var(VAR_LT_DIFFICULTY, CLASSIC)
        g.edit_party_mon(0, moves=[my_move, 0, 0, 0])
        story.find_wild_battle(g)
        self.assertTrue(g.wait_action_menu())
        me, foe = self.mon(0), self.mon(1)
        for base, types in ((me, my_types), (foe, foe_types)):
            g.w8(base + 0x21, types[0])
            g.w8(base + 0x22, types[1])
        g.w16(foe + 0x0C, foe_move)                     # set-up: the foe only knows foe_move
        for slot in range(1, 4):
            g.w16(foe + 0x0C + 2 * slot, 0)
        g.w8(foe + 0x24, 25)
        for base in (me, foe):                          # set-up: big enough hits to tell the steps apart
            g.w16(base + 2, 60)
            g.w16(base + 8, 60)
        stats = {"me": {"level": g.r8(me + 0x2A), "atk": 60, "def": g.r16(me + 4), "spdef": g.r16(me + 0xA)},
                 "foe": {"level": g.r8(foe + 0x2A), "atk": 60, "def": g.r16(foe + 4), "spdef": g.r16(foe + 0xA)}}
        dealt = taken = None
        for _ in range(8):                              # until both sides have landed a hit
            g.set_battle_hp(0, TOUGH)
            g.set_battle_hp(1, TOUGH)
            g.w32(me + 0x4C, 0)                         # set-up: no burn (Classic has no Safeguard)
            if classic:
                g.use_move(0)
            else:
                g.attack()
            self.assertTrue(g.wait_action_menu(), "set-up: both survive the turn")
            if dealt is None and g.last_move(0) == my_move and g.battle_mon(1)["hp"] < TOUGH:
                dealt = TOUGH - g.battle_mon(1)["hp"]
            if taken is None and g.last_move(1) == foe_move and g.battle_mon(0)["hp"] < TOUGH:
                taken = TOUGH - g.battle_mon(0)["hp"]
            if dealt is not None and taken is not None:
                break
        self.assertIsNotNone(dealt, "set-up: the player's attack hit")
        self.assertIsNotNone(taken, "set-up: the foe's attack hit (it can miss)")
        return dealt, taken, stats

    # Scratch is physical (Attack against Defence), Ember special (Sp. Atk against Sp. Def): power 40 each.
    def expect(self, dealt, taken, s, mine, theirs, mine_percent, their_percent, classic=False):
        my_move, my_steps, my_gentle = mine
        foe_move, foe_steps, foe_gentle = theirs
        me, foe = s["me"], s["foe"]
        my_def = foe["def"] if my_move == SCRATCH else foe["spdef"]
        foe_def = me["def"] if foe_move == SCRATCH else me["spdef"]
        self.assertIn(dealt, rolls(me["level"], me["atk"], my_def, 40, mine_percent, my_steps, my_gentle, crits=True),
                      "the player's hit")
        self.assertIn(taken, rolls(foe["level"], foe["atk"], foe_def, 40, their_percent, foe_steps, foe_gentle, crits=classic),
                      "the foe's hit")

    def test_little_trainer_softens_resisted_hits_by_the_player_and_super_effective_hits_on_them(self):
        # Scratch into Rock: 1/2 -> 3/4. Ember into Grass: x2 -> x1.5.
        dealt, taken, s = self.exchange(SCRATCH, (TYPE_GRASS, TYPE_GRASS), EMBER, (TYPE_ROCK, TYPE_ROCK))
        self.expect(dealt, taken, s, (SCRATCH, [HALF], (3, 2)), (EMBER, [DOUBLE], (3, 4)), 150, 50)

    def test_little_trainer_leaves_the_other_direction_alone(self):
        # The player's Ember into Grass stays x2; the foe's Scratch into Rock stays 1/2.
        dealt, taken, s = self.exchange(EMBER, (TYPE_ROCK, TYPE_ROCK), SCRATCH, (TYPE_GRASS, TYPE_GRASS))
        self.expect(dealt, taken, s, (EMBER, [DOUBLE], None), (SCRATCH, [HALF], None), 150, 50)

    def test_little_trainer_double_resistance_and_mixed_matchups(self):
        # Scratch into Rock/Steel: 1/4 -> 3/8. Ember into Grass/Water: 1/2 then x2 (the chart's order),
        # neutral, unchanged.
        dealt, taken, s = self.exchange(SCRATCH, (TYPE_GRASS, TYPE_WATER), EMBER, (TYPE_ROCK, TYPE_STEEL))
        self.expect(dealt, taken, s, (SCRATCH, [HALF, HALF], (3, 2)), (EMBER, [HALF, DOUBLE], None), 150, 50)

    def test_the_suggested_attack_follows_the_gentler_numbers(self):
        """Charmander against a wild Squirtle: Ember (own type, x1.5) is resisted, so it now does
        1.5 x 3/4 = 1.125 times Scratch's damage. The ring starts on the stronger one."""
        g = self.g
        g.edit_party_mon(0, moves=[SCRATCH, EMBER, 0, 0])
        g.start_wild_battle(SQUIRTLE, 5)
        self.assertTrue(g.wait_action_menu())
        self.assertEqual(g.menu_cursor(), g.SPECIAL, "Ember is suggested")

    def test_classic_keeps_the_original_matchups(self):
        dealt, taken, s = self.exchange(SCRATCH, (TYPE_GRASS, TYPE_GRASS), EMBER, (TYPE_ROCK, TYPE_ROCK), classic=True)
        self.expect(dealt, taken, s, (SCRATCH, [HALF], None), (EMBER, [DOUBLE], None), 100, 100, classic=True)


if __name__ == "__main__":
    unittest.main()
