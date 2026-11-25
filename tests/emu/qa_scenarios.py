"""QA (2026-11-26): scenarios that start from QA journey save states, with screenshots.

    python3 -m tests.emu.qa_scenarios --starter arrow

Needs work/qa-states/<starter>/ from `python3 -m tests.emu.qa_journey`. Each scenario prints what
happened and saves pictures to builds/qa/scenarios/ (git-ignored). These are observations for the
QA report, not pass/fail tests: where a result is clearly wrong, the report says so and a
regression test goes in tests/emu/emu_qa_flows.py.

    save-reload      after four badges: save from the Start menu, power off and on, CONTINUE:
                     same place, party, badges and mode
    mode-switch      after three badges, switch to Classic and back with the game's own OPTION
                     menu: what changes at once, what stays
    shop             a Poke Mart (opened by its own script): BUY and SELL, and whether selling
                     loses an item for good
    party-screen     the Start menu's POKeMON screen: the choices it offers
    post-game        after the Hall of Fame: CONTINUE, where the player is, whether the arrow
                     shows, and what the player can do next
"""
import argparse
import json
import os
import struct

from .firered import FireRed
from .gba import ROOT, EmulatorError
from .maps import map_name
from .emu_qa_flows import (bag_count, save_game, power_cycle_and_continue, open_start_entry,
                           VAR_LT_DIFFICULTY, START_OPTION)

OUT = os.path.join(ROOT, "builds", "qa", "scenarios")
FLAG_BADGE01_GET, FLAG_SYS_GAME_CLEAR = 0x820, 0x82C
ITEM_POTION = 13


def load(starter, name):
    g = FireRed()
    g.frames(5)
    g.load_state(os.path.join(ROOT, "work", "qa-states", starter, name + ".ss"))
    g.frames(10)
    if not g.free_to_move():
        g.advance_text(g.free_to_move, max_presses=200, what="a quiet start")
    return g


def snapshot(g):
    return {"map": map_name(g.location()), "position": g.position(),
            "party": [(m.species, m.level, m.hp) for m in g.party()],
            "badges": sum(g.flag(FLAG_BADGE01_GET + b) for b in range(8)),
            "mode": g.var(VAR_LT_DIFFICULTY), "money": g.money(), "arrow": g.nav_arrow_shown()}


def shot(g, name):
    g.screenshot(os.path.join(OUT, name + ".png"))
    return name + ".png"


def set_mode_with_option_menu(g, presses_right):
    """Start -> OPTION -> MODE row -> RIGHT/LEFT -> close: exactly as a parent would."""
    open_start_entry(g, START_OPTION)
    g.press("A", wait=90)
    g.press("DOWN", wait=10)
    g.press("DOWN", wait=10)
    for _ in range(abs(presses_right)):
        g.press("RIGHT" if presses_right > 0 else "LEFT", wait=20)
    shot(g, f"mode-option-{g.var(VAR_LT_DIFFICULTY)}")
    g.press("B", wait=120)
    g.press("B", wait=60)


def save_reload(starter):
    g = load(starter, "badge4")
    try:
        before = snapshot(g)
        save_game(g)
        power_cycle_and_continue(g)
        g.frames(30)
        after = snapshot(g)
        shot(g, "save-reload-after")
        return {"before": before, "after": after, "same": {k: before[k] == after[k] for k in before}}
    finally:
        g.close()


def mode_switch(starter):
    g = load(starter, "badge3")
    try:
        result = {"little": snapshot(g), "shots": {}}
        set_mode_with_option_menu(g, 2)                  # Little -> Junior -> Classic
        g.frames(30)
        result["classic"] = snapshot(g)
        result["shots"]["classic"] = shot(g, "mode-classic-field")
        set_mode_with_option_menu(g, -2)                 # back to Little
        g.frames(30)
        result["little_again"] = snapshot(g)
        result["shots"]["little_again"] = shot(g, "mode-little-again-field")
        return result
    finally:
        g.close()


def shop(starter):
    g = load(starter, "badge2")
    try:
        g.give_item(ITEM_POTION, 1)
        money0, potions0 = g.money(), bag_count(g, ITEM_POTION)
        items = g.sym("ViridianCity_Mart_Items")
        g.run_script([0x86, *struct.pack("<I", items)], wait=False)      # pokemart
        g.frames(60)
        names = [shot(g, "shop-0-menu")]
        # SELL: DOWN to SELL, A, (the bag opens on Items) A on the Potion, quantity A, YES A
        for i, key in enumerate(("DOWN", "A", "WAIT", "A", "A", "A", "A", "A"), 1):
            if key == "WAIT":
                g.frames(90)
            else:
                g.press(key, wait=45)
            names.append(shot(g, f"shop-{i}"))
        for _ in range(12):
            if g.free_to_move():
                break
            g.press("B", wait=40)
        return {"money_before": money0, "money_after": g.money(), "potions_before": potions0,
                "potions_after": bag_count(g, ITEM_POTION), "shots": names, "back_on_field": g.free_to_move()}
    finally:
        g.close()


def party_screen(starter):
    g = load(starter, "badge4")
    try:
        open_start_entry(g, 1)                           # POKeMON
        g.press("A", wait=120)
        names = [shot(g, "party-0")]
        g.press("A", wait=40)
        names.append(shot(g, "party-1-choices"))
        for i in range(1, 6):
            g.press("DOWN", wait=15)
            names.append(shot(g, f"party-1-choice-{i}"))
        for _ in range(8):
            if g.free_to_move():
                break
            g.press("B", wait=50)
        return {"shots": names, "party": snapshot(g)["party"]}
    finally:
        g.close()


def post_game(starter):
    g = FireRed()
    try:
        g.frames(5)
        g.load_state(os.path.join(ROOT, "work", "qa-states", starter, "hall-of-fame.ss"))
        g.frames(10)
        seen = []
        for _ in range(900):                              # through the credits to the title, then CONTINUE
            cb = g.callback2()
            if not seen or seen[-1] != cb:
                seen.append(cb)
            if g.free_to_move():
                break
            g.press("A", hold=3, wait=17)
        g.frames(60)
        result = {"screens": seen[:30], "free": g.free_to_move(), "game_clear": g.flag(FLAG_SYS_GAME_CLEAR)}
        if g.free_to_move():
            result.update(snapshot(g))
            result["shot"] = shot(g, "post-game-continue")
            result["goal"] = g.nav_goal()
            # Walk about a little: does anything lead the way?
            moved = []
            for direction in ("DOWN", "DOWN", "LEFT", "LEFT", "UP", "RIGHT"):
                g.step(direction)
                moved.append(g.nav_arrow_shown())
            result["arrow_while_walking"] = moved
            result["shot2"] = shot(g, "post-game-walking")
        return result
    finally:
        g.close()


SCENARIOS = {"save-reload": save_reload, "mode-switch": mode_switch, "shop": shop,
             "party-screen": party_screen, "post-game": post_game}


def main():
    parser = argparse.ArgumentParser(description="QA scenarios from journey save states")
    parser.add_argument("--starter", default="arrow")
    parser.add_argument("names", nargs="*", default=list(SCENARIOS))
    args = parser.parse_args()
    os.makedirs(OUT, exist_ok=True)
    results = {}
    for name in args.names:
        try:
            results[name] = SCENARIOS[name](args.starter)
        except (EmulatorError, FileNotFoundError) as error:
            results[name] = {"error": str(error)}
        print(name, json.dumps(results[name], default=str)[:1500], flush=True)
    with open(os.path.join(OUT, f"results-{args.starter}.json"), "w") as f:
        json.dump(results, f, indent=1, default=str)


if __name__ == "__main__":
    main()
