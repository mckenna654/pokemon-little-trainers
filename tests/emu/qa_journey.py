"""QA journey: the whole game from a fresh save, with pictures, a log and save states on the way.

    python3 -m tests.emu.qa_journey --starter arrow       # take whichever starter the arrow leads to
    python3 -m tests.emu.qa_journey --starter bulbasaur   # walk to that ball instead, then follow the arrow
    python3 -m tests.emu.qa_journey --starter charmander --shots key

Normal inputs only, like `emu_full_game.py`: the player walks where the arrow points, presses A
when there is no arrow or something is in the way, and mashes A in battles. Choosing a starter
other than the arrow's means walking to that ball and pressing A, which is also a normal input.
No memory is written and no story flag is set.

Writes, under builds/qa/journey-<starter>/ (git-ignored: screenshots of the game stay local):
    shot-NNNN.png, sheet-NN.png, INDEX.txt   pictures through the whole game (deduplicated)
    events.jsonl                             maps entered, battles, badges, party changes, arrows
    summary.json                             totals, timings, arrow directions seen, the result
and under work/qa-states/<starter>/ (git-ignored) a save state at each new story goal and badge,
for targeted tests that start mid-game. Save states only work with the exact same ROM.

The run is deterministic for a given ROM: the same command gives the same play.
"""
import argparse
import hashlib
import json
import os
import sys
import time

from . import story
from .firered import FireRed
from .gba import ROOT, EmulatorError
from .maps import map_name
from .screen_tour import write_sheet, PER_SHEET, COLUMNS

FLAG_BADGE01_GET, FLAG_SYS_GAME_CLEAR = 0x820, 0x82C
BATTLE_TYPE_TRAINER = 0x8
BADGES = ["Boulder", "Cascade", "Thunder", "Rainbow", "Soul", "Marsh", "Volcano", "Earth"]
ARROWS = ("DOWN", "UP", "LEFT", "RIGHT", "UP-RIGHT", "UP-LEFT", "DOWN-RIGHT", "DOWN-LEFT")
STALL_FRAMES = 60 * 60 * 60     # an hour of play with no new map or badge: stop and report


class Journey:
    def __init__(self, starter, shots, out=None, states=None, max_shots=900, from_state=None):
        self.starter = starter
        self.from_state = from_state
        self.mode = shots
        self.out = out or os.path.join(ROOT, "builds", "qa", f"journey-{starter}")
        self.states = states or os.path.join(ROOT, "work", "qa-states", starter)
        for folder in (self.out, self.states):
            os.makedirs(folder, exist_ok=True)
            for name in os.listdir(folder):
                if name.endswith((".png", ".ss", ".jsonl", ".json", ".txt")):
                    os.remove(os.path.join(folder, name))
        self.log = open(os.path.join(self.out, "events.jsonl"), "w")
        self.max_shots = max_shots
        self.shots, self.seen = [], set()
        self.maps, self.badges, self.goal = set(), set(), None
        self.arrows = {}                 # direction -> {"count": n, "first": shot or None}
        self.arrow_by_map = {}
        self.battles = []
        self.field_actions = self.no_arrow_presses = self.field_since_shot = 0
        self.progress_frame = 0
        self.party_seen = None
        self.started = time.time()

    # --- recording ------------------------------------------------------------------------------
    def event(self, kind, **data):
        data.update(kind=kind, frame=self.g.frame, minute=self.g.frame // 3600, map=self.where())
        self.log.write(json.dumps(data) + "\n")
        self.log.flush()

    def where(self):
        try:
            return map_name(self.g.location())
        except Exception:
            return str(self.g.location())

    def shot(self, scene, force=False):
        if len(self.shots) >= self.max_shots and not force:
            return None
        path = os.path.join(self.out, f"shot-{len(self.shots) + 1:04d}.png")
        self.g.screenshot(path)
        with open(path, "rb") as f:
            digest = hashlib.sha1(f.read()).hexdigest()
        if digest in self.seen:
            os.remove(path)
            return None
        self.seen.add(digest)
        label = f"{scene} [{self.where()}, {self.g.frame // 3600} min]"
        self.shots.append((path, label))
        return os.path.basename(path)

    def save_state(self, name):
        self.g.save_state(os.path.join(self.states, name + ".ss"))

    # --- what the player sees and has --------------------------------------------------------
    def party(self):
        return [(m.species, m.level) for m in self.g.party()]

    def check_party(self):
        party = self.party()
        if party != self.party_seen:
            self.event("party", party=party)
            self.party_seen = party

    def watch_field(self):
        """Called before every action on the field. Returns True when the game is finished."""
        g = self.g
        if g.flag(FLAG_SYS_GAME_CLEAR):
            return True
        if not g.free_to_move():
            return False
        self.field_actions += 1
        name = self.where()
        if name not in self.maps:
            self.maps.add(name)
            self.progress_frame = g.frame
            g.frames(2)
            self.event("map", shot=self.shot("first look at a new place"))
            self.check_party()
        goal = g.nav_goal()
        if goal != self.goal:
            self.event("goal", goal=goal)
            self.goal = goal
            self.save_state(f"goal{goal:03d}")
        held = {b for b in range(8) if g.flag(FLAG_BADGE01_GET + b)}
        for b in sorted(held - self.badges):
            self.badges.add(b)
            self.progress_frame = g.frame
            self.event("badge", badge=BADGES[b], count=len(self.badges), party=self.party(),
                       shot=self.shot(f"{BADGES[b]} Badge earned", force=True))
            self.save_state(f"badge{len(self.badges)}")
            print(f"  [{time.time() - self.started:5.0f}s, {g.frame // 3600:4d} min] {BADGES[b]} Badge "
                  f"({len(self.badges)}/8) in {name}; party {self.party()}", file=sys.stderr, flush=True)
        if g.frame - self.progress_frame > STALL_FRAMES:
            raise EmulatorError(f"no new place or badge for an hour of play; last in {name}")
        shown = g.nav_arrow_shown()
        if shown:
            record = self.arrows.setdefault(shown, {"count": 0, "first": None})
            record["count"] += 1
            per_map = self.arrow_by_map.setdefault(name, {})
            per_map[shown] = per_map.get(shown, 0) + 1
            if record["first"] is None:
                record["first"] = self.shot(f"first time the arrow points {shown}", force=True)
                record["first_where"] = name
        else:
            self.no_arrow_presses += 1
        self.field_since_shot += 1
        if self.mode == "full" and self.field_since_shot >= 120:
            self.field_since_shot = 0
            self.shot("walking with the arrow" if shown else "on the field, no arrow showing")
        return False

    def battle(self):
        """Mash A through a battle like a child, taking pictures on the way. Same presses as
        FireRed.follow_arrow's own battle handling."""
        g = self.g
        trainer = bool(g.r32(g.sym("gBattleTypeFlags")) & BATTLE_TYPE_TRAINER)
        number = len(self.battles) + 1
        wild_shots = trainer or number <= 12 or number % 15 == 0
        every = 25 if trainer else 60
        start, menus, presses, first_menu = g.frame, 0, 0, None
        enemy = None
        for presses in range(1, 6000):
            if not g.in_battle():
                break
            if g.at_action_menu():
                menus += 1
                if enemy is None:
                    try:
                        enemy = g.battle_mon(1)["species"]
                    except Exception:
                        enemy = None
                if first_menu is None and (wild_shots or self.mode == "full"):
                    g.frames(10)
                    first_menu = self.shot(("trainer" if trainer else "wild") + " battle: the buttons")
            if self.mode == "full" and wild_shots and presses % every == 0:
                self.shot(("trainer" if trainer else "wild") + " battle")
            if g.callback2() == "CB2_NamingScreen":
                g.press("START", wait=20)
                g.press("A", wait=40)
            else:
                g.press("A", hold=3, wait=13)
        outcome = g.battle_outcome()
        record = {"number": number, "trainer": trainer, "enemy": enemy, "outcome": outcome,
                  "frames": g.frame - start, "menus": menus, "presses": presses, "shot": first_menu}
        self.battles.append(record)
        self.event("battle", **record)
        self.check_party()

    # --- the run -------------------------------------------------------------------------------
    def run(self):
        self.g = g = FireRed()
        result = {"starter": self.starter, "finished": False}
        try:
            if self.from_state:                                     # the second half of a journey
                g.frames(5)
                g.load_state(self.from_state)
                g.frames(10)
                self.badges = {b for b in range(8) if g.flag(FLAG_BADGE01_GET + b)}
                self.shot("resumed from " + os.path.basename(self.from_state), force=True)
            elif self.starter == "arrow":
                self.shot("power on")
                g.start_new_game()
            else:
                self.shot("power on")
                story.new_game_to_starter(g, self.starter)          # walk to the ball and press A
            self.event("start", party=self.party())
            g.follow_arrow(self.watch_field, max_actions=400000, on_battle=self.battle, what="the Hall of Fame")
            self.event("hall of fame", party=self.party())
            for _ in range(300):
                if "HallOfFame" in g.callback2():
                    break
                g.press("A", hold=3, wait=17)
            g.frames(600)
            self.shot("Hall of Fame", force=True)
            for _ in range(120):                                    # through the credits
                g.press("A", hold=3, wait=40)
            self.shot("after the Hall of Fame", force=True)
            self.save_state("hall-of-fame")
            result["finished"] = True
        except EmulatorError as error:
            result["error"] = str(error)
            self.shot("stopped here", force=True)
            self.save_state("stopped")
            self.event("stopped", error=str(error))
        finally:
            result.update({
                "frames": g.frame, "minutes_of_play": round(g.frame / 3600, 1),
                "seconds": round(time.time() - self.started), "badges": len(self.badges),
                "party": self.party(), "maps": len(self.maps), "battles": len(self.battles),
                "trainer_battles": sum(b["trainer"] for b in self.battles),
                "battles_lost": sum(b["outcome"] == 2 for b in self.battles),
                "longest_battle_presses": max((b["presses"] for b in self.battles), default=0),
                "field_actions": self.field_actions, "field_actions_without_arrow": self.no_arrow_presses,
                "arrows": self.arrows, "arrow_directions_never_seen": [d for d in ARROWS if d not in self.arrows],
                "arrow_by_map": self.arrow_by_map, "shots": len(self.shots),
            })
            with open(os.path.join(self.out, "summary.json"), "w") as f:
                json.dump(result, f, indent=1)
            self.log.close()
            self.write_sheets()
            g.close()
        return result

    def write_sheets(self):
        lines = []
        for n in range(0, len(self.shots), PER_SHEET):
            group = self.shots[n:n + PER_SHEET]
            sheet = os.path.join(self.out, f"sheet-{n // PER_SHEET + 1:02d}.png")
            write_sheet([p for p, _ in group], sheet)
            lines.append(os.path.relpath(sheet, ROOT))
            for i, (path, scene) in enumerate(group):
                lines.append(f"  row {i // COLUMNS + 1}, column {i % COLUMNS + 1}: {scene}  ({os.path.basename(path)})")
        with open(os.path.join(self.out, "INDEX.txt"), "w") as f:
            f.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description="QA journey: the whole game with pictures, a log and save states")
    parser.add_argument("--starter", choices=["arrow", "bulbasaur", "charmander", "squirtle"], default="arrow")
    parser.add_argument("--from-state", help="carry on from a save state (pictures for the rest of the game)")
    parser.add_argument("--name", help="folder name (default: the starter)")
    parser.add_argument("--shots", choices=["full", "key"], default="full",
                        help="full: pictures throughout; key: new places, badges, first battle screens, arrows")
    args = parser.parse_args()
    name = args.name or args.starter
    result = Journey(name, args.shots, out=os.path.join(ROOT, "builds", "qa", f"journey-{name}"),
                     states=os.path.join(ROOT, "work", "qa-states", name), from_state=args.from_state).run()
    print(json.dumps({k: v for k, v in result.items() if k not in ("arrows", "arrow_by_map")}, indent=1))
    sys.exit(0 if result["finished"] else 1)


if __name__ == "__main__":
    main()
