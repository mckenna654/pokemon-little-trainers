"""Read the game's own map data (game/data) so scripted walking can path-find instead of guessing.

Collision comes from each layout's map.bin (bits 10-11 of every block); NPC positions and warps
come from map.json. This mirrors what the engine uses, so if a tileset or map edit breaks
collision, path-finding tests fail.
"""
import json
import os
import struct
from collections import deque
from functools import lru_cache

from .gba import ROOT

DATA = os.path.join(ROOT, "game", "data")
DIRS = {"UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0)}


@lru_cache(maxsize=None)
def _groups():
    with open(os.path.join(DATA, "maps", "map_groups.json"), encoding="utf-8") as f:
        d = json.load(f)
    return [d[name] for name in d["group_order"]]


@lru_cache(maxsize=None)
def _layouts():
    with open(os.path.join(DATA, "layouts", "layouts.json"), encoding="utf-8") as f:
        return {entry["id"]: entry for entry in json.load(f)["layouts"] if entry}


def map_name(location):
    group, num = location
    return _groups()[group][num]


def location_of(name):
    for g, maps in enumerate(_groups()):
        if name in maps:
            return (g, maps.index(name))
    raise KeyError(name)


class MapInfo:
    def __init__(self, location):
        self.name = map_name(location)
        with open(os.path.join(DATA, "maps", self.name, "map.json"), encoding="utf-8") as f:
            self.json = json.load(f)
        layout = _layouts()[self.json["layout"]]
        self.width, self.height = layout["width"], layout["height"]
        with open(os.path.join(ROOT, "game", layout["blockdata_filepath"]), "rb") as f:
            raw = f.read()
        self.blocks = struct.unpack(f"<{self.width * self.height}H", raw[:2 * self.width * self.height])
        self.warps = [(w["x"], w["y"], w["dest_map"]) for w in self.json.get("warp_events", [])]
        self.objects = [(o["x"], o["y"]) for o in self.json.get("object_events", [])]

    def passable(self, x, y):
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        return (self.blocks[y * self.width + x] >> 10) & 3 == 0

    def path(self, start, goal, avoid=(), static_objects=True):
        """Breadth-first route of directions from start to goal, or None. NPC start tiles and
        `avoid` tiles are treated as walls; the goal itself may be an impassable warp tile."""
        blocked = set(avoid) | (set(self.objects) if static_objects else set())
        prev = {start: None}
        queue = deque([start])
        while queue:
            cur = queue.popleft()
            if cur == goal:
                steps = []
                while prev[cur] is not None:
                    cur, d = prev[cur]
                    steps.append(d)
                return steps[::-1]
            for d, (dx, dy) in DIRS.items():
                nxt = (cur[0] + dx, cur[1] + dy)
                if nxt in prev or (nxt in blocked and nxt != goal):
                    continue
                if self.passable(*nxt) or nxt == goal:
                    prev[nxt] = (cur, d)
                    queue.append(nxt)
        return None

    def render(self, mark=()):
        rows = []
        for y in range(self.height):
            row = ""
            for x in range(self.width):
                if (x, y) in mark:
                    row += "@"
                elif any((x, y) == (wx, wy) for wx, wy, _ in self.warps):
                    row += "W"
                elif (x, y) in self.objects:
                    row += "o"
                else:
                    row += "." if self.passable(x, y) else "#"
            rows.append(row)
        return "\n".join(rows)
