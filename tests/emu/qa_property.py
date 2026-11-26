"""QA (2026-11-26): generated tests from save states taken during a QA journey.

    python3 -m tests.emu.qa_property --starter arrow --jobs 4          # all checks, every few goals
    python3 -m tests.emu.qa_property --check mash --seeds 1 2 3        # one kind of check

Needs the save states written by `python3 -m tests.emu.qa_journey` for the same ROM
(work/qa-states/<starter>/goalNNN.ss). Each check starts from one of those states:

    wander     take N random steps, sometimes pressing A at whatever is in front (people,
               signs, defeated trainers), and A/B when not free to walk, then follow the arrow:
               the next story goal must still be reached
    backtrack  walk the opposite way to the arrow for N steps (back along the path, often into
               the previous map), then follow the arrow: the next goal must still be reached
    mash       N random presses of every button, held for random lengths, then B to get out:
               the game must come back to the player, with no Pokemon lost
    arrows     follow the arrow and look at every direction it shows: each picture must be one
               whole arrow pointing the way it says

Every check is seeded. A failure is replayed and shrunk (at most 150 replays) to a shorter list of
actions that still fails the same way, and written with its seed, state, actions and the ROM's and
state's SHA-1 to builds/qa/property/failures/. Replay one with `--replay FILE`. The emulator is
deterministic, so replaying the actions from the same state on the same ROM repeats the result.
"""
import argparse
import json
import multiprocessing
import os
import random
import sys
import time

from .firered import FireRed
from .gba import ROOT, EmulatorError
from .maps import map_name

DIRS = ("UP", "DOWN", "LEFT", "RIGHT")
OPPOSITE = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}
BUTTONS = ("A", "B", "START", "SELECT", "UP", "DOWN", "LEFT", "RIGHT", "L", "R")
OUT = os.path.join(ROOT, "builds", "qa", "property")


# --- what can be lost ------------------------------------------------------------------------------
def pokemon_owned(g):
    from .emu_qa_flows import storage_count
    return g.party_count() + storage_count(g)


def items_owned(g):
    """Total quantity of everything in the bag (all pockets)."""
    import struct
    sb1, sb2 = g.r32(g.sym("gSaveBlock1Ptr")), g.r32(g.sym("gSaveBlock2Ptr"))
    key = g.r32(sb2 + 0xF20) & 0xFFFF
    total = 0
    for offset, slots in ((0x310, 42), (0x3B8, 30), (0x430, 13), (0x464, 58), (0x54C, 43)):
        for item, quantity in struct.iter_unpack("<HH", g.read(sb1 + offset, 4 * slots)):
            if item:
                total += quantity ^ key
    return total


# --- actions: everything a check does, so it can be replayed exactly ----------------------------------
def do(g, action):
    kind, value = action
    if kind == "step":
        g.step(value)
    elif kind == "press":
        key, hold, wait = value
        g.press(key, hold=hold, wait=wait)
    elif kind == "battle":                 # mash A to the end, as the journey does
        for _ in range(6000):
            if not g.in_battle():
                break
            if g.callback2() == "CB2_NamingScreen":
                g.press("START", wait=20)
                g.press("A", wait=40)
            else:
                g.press("A", hold=3, wait=13)


def generate(check, g, rng, length):
    """Make and perform the actions of one generated run, returning them."""
    actions = []
    for _ in range(length):
        if check != "mash" and g.in_battle():
            action = ("battle", None)
        elif check == "mash":
            action = ("press", (rng.choice(BUTTONS), rng.choice((1, 3, 3, 8, 30)), rng.choice((4, 12, 20, 40))))
        elif not g.free_to_move():
            action = ("press", (rng.choice(("A", "A", "B")), 3, 17))
        elif check == "backtrack" and g.nav_arrow():
            action = ("step", OPPOSITE[g.nav_arrow()])
        elif rng.random() < 0.2:                         # talk to whoever or whatever is in front
            action = ("press", ("A", 3, 17))
        else:
            action = ("step", rng.choice(DIRS))
        actions.append(action)
        do(g, action)
    return actions


def get_back(g):
    """After mashing: B out of menus, finish any battle, until the player can walk again."""
    for _ in range(80):
        if g.free_to_move():
            return True
        if g.in_battle():
            do(g, ("battle", None))
        else:
            g.press("B", hold=3, wait=30)
    for _ in range(80):                    # some messages only close with A
        if g.free_to_move():
            return True
        g.press("A", hold=3, wait=20)
    return g.free_to_move()


# --- one check from one state ---------------------------------------------------------------------
def run_one(task, actions=None):
    """Returns (ok, detail, actions). With `actions`, replays them instead of generating."""
    check, state, seed, length = task["check"], task["state"], task["seed"], task["length"]
    g = FireRed()
    try:
        g.frames(5)
        g.load_state(state)
        g.frames(5)
        if not g.free_to_move():
            g.advance_text(g.free_to_move, max_presses=200, what="a quiet start")
        goal0 = g.nav_goal()
        owned0, items0 = pokemon_owned(g), items_owned(g)
        rng = random.Random(seed)
        if actions is None:
            actions = generate(check, g, rng, length)
        else:
            for action in actions:
                do(g, action)
        if check == "mash":
            if not get_back(g):
                return False, f"did not get back to the field (screen {g.callback2()}, map {map_name(g.location())})", actions
            lost = owned0 - pokemon_owned(g)
            if lost > 0:
                return False, f"{lost} Pokemon lost", actions
            items_used = items0 - items_owned(g)
            return True, {"items_used": items_used, "map": map_name(g.location())}, actions
        # wander / backtrack: the arrow must still lead on
        start = g.frame

        def goal_reached():
            goal = g.nav_goal()
            return goal != goal0 and goal != 255 or g.flag(0x82C)

        try:
            g.follow_arrow(goal_reached, max_actions=5000, what=f"goal after {goal0}")
        except EmulatorError as error:
            return False, f"arrow did not lead on: {error}", actions
        return True, {"frames_to_goal": g.frame - start, "goal": g.nav_goal()}, actions
    except EmulatorError as error:
        return False, f"emulator error: {error}", actions
    finally:
        g.close()


def same_failure(a, b):
    """Two failure details describe the same problem (same kind of failure, same first words)."""
    return str(a).split(":")[0] == str(b).split(":")[0]


def shrink(task, actions, detail, budget=150):
    """Delta debugging: a shorter list of actions (from the same state) that fails *the same way*.
    A candidate that fails differently is not accepted, and at most `budget` replays are made."""
    n, runs = 2, 0
    while len(actions) >= 2 and runs < budget:
        chunk = max(1, len(actions) // n)
        for start in range(0, len(actions), chunk):
            if runs >= budget:
                break
            candidate = actions[:start] + actions[start + chunk:]
            ok, candidate_detail, _ = run_one(task, candidate)
            runs += 1
            if not ok and same_failure(candidate_detail, detail):
                actions, n = candidate, max(n - 1, 2)
                break
        else:
            if chunk == 1:
                break
            n = min(len(actions), n * 2)
    return actions, runs


def file_sha1(path):
    import hashlib
    with open(path, "rb") as f:
        return hashlib.sha1(f.read()).hexdigest()


def FireRed_rom():
    from .firered import ROM
    return ROM


def replay(path):
    """Replay a saved failure: its shrunk actions (or all of them) from its state, on this ROM."""
    with open(path) as f:
        failure = json.load(f)
    if failure.get("rom_sha1") and failure["rom_sha1"] != file_sha1(FireRed_rom()):
        print("warning: this ROM is not the one the failure was found on; save states may not load", file=sys.stderr)
    actions = [tuple(a) if a[0] != "press" else ("press", tuple(a[1])) for a in failure.get("shrunk_actions") or failure["actions"]]
    ok, detail, _ = run_one(failure, actions)
    print(json.dumps({"reproduced": not ok, "detail": detail, "actions": len(actions)}, default=str))
    return 0 if ok else 1


def worker(task):
    started = time.time()
    ok, detail, actions = run_one(task)
    result = dict(task, ok=ok, detail=detail, seconds=round(time.time() - started), actions_count=len(actions))
    if not ok and task.get("shrink", True):
        small, runs = shrink(task, actions, detail)
        ok2, detail2, _ = run_one(task, small)
        result.update(shrunk_actions=small, shrunk_detail=detail2, shrink_runs=runs,
                      shrunk_reproduces=not ok2 and same_failure(detail2, detail))
        os.makedirs(os.path.join(OUT, "failures"), exist_ok=True)
        name = f"{task['check']}-{os.path.basename(task['state'])[:-3]}-seed{task['seed']}.json"
        with open(os.path.join(OUT, "failures", name), "w") as f:
            json.dump(dict(result, actions=actions, rom_sha1=file_sha1(FireRed_rom()), state_sha1=file_sha1(task["state"])),
                      f, indent=1)
    return result


# --- arrow pictures ---------------------------------------------------------------------------------
def judge_arrow(grid, shown):
    """None if the picture is one whole arrow pointing the way `shown` says, else what is wrong."""
    if not any(any(row) for row in grid):
        return "the picture is blank"
    if "-" in shown:                                      # turn it to point up and to the right
        if "DOWN" in shown:
            grid = grid[::-1]
        if "LEFT" in shown:
            grid = [row[::-1] for row in grid]
        if any(grid[y][x] != grid[15 - x][15 - y] for y in range(16) for x in range(16)):
            return "the two sides do not match"
        slices = {k: sum(grid[y][x] for y in range(16) for x in range(16) if x - y == k) for k in range(-15, 16)}
        inked = [k for k in slices if slices[k]]
        widest = max(inked, key=lambda k: slices[k])
        if slices[max(inked)] > 2 or widest <= 0 or min(inked) > -8:
            return "not pointing into its corner"
        return None
    if shown == "DOWN":                                   # turn it to point up
        grid = grid[::-1]
    elif shown == "LEFT":
        grid = [list(row) for row in zip(*grid)]
    elif shown == "RIGHT":
        grid = [list(row) for row in zip(*[row[::-1] for row in grid])]
    columns = [x for x in range(16) if any(row[x] for row in grid)]
    grid = [row[columns[0]:columns[-1] + 1] for row in grid if any(row)]
    widths = [sum(row) for row in grid]
    if any(row != row[::-1] for row in grid):
        return "the two sides do not match"
    widest = widths.index(max(widths))
    if widths[0] > 4 or widths[:widest + 1] != sorted(widths[:widest + 1]) or widths[-1] >= max(widths):
        return "not an arrow shape pointing that way"
    return None


def arrow_pictures(starter, budget=300):
    """Follow the arrow from every goal state, judging the first picture of each direction seen,
    and the arrow's place beside the player."""
    from .emu_playtest1 import ArrowPicture
    picture = ArrowPicture.arrow_picture
    folder = os.path.join(ROOT, "work", "qa-states", starter)
    seen, problems = {}, []
    for state in sorted(f for f in os.listdir(folder) if f.startswith("goal") and f != "goal255.ss"):
        g = FireRed()
        try:
            g.frames(5)
            g.load_state(os.path.join(folder, state))
            g.frames(5)

            def look():
                shown = g.nav_arrow_shown() if g.free_to_move() else None
                if shown:
                    record = seen.setdefault(shown, {"count": 0, "where": []})
                    record["count"] += 1
                    if len(record["where"]) < 3 and map_name(g.location()) not in record["where"]:
                        record["where"].append(map_name(g.location()))
                        problem = judge_arrow(picture(None, g), shown)
                        if problem:
                            problems.append({"state": state, "shown": shown, "problem": problem})
                            g.shot(f"qa-arrow-problem-{shown}-{state[:-3]}")
                return False

            try:
                g.follow_arrow(look, max_actions=budget, what="(looking at arrows)")
            except EmulatorError as error:
                if "did not reach" not in str(error):       # only the spent budget is expected
                    problems.append({"state": state, "shown": None, "problem": f"stopped: {error}"})
        finally:
            g.close()
    return seen, problems


def tasks_for(starter, checks, seeds, every, length):
    folder = os.path.join(ROOT, "work", "qa-states", starter)
    states = sorted(f for f in os.listdir(folder) if f.startswith("goal") and f.endswith(".ss") and f != "goal255.ss")
    chosen = states[::every]
    return [{"check": check, "state": os.path.join(folder, state), "seed": seed, "length": length[check]}
            for check in checks for state in chosen for seed in seeds]


def main():
    parser = argparse.ArgumentParser(description="QA generated checks from journey save states")
    parser.add_argument("--starter", default="arrow")
    parser.add_argument("--check", nargs="*", default=["wander", "backtrack", "mash"],
                        choices=["wander", "backtrack", "mash", "arrows"])
    parser.add_argument("--replay", help="replay a failure file from builds/qa/property/failures/")
    parser.add_argument("--seeds", nargs="*", type=int, default=[1, 2])
    parser.add_argument("--every", type=int, default=3, help="use every Nth goal state")
    parser.add_argument("--jobs", type=int, default=4)
    args = parser.parse_args()
    if args.replay:
        sys.exit(replay(args.replay))
    length = {"wander": 40, "backtrack": 30, "mash": 150}
    if "arrows" in args.check:
        seen, problems = arrow_pictures(args.starter)
        os.makedirs(OUT, exist_ok=True)
        with open(os.path.join(OUT, f"arrows-{args.starter}.json"), "w") as f:
            json.dump({"seen": seen, "problems": problems}, f, indent=1)
        if not seen:
            problems.append({"state": None, "shown": None, "problem": "no arrow was seen at all"})
        print(json.dumps({"directions": {k: v["count"] for k, v in seen.items()}, "problems": problems}, indent=1))
        args.check = [c for c in args.check if c != "arrows"]
        if not args.check:
            sys.exit(1 if problems else 0)
    tasks = tasks_for(args.starter, args.check, args.seeds, args.every, length)
    os.makedirs(OUT, exist_ok=True)
    print(f"{len(tasks)} runs", file=sys.stderr, flush=True)
    results = []
    with multiprocessing.Pool(args.jobs) as pool:
        for result in pool.imap_unordered(worker, tasks):
            results.append(result)
            print(f"  {'ok  ' if result['ok'] else 'FAIL'} {result['check']:9s} {os.path.basename(str(result['state']))} "
                  f"seed {result['seed']}: {result['detail']}", file=sys.stderr, flush=True)
    name = "-".join(args.check)
    with open(os.path.join(OUT, f"results-{args.starter}-{name}.json"), "w") as f:
        json.dump(results, f, indent=1)
    failed = [r for r in results if not r["ok"]]
    print(f"{len(results) - len(failed)} passed, {len(failed)} failed", file=sys.stderr)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
