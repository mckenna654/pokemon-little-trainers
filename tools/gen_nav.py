#!/usr/bin/env python3
"""Generate the Little Trainers navigation data from the story goals and the game's own maps.

    python3 tools/gen_nav.py            # writes game/src/data/little_trainers_nav.h
    python3 tools/gen_nav.py --check    # only validate tools/nav/objectives.json

For every goal it works out, for each map in the game, which door or map edge to head for. The
world is modelled as a graph of "areas" (connected walkable regions of a map), joined by doors,
stairs and map edges, so a town split in two by a ledge or a locked house is handled correctly.
The game then only has to find a walkable path on the current map (src/little_trainers_nav.c).
"""
import json
import os
import re
import struct
import sys
from collections import deque

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GAME = os.path.join(ROOT, "game")
DATA = os.path.join(GAME, "data")
OUT = os.path.join(GAME, "src", "data", "little_trainers_nav.h")
SPEC = os.path.join(ROOT, "tools", "nav", "objectives.json")

WATER = {0x10, 0x11, 0x12, 0x13, 0x15, 0x1A, 0x1B}   # surfable metatile behaviours
DIRS = {"up": (0, -1, 2), "down": (0, 1, 1), "left": (-1, 0, 3), "right": (1, 0, 4)}   # dx, dy, CONNECTION_*
LEDGES = {0x38: (1, 0), 0x39: (-1, 0), 0x3A: (0, -1), 0x3B: (0, 1)}   # MB_JUMP_EAST/WEST/NORTH/SOUTH
HOP_LEDGE = 0        # an edge inside one map (a ledge jump); not something the arrow aims for itself
MAX_EXITS = 24          # exits listed per map: at least one for each separate area (caves have many)
HOP_WARP = 0x10


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def constants(header, prefix, seed=None):
    """Evaluate #define NAME value lines (simple integers and (BASE + n) forms)."""
    table = dict(seed or {})
    with open(os.path.join(GAME, "include", "constants", header), encoding="utf-8") as f:
        for line in f:
            m = re.match(r"#define\s+(\w+)\s+(.+?)\s*(//.*)?$", line)
            if not m:
                continue
            expr = re.sub(r"\b([A-Za-z_]\w*)\b", lambda n: str(table.get(n.group(1), n.group(1))), m.group(2))
            try:
                table[m.group(1)] = int(eval(expr, {"__builtins__": {}}))
            except Exception:
                pass
    return {k: v for k, v in table.items() if k.startswith(prefix)}


class Map:
    def __init__(self, name, group, num, layouts, attr_cache):
        self.name, self.group, self.num = name, group, num
        self.json = load_json(os.path.join(DATA, "maps", name, "map.json"))
        self.id = self.json["id"]
        layout = layouts[self.json["layout"]]
        self.w, self.h = layout["width"], layout["height"]
        with open(os.path.join(GAME, layout["blockdata_filepath"]), "rb") as f:
            raw = f.read()
        self.blocks = struct.unpack(f"<{self.w * self.h}H", raw[:2 * self.w * self.h])
        self.attrs = (attr_cache("primary", layout["primary_tileset"]), attr_cache("secondary", layout["secondary_tileset"]))
        self.warps = self.json.get("warp_events", [])
        self.objects = self.json.get("object_events", [])
        self.connections = self.json.get("connections") or []
        self.obstacles = {}
        for o in self.objects:
            kind = {"OBJ_EVENT_GFX_CUT_TREE": "tree", "OBJ_EVENT_GFX_PUSHABLE_BOULDER": "boulder",
                    "OBJ_EVENT_GFX_ROCK_SMASH_ROCK": "rock"}.get(o["graphics_id"])
            if kind:
                self.obstacles[(o["x"], o["y"])] = kind
        self.comp = {}      # abilities -> {(x, y): component id}

    def behavior(self, x, y):
        metatile = self.blocks[y * self.w + x] & 0x3FF
        attrs = self.attrs[0][metatile] if metatile < 640 else self.attrs[1][metatile - 640]
        return attrs & 0x1FF

    def walkable(self, x, y, can):
        """can = (surf, cut, strength): what the player is able to do at this point of the story."""
        if not (0 <= x < self.w and 0 <= y < self.h):
            return False
        if (self.blocks[y * self.w + x] >> 10) & 3:
            return False
        if not can[0] and self.behavior(x, y) in WATER:
            return False
        kind = self.obstacles.get((x, y))
        if kind == "tree" and not can[1]:
            return False
        if kind == "boulder" and not can[2]:
            return False
        return kind != "rock"

    def same_level(self, a, b):
        """Ground heights: steps are only possible between equal heights, or via the 'any
        height' tiles (0 and 15) used for stairs and bridges."""
        ea = self.blocks[a[1] * self.w + a[0]] >> 12
        eb = self.blocks[b[1] * self.w + b[0]] >> 12
        wa, wb = self.behavior(*a) in WATER, self.behavior(*b) in WATER
        if wa and wb:
            return True
        if wa or wb:
            return (eb if wa else ea) == 3      # you can only get on and off a surfing Pokemon at ordinary ground level
        return ea == eb or ea in (0, 15) or eb in (0, 15)

    def components(self, water):
        if water not in self.comp:
            comp, n = {}, 0
            for y in range(self.h):
                for x in range(self.w):
                    if (x, y) in comp or not self.walkable(x, y, water):
                        continue
                    queue = deque([(x, y)])
                    comp[(x, y)] = n
                    while queue:
                        cx, cy = queue.popleft()
                        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            nxt = (cx + dx, cy + dy)
                            if nxt not in comp and self.walkable(nxt[0], nxt[1], water) and self.same_level((cx, cy), nxt):
                                comp[nxt] = n
                                queue.append(nxt)
                    n += 1
            self.comp[water] = comp
        return self.comp[water]

    def area_of(self, x, y, water):
        """Component of a tile, or of a walkable neighbour (doors and NPC tiles are often solid)."""
        comp = self.components(water)
        if (x, y) in comp:
            return comp[(x, y)]
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            if (x + dx, y + dy) in comp:
                return comp[(x + dx, y + dy)]
        return None


class World:
    def __init__(self):
        groups = load_json(os.path.join(DATA, "maps", "map_groups.json"))
        layouts = {e["id"]: e for e in load_json(os.path.join(DATA, "layouts", "layouts.json"))["layouts"] if e}
        cache = {}

        folders = {}
        for kind in ("primary", "secondary"):
            for folder in os.listdir(os.path.join(DATA, "tilesets", kind)):
                folders[(kind, folder.replace("_", "").lower())] = folder

        def attrs(kind, symbol):
            if symbol not in cache:
                folder = folders[(kind, symbol.replace("gTileset_", "").replace("_", "").lower())]
                with open(os.path.join(DATA, "tilesets", kind, folder, "metatile_attributes.bin"), "rb") as f:
                    raw = f.read()
                cache[symbol] = struct.unpack(f"<{len(raw) // 4}I", raw)
            return cache[symbol]

        # Map data contains some warp events on plain floor tiles that never trigger. Only tiles
        # whose behaviour is a door, stairs, ladder, mat, pad or hole are real ways out.
        behaviors = constants("metatile_behaviors.h", "MB_")
        self.warp_behaviors = {v for k, v in behaviors.items()
                               if any(word in k for word in ("WARP", "DOOR", "LADDER", "ESCALATOR", "STAIR"))}

        self.maps, self.by_id, self.order, self.group_start = {}, {}, [], []
        for g, group_name in enumerate(groups["group_order"]):
            self.group_start.append(len(self.order))
            for n, name in enumerate(groups[group_name]):
                m = Map(name, g, n, layouts, attrs)
                self.maps[name] = m
                self.by_id[m.id] = m
                self.order.append(m)
        self.index = {m.name: i for i, m in enumerate(self.order)}

    def edges(self, water, avoid):
        """Directed edges {(map, area): [((map2, area2), hop_code)]}."""
        out = {}
        self.lifts = getattr(self, "lifts", {})
        self.edge_tiles = {}     # (a, b, code) -> positions along the map edge where area a meets area b

        def add(a, b, code, along=None):
            if a[1] is None or b[1] is None or a[0] in avoid or b[0] in avoid:
                return
            out.setdefault(a, [])
            if (b, code) not in out[a]:
                out[a].append((b, code))
            if along is not None:
                self.edge_tiles.setdefault((a, b, code), set()).add(along)

        for m in self.order:
            for i, warp in enumerate(m.warps):
                dest = self.by_id.get(warp["dest_map"])
                here = (m.name, m.area_of(warp["x"], warp["y"], water))
                if dest is None:
                    continue                      # MAP_DYNAMIC (lifts): handled below from the other side
                if not (0 <= warp["x"] < m.w and 0 <= warp["y"] < m.h) or m.behavior(warp["x"], warp["y"]) not in self.warp_behaviors:
                    continue                      # a warp event that can never fire
                dwarps = dest.warps
                wid = int(warp["dest_warp_id"])
                if wid >= len(dwarps):
                    continue
                there = (dest.name, dest.area_of(dwarps[wid]["x"], dwarps[wid]["y"], water))
                add(here, there, HOP_WARP + i)
                # A lift cabin's own doors have no fixed destination; it can return to any floor
                # that has a door into it.
                for j, back in enumerate(dwarps):
                    if back["dest_map"] == "MAP_DYNAMIC" and dest.behavior(back["x"], back["y"]) in self.warp_behaviors:
                        add((dest.name, dest.area_of(back["x"], back["y"], water)), here, HOP_WARP + j)
                        # leaving the cabin onto this floor puts the player at the floor's own lift door
                        self.lifts[(dest.name, HOP_WARP + j, here)] = (m, i)
            # Ledges are one-way: standing above one you can hop down to the tile beyond it.
            for y in range(m.h):
                for x in range(m.w):
                    jump = LEDGES.get(m.behavior(x, y))
                    if jump and m.walkable(x - jump[0], y - jump[1], water) and m.walkable(x + jump[0], y + jump[1], water):
                        a = m.area_of(x - jump[0], y - jump[1], water)
                        b = m.area_of(x + jump[0], y + jump[1], water)
                        if a != b:
                            add((m.name, a), (m.name, b), HOP_LEDGE)
            for con in m.connections:
                other = self.by_id.get(con["map"])
                if other is None or con["direction"] not in DIRS:
                    continue
                dx, dy, code = DIRS[con["direction"]]
                off = con["offset"]
                if dy:
                    y_here = 0 if dy < 0 else m.h - 1
                    y_there = other.h - 1 if dy < 0 else 0
                    for x in range(m.w):
                        if m.walkable(x, y_here, water) and other.walkable(x - off, y_there, water):
                            add((m.name, m.area_of(x, y_here, water)), (other.name, other.area_of(x - off, y_there, water)), code, x)
                else:
                    x_here = 0 if dx < 0 else m.w - 1
                    x_there = other.w - 1 if dx < 0 else 0
                    for y in range(m.h):
                        if m.walkable(x_here, y, water) and other.walkable(x_there, y - off, water):
                            add((m.name, m.area_of(x_here, y, water)), (other.name, other.area_of(x_there, y - off, water)), code, y)
        return out


def resolve_target(world, obj):
    """Returns ((x, y) or None, local id of the person/object to find at run time or 0)."""
    m = world.maps[obj["map"]]
    target = obj["target"]
    if "xy" in target:
        return tuple(target["xy"]), 0
    if "object" in target or "object_flag" in target:
        for index, o in enumerate(m.objects):
            if "object_flag" in target:
                found = o["flag"] == target["object_flag"]
            else:
                found = target["object"].lower() in o["script"].lower()
            if found:
                # People are moved about by scripts, so the game looks them up by number.
                return (o["x"], o["y"]), index + 1
        raise SystemExit(f'{obj["id"]}: no object matching {target} on {m.name}: '
                         f'{[(o["script"], o["flag"]) for o in m.objects]}')
    if "bg" in target:
        for b in m.json.get("bg_events", []):
            if target["bg"].lower() in str(b.get("script", "")).lower():
                return (b["x"], b["y"]), 0
        raise SystemExit(f'{obj["id"]}: no sign or switch matching {target["bg"]!r} on {m.name}')
    if "warp_to" in target:
        for w in m.warps:
            if w["dest_map"] == target["warp_to"]:
                return (w["x"], w["y"]), 0
        raise SystemExit(f'{obj["id"]}: no warp to {target["warp_to"]} on {m.name}')
    return None, 0     # anywhere


def main():
    spec = load_json(SPEC)
    world = World()
    flags = constants("flags.h", "FLAG_", seed=constants("opponents.h", ""))
    variables = constants("vars.h", "VAR_")
    items = constants("items.h", "ITEM_")
    blocks = spec["blocks"]
    graphs, routes, rows, problems, notes, lift_rows = {}, {}, [], [], [], []
    previous = ("PalletTown_PlayersHouse_2F", world.maps["PalletTown_PlayersHouse_2F"].area_of(6, 6, (False, False, False)))

    for obj in spec["objectives"]:
        water = (obj.get("surf", False), obj.get("cut", False), obj.get("strength", False))
        avoid = set()
        for entry in obj.get("avoid", spec["defaults"]["avoid"]):
            avoid.update(blocks.get(entry, [entry]))
        unknown = [name for name in avoid | {obj["map"]} if name not in world.maps]
        if unknown:
            raise SystemExit(f'{obj["id"]}: unknown map(s) {unknown}')
        done = obj["done"]
        if "flag" in done:
            cond = (0, flags[done["flag"]], 0, done["flag"])
        elif "item" in done:
            cond = (2, items[done["item"]], 0, f'has {done["item"]}')
        else:
            cond = (1, variables[done["var"]], done["ge"], f'{done["var"]} >= {done["ge"]}')

        m = world.maps[obj["map"]]
        xy, local_id = resolve_target(world, obj)
        gkey = (water, tuple(sorted(avoid)))
        if gkey not in graphs:
            edges = world.edges(water, avoid)
            reverse = {}
            for a, outs in edges.items():
                for b, code in outs:
                    reverse.setdefault(b, []).append(a)
            graphs[gkey] = (edges, reverse)
        edges, reverse = graphs[gkey]

        def distances(goals):
            dist = {g: 0 for g in goals}
            queue = deque(goals)
            while queue:
                cur = queue.popleft()
                for prev in reverse.get(cur, []):
                    if prev not in dist:
                        dist[prev] = dist[cur] + 1
                        queue.append(prev)
            return dist

        every_area = [(m.name, a) for a in sorted(set(m.components(water).values()))]
        area = None if xy is None else m.area_of(xy[0], xy[1], water)
        if area is not None and previous not in distances([(m.name, area)]):
            # The exact spot is behind something the map data cannot see (a gym's gates, a quiz
            # door). Lead the player into the building; the marker still shows the spot.
            notes.append(f'{obj["id"]}: the arrow leads into {m.name}, but not past its barriers')
            area = None
        key = (obj["map"], water, tuple(sorted(avoid)), area)
        if key not in routes:
            goals = [(m.name, area)] if area is not None else every_area
            dist = distances(goals)
            def hop_from(node, depth=0):
                """The exit to aim for from an area: (code, area the exit is in, area it leads to).
                Ledge jumps inside the map are followed to the next real exit."""
                outs = edges.get(node, [])
                if not outs or depth > 8:
                    return None
                nxt = min(outs, key=lambda e: dist.get(e[0], 10 ** 9))
                if dist.get(nxt[0], 10 ** 9) >= dist[node]:
                    return None
                return hop_from(nxt[0], depth + 1) if nxt[1] == HOP_LEDGE else (nxt[1], node, nxt[0])

            table = []
            for mm in world.order:
                exits = {}       # (code, lo, hi) -> distance
                for node in edges:
                    if node[0] != mm.name or node not in dist or dist[node] == 0:
                        continue
                    hop = hop_from(node)
                    if not hop:
                        continue
                    code, start, leads_to = hop
                    if code >= HOP_WARP:
                        spans = [(0, 0)]
                        if (mm.name, code, leads_to) in world.lifts and not any(r[0] == len(routes) and r[1] == world.index[mm.name] for r in lift_rows):
                            floor, door = world.lifts[(mm.name, code, leads_to)]
                            lift_rows.append((len(routes), world.index[mm.name], floor, door))
                    else:
                        # the stretch(es) of the map edge where this area meets the next one
                        tiles = sorted(world.edge_tiles[(start, leads_to, code)])
                        spans, lo = [], tiles[0]
                        for prev, cur in zip(tiles, tiles[1:] + [None]):
                            if cur != prev + 1:
                                spans.append((lo, prev))
                                lo = cur
                    for lo, hi in spans:
                        exits[(code, lo, hi)] = min(exits.get((code, lo, hi), 10 ** 9), dist[node])
                table.append([e for e, _ in sorted(exits.items(), key=lambda kv: kv[1])][:MAX_EXITS])
            routes[key] = (len(routes), table, dist)
        route_id, _, dist = routes[key]
        if previous not in dist:
            problems.append(f'{obj["id"]}: cannot be reached from the previous goal ({previous[0]})')
        if previous not in dist and "--why" in sys.argv:
            reach, seen = deque([previous]), {previous}
            while reach:
                cur = reach.popleft()
                for nxt, _ in edges.get(cur, []):
                    if nxt not in seen:
                        seen.add(nxt)
                        reach.append(nxt)
            print(f'  {obj["id"]}: from {previous} the player can reach {len({n for n, _ in seen})} maps, '
                  f'but none of the areas of {m.name}')
        # Where the player stands when this goal is done: the reachable area closest to the target.
        inside = [g for g in ([(m.name, area)] if area is not None else every_area)]
        previous = next((g for g in inside if previous in distances([g])), inside[0])
        rows.append((obj["id"], cond, m, xy, route_id, local_id, int(bool(obj.get("surf", False)))))

    for n in notes:
        print("note:", n)
    for p in problems:
        print("warning:", p)
    print(f"{len(rows)} goals, {len(routes)} route tables, {len(world.order)} maps")
    if "--check" in sys.argv:
        return 1 if problems else 0

    # Exit lists are pooled: most maps have one exit or none, and many routes share lists.
    pool, pool_index = [0], {(): 0}                      # offset 0 = "no exits"
    route_offsets = {}
    for key, (route_id, table, _) in routes.items():
        offsets = []
        for exits in table:
            t = tuple(exits)
            if t not in pool_index:
                pool_index[t] = len(pool)
                pool.append(len(t))
                for code, lo, hi in t:
                    pool += [code, lo, hi]
            offsets.append(pool_index[t])
        route_offsets[route_id] = (key, offsets)
    print(f"{len(pool)} bytes of exit lists")

    lines = ["// Generated by tools/gen_nav.py from tools/nav/objectives.json and the map data.",
             "// Do not edit by hand: change the goals file and run the generator again.", "",
             f"#define LT_NAV_NUM_MAPS {len(world.order)}",
             f"#define LT_NAV_HOP_WARP {HOP_WARP:#x}", "",
             "static const u16 sLtNavGroupStart[] = {" + ", ".join(str(v) for v in world.group_start) + "};", "",
             "// Exit lists: a count, then {exit, from, to} triples. An exit is a map edge (CONNECTION_*,",
             "// with the stretch of tiles along that edge) or LT_NAV_HOP_WARP + a warp number.",
             "static const u8 sLtNavExits[] = {"]
    for i in range(0, len(pool), 24):
        lines.append("    " + ", ".join(str(v) for v in pool[i:i + 24]) + ",")
    lines += ["};", ""]
    for route_id, (key, offsets) in sorted(route_offsets.items()):
        lines.append(f"// route {route_id}: to {key[0]}: where each map's exit list starts in sLtNavExits")
        lines.append(f"static const u16 sLtNavRoute{route_id}[LT_NAV_NUM_MAPS] = {{")
        for i in range(0, len(offsets), 20):
            lines.append("    " + ", ".join(str(v) for v in offsets[i:i + 20]) + ",")
        lines.append("};")
        lines.append("")
    lines.append("static const u16 *const sLtNavRoutes[] = {" + ", ".join(f"sLtNavRoute{i}" for i in range(len(routes))) + "};")
    lines.append("")
    lines.append("// Lift cabins: for a route, the floor the lift should open onto.")
    lines.append("static const struct LtNavLift sLtNavLifts[] = {")
    for route_id, map_index, floor, door in lift_rows:
        lines.append(f"    {{{route_id}, {map_index}, {floor.group}, {floor.num}, {door}}}, // {world.order[map_index].name} -> {floor.name}")
    lines.append("};")
    lines.append("")
    lines.append("static const struct LtNavGoal sLtNavGoals[] = {")
    for name, cond, m, xy, route_id, local_id, surf in rows:
        x, y = (0xFF, 0xFF) if xy is None else xy
        lines.append(f"    {{{cond[0]}, {cond[1]:#06x}, {cond[2]}, {m.group}, {m.num}, {x}, {y}, {route_id}, {local_id}, {surf}}}, // {name}: until {cond[3]}")
    lines.append("};")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("wrote", os.path.relpath(OUT, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
